"""Optional Langfuse observability helpers for BENNO AI flows."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from flask import current_app, has_app_context

from benno.models import Chat, ReportDraft
from benno.services.ai_provider import AiMessageAnalysis
from benno.services.report_state import draft_data

SECRET_KEY_PARTS = ("api_key", "apikey", "password", "secret", "token")
MAX_CAPTURED_STRING_LENGTH = 4_000
REPORT_LOOP_TRACE_NAME = "process-report-turn"


class ObservationHandle:
    """Small wrapper that hides Langfuse SDK details from BENNO services."""

    def __init__(self, observation: Any | None = None) -> None:
        self._observation = observation

    def update(self, **kwargs: Any) -> None:
        """Update an active observation when tracing is enabled."""
        if self._observation is None:
            return

        self._observation.update(**kwargs)


@contextmanager
def trace_report_turn(
    chat: Chat,
    draft: ReportDraft,
    current_step: str | None,
    message_text: str,
):
    """Create one trace for a report chat turn when Langfuse is enabled."""
    langfuse = _langfuse_client()
    if langfuse is None:
        yield ObservationHandle()
        return

    from langfuse import propagate_attributes

    with propagate_attributes(
        user_id=str(chat.sales_user_id),
        session_id=f"benno-chat-{chat.id}",
        tags=["benno", "report-loop", "phase-7"],
        metadata={
            "feature": "sales-report-loop",
            "chat_id": chat.id,
            "report_status": draft.report_status,
        },
        environment=_langfuse_environment(),
        trace_name=REPORT_LOOP_TRACE_NAME,
    ):
        with langfuse.start_as_current_observation(
            as_type="span",
            name=REPORT_LOOP_TRACE_NAME,
            input=_report_turn_input(draft, current_step, message_text),
            metadata={
                "current_step": current_step,
                "chat_id": chat.id,
                "sales_user_id": chat.sales_user_id,
            },
        ) as span:
            handle = ObservationHandle(span)
            try:
                yield handle
            except Exception as error:
                handle.update(
                    output={
                        "status": "error",
                        "error_type": type(error).__name__,
                    }
                )
                raise
            finally:
                _flush_if_configured()


@contextmanager
def trace_generation(
    name: str,
    model: str,
    input_payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
):
    """Create a generation observation under the active trace."""
    langfuse = _langfuse_client()
    if langfuse is None:
        yield ObservationHandle()
        return

    with langfuse.start_as_current_observation(
        as_type="generation",
        name=name,
        model=model,
        input=_safe_capture(input_payload),
        metadata=_safe_capture(metadata or {}),
    ) as generation:
        yield ObservationHandle(generation)


def trace_report_decision(
    draft: ReportDraft,
    analysis: AiMessageAnalysis | None,
    applied_step_keys: list[str],
    next_step_key: str | None,
) -> None:
    """Attach backend validation and flow decisions to the active trace."""
    langfuse = _langfuse_client()
    if langfuse is None:
        return

    langfuse.update_current_span(
        output=_safe_capture(
            {
                "status": draft.report_status,
                "next_step": next_step_key or "review",
                "missing_sections": draft.missing_sections_json,
                "applied_step_keys": applied_step_keys,
                "accepted_ai_update_keys": _ai_update_keys(analysis),
            }
        ),
        metadata=_safe_capture(
            {
                "completed_steps": draft_data(draft).get("completed_steps", []),
                "rating_keys": list(draft.ratings_json.keys()),
                "last_ai_error": draft_data(draft).get("last_ai_error"),
            }
        ),
    )


def traced_generation_input(
    prompt: str,
    system_instruction: str,
) -> dict[str, Any]:
    """Return a readable role-labeled generation input."""
    return {
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ]
    }


def traced_generation_output(value: Any) -> Any:
    """Return provider output using the configured privacy level."""
    return _safe_capture(value)


def traced_usage_details(response: Any) -> dict[str, int]:
    """Extract Gemini usage details in Langfuse's preferred token buckets."""
    usage_metadata = getattr(response, "usage_metadata", None)
    if usage_metadata is None:
        return {}

    usage_details = {
        "input": getattr(usage_metadata, "prompt_token_count", None),
        "output": getattr(usage_metadata, "candidates_token_count", None),
        "total": getattr(usage_metadata, "total_token_count", None),
        "cached_input": getattr(usage_metadata, "cached_content_token_count", None),
    }
    return {
        key: value
        for key, value in usage_details.items()
        if isinstance(value, int) and value >= 0
    }


