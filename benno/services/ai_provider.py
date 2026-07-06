"""AI provider interface and shared response models."""

from __future__ import annotations

import importlib.util
from typing import Any, Protocol

from flask import current_app, has_app_context
from pydantic import BaseModel, ConfigDict, Field

from benno.enums import AiProvider, UserIntent


class AiProviderError(RuntimeError):
    """Raised when an AI provider cannot return a usable response."""


class AiMessageAnalysis(BaseModel):
    """Structured AI proposal for one user message."""

    model_config = ConfigDict(extra="ignore")

    intent: UserIntent = UserIntent.UNKNOWN
    intent_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    target_sections: list[str] = Field(default_factory=list)
    section_updates: dict[str, str] = Field(default_factory=dict)
    suggested_next_section: str | None = None
    suggested_next_question: str | None = None


class AiService(Protocol):
    """Provider-independent AI service contract."""

    def analyze_report_message(
        self,
        context: dict[str, Any],
        message_text: str,
    ) -> AiMessageAnalysis | None:
        """Return a structured proposal for one report message."""

    def draft_review_text(self, draft_context: dict[str, Any]) -> str | None:
        """Return optional wording for the human review."""

    def draft_final_report_text(self, draft_context: dict[str, Any]) -> str | None:
        """Return optional wording for the final report."""


class NullAiService:
    """No-op provider used when AI is unavailable or disabled."""

    def analyze_report_message(
        self,
        context: dict[str, Any],
        message_text: str,
    ) -> AiMessageAnalysis | None:
        """Return no analysis."""
        return None

    def draft_review_text(self, draft_context: dict[str, Any]) -> str | None:
        """Return no review wording."""
        return None

    def draft_final_report_text(self, draft_context: dict[str, Any]) -> str | None:
        """Return no final report wording."""
        return None


def get_ai_service() -> AiService:
    """Build the configured AI service for the current Flask app."""
    if not has_app_context():
        return NullAiService()

    current_app.config.pop("AI_PROVIDER_LAST_ERROR", None)
    provider_code = current_app.config.get("AI_PROVIDER", AiProvider.GEMINI.value)
    if provider_code != AiProvider.GEMINI.value:
        return NullAiService()

    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        return NullAiService()

    model = current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
    from benno.services.gemini_provider import GeminiService

    try:
        return GeminiService(api_key=api_key, model=model)
    except AiProviderError as error:
        current_app.config["AI_PROVIDER_LAST_ERROR"] = _provider_error_label(error)
        return NullAiService()


def get_ai_status() -> dict[str, str]:
    """Return a display-safe summary of the configured AI provider."""
    if not has_app_context():
        return {"label": "KI: Fallback ohne externen Provider", "state": "inactive"}

    provider_code = current_app.config.get("AI_PROVIDER", AiProvider.GEMINI.value)
    if provider_code != AiProvider.GEMINI.value:
        return {"label": f"KI: {provider_code} nicht aktiv", "state": "inactive"}

    model = current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
    if not current_app.config.get("GEMINI_API_KEY"):
        return {"label": f"KI: Gemini / {model} ohne API-Key", "state": "inactive"}

    if not _gemini_sdk_is_available():
        return {"label": f"KI: Gemini / {model} SDK fehlt", "state": "inactive"}

    last_error = current_app.config.get("AI_PROVIDER_LAST_ERROR")
    if last_error:
        return {
            "label": f"KI: Gemini / {model} nicht verfügbar ({last_error})",
            "state": "inactive",
        }

    return {"label": f"KI: Gemini / {model}", "state": "active"}


def _gemini_sdk_is_available() -> bool:
    return importlib.util.find_spec("google.genai") is not None


def _provider_error_label(error: AiProviderError) -> str:
    error_text = str(error).lower()
    if "not installed" in error_text or "sdk" in error_text:
        return "SDK fehlt"
    if "initialization" in error_text:
        return "Initialisierung fehlgeschlagen"

    return "Provider-Fehler"
