"""Shared draft-state helpers for the BENNO report workflow."""

from dataclasses import asdict
from typing import Any

from benno.models import ReportDraft

AI_CACHE_KEY = "ai_cache"
CRM_REFERENCES_KEY = "crm_references"
INSIDE_SALES_FOLLOW_UP_KEY = "inside_sales_follow_up_requested"
DISPLAY_VALUE_LABELS = {
    "in_person": "Vor Ort",
    "virtual": "Virtuell",
    "phone": "Telefonisch",
    "not_applicable": "Nicht relevant",
}


def draft_data(draft: ReportDraft) -> dict[str, Any]:
    """Return mutable-safe draft JSON data."""
    return dict(draft.draft_data_json or {})


def draft_answer(draft: ReportDraft, key: str) -> str:
    """Return one saved draft answer as text."""
    answer = draft_data(draft).get("answers", {}).get(key)
    return answer or ""


def remove_draft_answer(draft: ReportDraft, key: str) -> None:
    """Remove one saved answer from draft JSON data."""
    data = draft_data(draft)
    answers = dict(data.get("answers", {}))
    answers.pop(key, None)
    data["answers"] = answers
    draft.draft_data_json = data


def store_crm_reference(
    draft: ReportDraft,
    reference_key: str,
    reference: Any,
) -> None:
    """Store a gateway DTO snapshot in draft JSON data."""
    data = draft_data(draft)
    references = dict(data.get(CRM_REFERENCES_KEY, {}))
    references[reference_key] = asdict(reference)
    draft.draft_data_json = {
        **data,
        CRM_REFERENCES_KEY: references,
    }


def clear_crm_reference(draft: ReportDraft, reference_key: str) -> None:
    """Remove one gateway DTO snapshot from draft JSON data."""
    data = draft_data(draft)
    references = dict(data.get(CRM_REFERENCES_KEY, {}))
    references.pop(reference_key, None)
    draft.draft_data_json = {
        **data,
        CRM_REFERENCES_KEY: references,
    }


def crm_reference(
    draft: ReportDraft,
    reference_key: str,
) -> dict[str, Any] | None:
    """Return one stored gateway DTO snapshot."""
    reference = draft_data(draft).get(CRM_REFERENCES_KEY, {}).get(reference_key)
    return reference if isinstance(reference, dict) else None


def crm_reference_value(
    draft: ReportDraft,
    reference_key: str,
    value_key: str,
) -> Any:
    """Return one value from a stored gateway DTO snapshot."""
    reference = crm_reference(draft, reference_key)
    return reference.get(value_key) if reference is not None else None


def display_value(value: Any, empty: str = "Not provided") -> str:
    """Return a display-safe value."""
    if value is None:
        return empty

    text = str(value).strip()
    if not text:
        return empty

    return DISPLAY_VALUE_LABELS.get(text, text)