def observability_status() -> dict[str, str]:
    """Return a display-safe Langfuse status summary."""
    if not _langfuse_enabled():
        return {"label": "Langfuse: disabled", "state": "inactive"}
    if not _langfuse_configured():
        return {"label": "Langfuse: missing credentials", "state": "inactive"}
    if _langfuse_client() is None:
        return {"label": "Langfuse: SDK unavailable", "state": "inactive"}

    return {"label": "Langfuse: active", "state": "active"}


def flush_observability() -> None:
    """Flush pending Langfuse observations when available."""
    langfuse = _langfuse_client()
    if langfuse is None:
        return

    langfuse.flush()


def _report_turn_input(
    draft: ReportDraft,
    current_step: str | None,
    message_text: str,
) -> dict[str, Any]:
    payload = {
        "messages": [{"role": "user", "content": message_text}],
        "current_step": current_step,
    }
    if _capture_full_context():
        payload["draft_context"] = {
            "known_answers": draft_data(draft).get("answers", {}),
            "missing_sections": draft.missing_sections_json,
            "ratings": draft.ratings_json,
        }
    else:
        payload["draft_context"] = {
            "known_answer_keys": list(draft_data(draft).get("answers", {}).keys()),
            "missing_sections": draft.missing_sections_json,
            "rating_keys": list(draft.ratings_json.keys()),
        }

    return _safe_capture(payload)


def _safe_capture(value: Any) -> Any:
    if _capture_full_context():
        return _mask_sensitive_values(value)

    return _summarize_and_mask(value)


def _summarize_and_mask(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _summarize_and_mask(child_value)
            for key, child_value in value.items()
            if not _is_secret_key(str(key))
        }
    if isinstance(value, list):
        return [_summarize_and_mask(child_value) for child_value in value]
    if isinstance(value, str):
        return _truncate_text(value)

    return value


def _mask_sensitive_values(value: Any) -> Any:
    if isinstance(value, dict):
        masked_value = {}
        for key, child_value in value.items():
            if _is_secret_key(str(key)):
                masked_value[key] = "[REDACTED]"
            else:
                masked_value[key] = _mask_sensitive_values(child_value)
        return masked_value
    if isinstance(value, list):
        return [_mask_sensitive_values(child_value) for child_value in value]
    if isinstance(value, str):
        return _truncate_text(value)

    return value


def _truncate_text(value: str) -> str:
    if len(value) <= MAX_CAPTURED_STRING_LENGTH:
        return value

    return f"{value[:MAX_CAPTURED_STRING_LENGTH]}...[truncated]"


def _is_secret_key(key: str) -> bool:
    normalized_key = key.lower()
    return any(secret_part in normalized_key for secret_part in SECRET_KEY_PARTS)


def _ai_update_keys(analysis: AiMessageAnalysis | None) -> list[str]:
    if analysis is None:
        return []

    return list(analysis.section_updates.keys())


def _langfuse_client() -> Any | None:
    if not _langfuse_enabled() or not _langfuse_configured():
        return None

    try:
        from langfuse import get_client
    except ImportError:
        return None

    return get_client()


def _langfuse_enabled() -> bool:
    if not has_app_context():
        return False

    return bool(current_app.config.get("LANGFUSE_ENABLED"))


def _langfuse_configured() -> bool:
    if not has_app_context():
        return False

    return all(
        current_app.config.get(key)
        for key in (
            "LANGFUSE_PUBLIC_KEY",
            "LANGFUSE_SECRET_KEY",
            "LANGFUSE_HOST",
        )
    )


def _capture_full_context() -> bool:
    if not has_app_context():
        return False

    return bool(current_app.config.get("LANGFUSE_CAPTURE_FULL_CONTEXT"))


def _flush_if_configured() -> None:
    if not has_app_context():
        return
    if not current_app.config.get("LANGFUSE_FLUSH_ON_TURN"):
        return

    flush_observability()


def _langfuse_environment() -> str:
    if not has_app_context():
        return "development"

    return "testing" if current_app.config.get("TESTING") else "development"
