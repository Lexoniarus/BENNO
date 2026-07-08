"""AI provider selection and display-safe status for BENNO."""

from __future__ import annotations

import importlib.util

from flask import current_app, has_app_context

from benno.enums import AiProvider
from benno.services.ai_provider import AiProviderError, AiService, NullAiService


def get_ai_service() -> AiService:
    """Build the configured AI service for the current Flask app."""
    if not has_app_context():
        return NullAiService()

    current_app.config.pop("AI_PROVIDER_LAST_ERROR", None)
    provider_code = get_active_ai_provider()
    if provider_code != AiProvider.GEMINI.value:
        return NullAiService()

    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        return NullAiService()

    from benno.services.gemini_provider import GeminiService

    try:
        return GeminiService(api_key=api_key, model=get_active_ai_model())
    except AiProviderError as error:
        current_app.config["AI_PROVIDER_LAST_ERROR"] = _provider_error_label(error)
        return NullAiService()


def get_ai_status() -> dict[str, str]:
    """Return a display-safe summary of the configured AI provider."""
    if not has_app_context():
        return {"label": "KI: Fallback ohne externen Provider", "state": "inactive"}

    provider_code = get_active_ai_provider()
    if provider_code != AiProvider.GEMINI.value:
        return {"label": f"KI: {provider_code} nicht aktiv", "state": "inactive"}

    model = get_active_ai_model()
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


def get_active_ai_provider() -> str:
    """Return the active provider code from Flask configuration."""
    if not has_app_context():
        return AiProvider.GEMINI.value

    return current_app.config.get("AI_PROVIDER", AiProvider.GEMINI.value)


def get_active_ai_model() -> str:
    """Return the active model name from Flask configuration."""
    if not has_app_context():
        return "gemini-3.1-flash-lite"

    return current_app.config.get("GEMINI_MODEL", "gemini-3.1-flash-lite")


def _gemini_sdk_is_available() -> bool:
    return importlib.util.find_spec("google.genai") is not None


def _provider_error_label(error: AiProviderError) -> str:
    error_text = str(error).lower()
    if "not installed" in error_text or "sdk" in error_text:
        return "SDK fehlt"
    if "initialization" in error_text:
        return "Initialisierung fehlgeschlagen"

    return "Provider-Fehler"
