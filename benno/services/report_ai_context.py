"""AI context and AI response sanitation for report messages."""

from typing import Any

from benno.enums import UserIntent
from benno.models import ReportDraft
from benno.services.ai_provider import AiMessageAnalysis, AiProviderError
from benno.services.report_shortcuts import extract_explicit_visit_reason
from benno.services.report_state import draft_data
from benno.services.report_steps import (
    allowed_update_keys,
    missing_rating_keys,
    missing_sections_for_draft,
    missing_step_keys,
    report_requirements,
    step_question,
)


def ai_message_context(draft: ReportDraft, current_step: Any) -> dict[str, Any]:
    """Build the context for one AI extraction call."""
    return {
        "current_step": current_step.key,
        "current_question": step_question(current_step, draft.session_language),
        "report_requirements": report_requirements(draft),
        "missing_sections": list(draft.missing_sections_json),
        "missing_step_keys": missing_step_keys(draft),
        "missing_rating_keys": missing_rating_keys(draft),
        "known_answers": dict(draft_data(draft).get("answers", {})),
        "ratings": dict(draft.ratings_json),
        "customer_context_type": draft.customer_context_type,
        "flow_hints": {
            "lead_can_skip_offer_and_order": True,
            "inside_sales_follow_up_can_update_next_action": True,
            "ratings_can_be_answered_together": True,
        },
        "allowed_section_update_keys": allowed_update_keys(),
    }


def next_question_context(draft: ReportDraft, next_step: Any) -> dict[str, Any]:
    """Build optional context for future AI question wording."""
    return {
        "next_step": next_step.key,
        "fallback_question": step_question(next_step, draft.session_language),
        "report_requirements": report_requirements(draft),
        "missing_sections": list(missing_sections_for_draft(draft)),
        "missing_step_keys": missing_step_keys(draft),
        "missing_rating_keys": missing_rating_keys(draft),
        "known_answers": dict(draft_data(draft).get("answers", {})),
        "ratings": dict(draft.ratings_json),
        "customer_context_type": draft.customer_context_type,
        "report_status": draft.report_status,
    }


def sanitize_ai_analysis(
    analysis: AiMessageAnalysis,
    message_text: str,
) -> AiMessageAnalysis:
    """Normalize one provider analysis into BENNO's allowed report keys."""
    allowed_keys = set(allowed_update_keys())
    section_updates = {
        key: value.strip()
        for key, value in analysis.section_updates.items()
        if key in allowed_keys and isinstance(value, str) and value.strip()
    }
    target_sections = [
        section for section in analysis.target_sections if section in allowed_keys
    ]
    add_explicit_visit_reason_clue(
        section_updates,
        target_sections,
        analysis,
        message_text,
    )

    return AiMessageAnalysis(
        intent=analysis.intent,
        intent_confidence=analysis.intent_confidence,
        target_sections=target_sections,
        section_updates=section_updates,
        suggested_next_section=clean_section_key(analysis.suggested_next_section),
        suggested_next_question=clean_ai_text(analysis.suggested_next_question, 500),
    )


def add_explicit_visit_reason_clue(
    section_updates: dict[str, str],
    target_sections: list[str],
    analysis: AiMessageAnalysis,
    message_text: str,
) -> None:
    """Add an explicit topic clue when AI missed a clear German pattern."""
    if analysis.intent == UserIntent.CORRECTION:
        return
    if section_updates.get("target_topic"):
        return

    visit_reason = extract_explicit_visit_reason(message_text)
    if visit_reason is None:
        return

    section_updates["target_topic"] = visit_reason
    if "target_topic" not in target_sections:
        target_sections.append("target_topic")


def store_ai_analysis(
    draft: ReportDraft,
    analysis: AiMessageAnalysis,
) -> None:
    """Store the last sanitized AI analysis for diagnostics."""
    draft.draft_data_json = {
        **draft_data(draft),
        "last_ai_analysis": analysis.model_dump(mode="json"),
    }


def store_ai_error(draft: ReportDraft, error_code: str) -> None:
    """Store the last AI error as a controlled diagnostic marker."""
    draft.draft_data_json = {
        **draft_data(draft),
        "last_ai_error": error_code,
    }


def ai_error_code(error: AiProviderError) -> str:
    """Map provider exceptions to display-safe diagnostic codes."""
    error_text = error_chain_text(error)
    if "additionalproperties" in error_text or "schema" in error_text:
        return "message_analysis_schema_failed"
    if "rate" in error_text or "quota" in error_text:
        return "message_analysis_rate_limited"
    if "api key" in error_text or "authentication" in error_text:
        return "message_analysis_auth_failed"

    return "message_analysis_failed"


def error_chain_text(error: BaseException) -> str:
    """Return a lower-case string containing an exception cause chain."""
    messages = []
    current_error: BaseException | None = error
    while current_error is not None:
        messages.append(str(current_error).lower())
        current_error = current_error.__cause__

    return " ".join(messages)


def clean_ai_text(value: str | None, max_length: int) -> str | None:
    """Clean AI text and cap it at a safe length."""
    if value is None:
        return None

    cleaned_value = value.strip()
    if not cleaned_value:
        return None

    return cleaned_value[:max_length]


def clean_section_key(value: str | None) -> str | None:
    """Return an allowed section key or None."""
    if value is None:
        return None

    cleaned_value = value.strip()
    if cleaned_value not in allowed_update_keys():
        return None

    return cleaned_value
