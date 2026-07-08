"""AI provider interface and shared response models."""

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from benno.enums import UserIntent


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

    def draft_next_question(self, question_context: dict[str, Any]) -> str | None:
        """Return optional wording for the next assistant question."""

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

    def draft_next_question(self, question_context: dict[str, Any]) -> str | None:
        """Return no assistant question wording."""
        return None

    def draft_review_text(self, draft_context: dict[str, Any]) -> str | None:
        """Return no review wording."""
        return None

    def draft_final_report_text(self, draft_context: dict[str, Any]) -> str | None:
        """Return no final report wording."""
        return None


def get_ai_service() -> AiService:
    """Build the configured AI service for the current Flask app."""
    from benno.services.ai_registry import get_ai_service as get_configured_ai_service

    return get_configured_ai_service()


def get_ai_status() -> dict[str, str]:
    """Return a display-safe summary of the configured AI provider."""
    from benno.services.ai_registry import get_ai_status as get_configured_ai_status

    return get_configured_ai_status()
