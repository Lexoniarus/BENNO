"""Review and final-text helpers for visit reports."""

import re
from typing import Any

from benno.enums import AccountType, CustomerContextType, VisitType
from benno.extensions import db
from benno.models import ReportDraft
from benno.services.ai_provider import AiProviderError, AiService
from benno.services.report_ai_context import clean_ai_text, store_ai_error
from benno.services.report_shortcuts import mentions_inside_sales_follow_up
from benno.services.report_state import (
    ACCOUNT_TYPE_OVERRIDE_KEY,
    AI_CACHE_KEY,
    INSIDE_SALES_FOLLOW_UP_KEY,
    REMINDER_SUPPRESSED_KEY,
    crm_reference,
    display_value,
    draft_data,
)
from benno.services.report_steps import CORRECTION_FIELDS, RATING_FIELDS


def build_report_review(
    draft: ReportDraft,
    ai_service: AiService | None = None,
) -> dict[str, Any]:
    """Build a human-readable review from a report draft."""
    review_text = review_text_for_draft(draft, ai_service)
    final_report_text = final_report_text_for_draft(draft, ai_service)

    return {
        "review_text": review_text,
        "sections": _build_review_sections(draft),
        "final_report_text": final_report_text,
        "correction_fields": CORRECTION_FIELDS,
        "structured_correction_fields": structured_correction_fields(draft),
        "status": draft.report_status,
    }


def _build_review_sections(draft: ReportDraft) -> list[tuple[str, str]]:
    answers = draft_data(draft).get("answers", {})
    return [
        *_core_review_sections(draft, answers),
        *_reference_review_sections(draft, answers),
        *_closing_review_sections(draft, answers),
    ]


def _core_review_sections(
    draft: ReportDraft,
    answers: dict[str, Any],
) -> list[tuple[str, str]]:
    return [
        ("AKL-Name", display_value(answers.get("visit_context"))),
        ("AKL-Typ", display_akl_type(draft)),
        ("Besuchsart", display_value(draft.visit_type)),
        ("Kontakt/Teilnehmer", display_value(answers.get("participants"))),
        ("Besuchsdatum", display_value(draft.visit_date)),
        ("Ziel/Thema", display_value(answers.get("target_topic"))),
        ("Info", display_value(draft.summary)),
        ("Vereinbarung", display_value(draft.outcome)),
        ("Nächster Schritt", display_value(draft.next_action)),
    ]


def _reference_review_sections(
    draft: ReportDraft,
    answers: dict[str, Any],
) -> list[tuple[str, str]]:
    return [
        _review_section(
            "Termin ab",
            draft.follow_up_date or answers.get("next_appointment_date"),
            empty="Nicht relevant",
        ),
        _review_section(
            "Angebotsbezug",
            answers.get("offer_reference"),
            empty="Nicht relevant",
        ),
        _review_section(
            "Auftragsbezug",
            answers.get("order_reference"),
            empty="Nicht relevant",
        ),
    ]


def _closing_review_sections(
    draft: ReportDraft,
    answers: dict[str, Any],
) -> list[tuple[str, str]]:
    return [
        _review_section(
            "Stärke",
            answers.get("strength_text"),
            empty="Nicht angegeben",
        ),
        _review_section(
            "Schwäche",
            answers.get("weakness_text"),
            empty="Nicht angegeben",
        ),
        ("Bewertungen", format_ratings(draft.ratings_json)),
        ("Wiedervorlagen", format_task_preview(draft)),
    ]


def structured_correction_fields(draft: ReportDraft) -> list[dict[str, Any]]:
    """Return directly editable review fields for STT correction."""
    answers = dict(draft_data(draft).get("answers", {}))
    return [
        _correction_field("visit_context", "AKL-Name", answers.get("visit_context")),
        _correction_field(
            "account_type",
            "AKL-Typ",
            account_type_value(draft),
            field_type="select",
            options=account_type_options(),
        ),
        _correction_field(
            "visit_type",
            "Besuchsart",
            draft.visit_type,
            field_type="select",
            options=visit_type_options(),
        ),
        _correction_field(
            "participants",
            "Kontakt/Teilnehmer",
            answers.get("participants"),
        ),
        _correction_field(
            "visit_date",
            "Besuchsdatum",
            draft.visit_date.isoformat() if draft.visit_date else "",
            field_type="date",
        ),
        _correction_field("target_topic", "Ziel/Thema", answers.get("target_topic")),
        _correction_field("info_text", "Info", draft.summary, field_type="textarea"),
        _correction_field(
            "agreement_text",
            "Vereinbarung",
            draft.outcome,
            field_type="textarea",
        ),
        _correction_field(
            "next_action",
            "Nächster Schritt",
            draft.next_action,
            field_type="textarea",
        ),
        _correction_field(
            "next_appointment_date",
            "Termin ab",
            draft.follow_up_date.isoformat() if draft.follow_up_date else "",
            field_type="date",
        ),
        _correction_field(
            "offer_reference",
            "Angebotsbezug",
            answers.get("offer_reference"),
        ),
        _correction_field(
            "order_reference",
            "Auftragsbezug",
            answers.get("order_reference"),
        ),
        _correction_field(
            "reminder_message",
            "Wiedervorlage",
            reminder_message(draft) if reminder_preview_titles(draft) else "",
            field_type="textarea",
        ),
        *_rating_correction_fields(draft),
    ]


def _correction_field(
    key: str,
    label: str,
    value: Any,
    *,
    field_type: str = "text",
    options: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "type": field_type,
        "value": "" if value is None else str(value),
        "options": options or [],
    }


def _rating_correction_fields(draft: ReportDraft) -> list[dict[str, Any]]:
    ratings = dict(draft.ratings_json)
    fields = []
    for rating_key, _label_en, label_de in RATING_FIELDS:
        rating = ratings.get(rating_key)
        value = rating.get("value") if isinstance(rating, dict) else ""
        fields.append(
            _correction_field(
                rating_key,
                label_de,
                value,
                field_type="number",
            )
        )
    return fields


def account_type_options() -> list[tuple[str, str]]:
    """Return selectable AKL account type labels."""
    return [
        (AccountType.ADDRESS.value, "Adresse / Interessent"),
        (AccountType.CUSTOMER.value, "Kunde"),
        (AccountType.SUPPLIER.value, "Lieferant"),
    ]


def visit_type_options() -> list[tuple[str, str]]:
    """Return selectable visit type labels."""
    return [
        (VisitType.IN_PERSON.value, "Vor Ort"),
        (VisitType.VIRTUAL.value, "Virtuell"),
        (VisitType.PHONE.value, "Telefonisch"),
    ]


def display_akl_type(draft: ReportDraft) -> str:
    """Return a German AKL/account classification label."""
    account_type = account_type_value(draft)
    context_type = draft.customer_context_type
    if (
        account_type == AccountType.ADDRESS.value
        and context_type == CustomerContextType.NEW_LEAD.value
    ):
        return "Adresse / neuer Interessent"
    if (
        account_type == AccountType.ADDRESS.value
        and context_type == CustomerContextType.EXISTING_LEAD.value
    ):
        return "Adresse / bestehender Interessent"

    return display_value(account_type, empty="Unklar")


def account_type_value(draft: ReportDraft) -> str | None:
    """Return the best current AKL type code for review/writeback display."""
    account = crm_reference(draft, "account")
    if account is not None and account.get("account_type"):
        return str(account["account_type"])

    override = draft_data(draft).get(ACCOUNT_TYPE_OVERRIDE_KEY)
    if override:
        return str(override)

    if draft.customer_context_type in {
        CustomerContextType.NEW_LEAD.value,
        CustomerContextType.EXISTING_LEAD.value,
    }:
        return AccountType.ADDRESS.value
    if draft.customer_context_type == CustomerContextType.EXISTING_CUSTOMER.value:
        return AccountType.CUSTOMER.value

    return None


def _review_section(label: str, value: Any, empty: str) -> tuple[str, str]:
    return (label, display_value(value, empty=empty))


def review_text_for_draft(
    draft: ReportDraft,
    ai_service: AiService | None,
) -> str | None:
    """Return cached or generated review wording."""
    return cached_or_generated_ai_text(
        draft=draft,
        cache_key="review_text",
        fallback_text=None,
        ai_service=ai_service,
        generator_name="draft_review_text",
    )


def final_report_text_for_draft(
    draft: ReportDraft,
    ai_service: AiService | None,
) -> str:
    """Return cached/generated final report text with deterministic fallback."""
    fallback_text = build_final_report_text(draft)
    generated_text = cached_or_generated_ai_text(
        draft=draft,
        cache_key="final_report_text",
        fallback_text=fallback_text,
        ai_service=ai_service,
        generator_name="draft_final_report_text",
    )

    return generated_text or fallback_text


def cached_or_generated_ai_text(
    draft: ReportDraft,
    cache_key: str,
    fallback_text: str | None,
    ai_service: AiService | None,
    generator_name: str,
) -> str | None:
    """Return cached text or ask the configured AI service once."""
    ai_cache = _ai_cache(draft)
    cached_text = ai_cache.get(cache_key)
    if cached_text:
        return normalize_report_display_text(cached_text)

    if ai_service is None:
        return fallback_text

    generator = getattr(ai_service, generator_name)
    try:
        generated_text = generator(draft_context(draft))
    except AiProviderError:
        store_ai_error(draft, f"{cache_key}_generation_failed")
        return fallback_text

    cleaned_text = clean_ai_text(generated_text, 8000)
    if not cleaned_text:
        return fallback_text

    cleaned_text = normalize_report_display_text(cleaned_text)
    persist_generated_ai_text(draft, cache_key, cleaned_text)
    return cleaned_text


def build_final_report_text(draft: ReportDraft) -> str:
    """Build deterministic German final report text."""
    answers = draft_data(draft).get("answers", {})
    report_lines = [
        "Besuchsbericht",
        "",
        f"AKL-Name: {display_value(answers.get('visit_context'))}",
        f"AKL-Typ: {display_akl_type(draft)}",
        f"Besuchsart: {display_value(draft.visit_type)}",
        f"Teilnehmer: {display_value(answers.get('participants'))}",
        f"Besuchsdatum: {display_value(draft.visit_date)}",
        f"Ziel/Thema: {display_value(answers.get('target_topic'))}",
        "",
        f"Info: {draft.summary or 'Nicht angegeben'}",
        f"Vereinbarung: {draft.outcome or 'Nicht angegeben'}",
        f"Nächster Schritt: {draft.next_action or 'Nicht angegeben'}",
        f"Stärke: {display_value(answers.get('strength_text'), 'Nicht angegeben')}",
        f"Schwäche: {display_value(answers.get('weakness_text'), 'Nicht angegeben')}",
        "",
        f"Bewertungen: {format_ratings(draft.ratings_json)}",
    ]
    return "\n".join(report_lines)


def normalize_report_display_text(text: str) -> str:
    """Convert lightweight Markdown-like AI output to safe readable plaintext."""
    normalized_lines = []
    for line in text.splitlines():
        cleaned_line = _normalize_report_line(line)
        if cleaned_line is None:
            continue

        normalized_lines.append(cleaned_line)

    normalized_text = "\n".join(_collapse_blank_lines(normalized_lines)).strip()
    return _normalize_report_context_wording(normalized_text)


def _normalize_report_line(line: str) -> str | None:
    stripped_line = line.strip()
    if not stripped_line:
        return ""
    if re.fullmatch(r"[-*_]{3,}", stripped_line):
        return None

    stripped_line = re.sub(r"^#{1,6}\s*", "", stripped_line)
    stripped_line = re.sub(r"^\*\s+", "- ", stripped_line)
    stripped_line = re.sub(r"\*\*(.*?)\*\*", r"\1", stripped_line)
    stripped_line = re.sub(r"__(.*?)__", r"\1", stripped_line)
    stripped_line = re.sub(
        r"(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)",
        r"\1",
        stripped_line,
    )

    return stripped_line.strip()


def _collapse_blank_lines(lines: list[str]) -> list[str]:
    collapsed_lines = []
    previous_blank = False
    for line in lines:
        is_blank = line == ""
        if is_blank and previous_blank:
            continue

        collapsed_lines.append(line)
        previous_blank = is_blank

    return collapsed_lines


def _normalize_report_context_wording(text: str) -> str:
    return re.sub(
        r"\bCRM[\s-]+Besuchsbericht\b",
        "Mock-eNVenta-Besuchsbericht",
        text,
        flags=re.IGNORECASE,
    )


def format_ratings(ratings: dict[str, Any]) -> str:
    """Format eNVenta ratings for display."""
    if not ratings:
        return "Nicht angegeben"

    parts = []
    for rating_key, _label_en, label_de in RATING_FIELDS:
        rating = ratings.get(rating_key)
        if rating is None:
            continue
        value = rating.get("value") or "nicht bewertet"
        reason = rating.get("reason") or "Keine Begründung angegeben"
        parts.append(f"{label_de}: {value}/10 ({reason})")

    return "; ".join(parts) if parts else "Nicht angegeben"


def format_task_preview(draft: ReportDraft) -> str:
    """Format reminder preview text for review."""
    reminder_titles = reminder_preview_titles(draft)
    if not reminder_titles:
        return "Keine"

    return "; ".join(reminder_titles)


def reminder_message(draft: ReportDraft) -> str:
    """Return the reminder message that would be written back."""
    return (
        draft_data(draft).get("reminder_message")
        or draft.next_action
        or "Bitte Besuchsbericht prüfen und Folgeaktion übernehmen."
    )


def reminder_preview_titles(draft: ReportDraft) -> list[str]:
    """Return reminder preview labels for review and AI draft context."""
    if not draft_has_reminder_request(draft):
        return []

    message = reminder_message(draft)
    due_date = (
        draft.follow_up_date.isoformat() if draft.follow_up_date else "ohne Datum"
    )
    return [f"Wiedervorlage Innendienst ({due_date}): {message}"]


def draft_has_reminder_request(draft: ReportDraft) -> bool:
    """Return whether the draft should create a follow-up reminder."""
    data = draft_data(draft)
    if data.get(REMINDER_SUPPRESSED_KEY):
        return False
    if data.get(INSIDE_SALES_FOLLOW_UP_KEY):
        return True

    return any(
        mentions_inside_sales_follow_up(text)
        for text in (
            data.get("reminder_message"),
            draft.next_action,
            draft.outcome,
            draft.summary,
        )
        if text
    )


def draft_context(draft: ReportDraft) -> dict[str, Any]:
    """Build validated draft context for review/final text generation."""
    answers = dict(draft_data(draft).get("answers", {}))
    return {
        "visit_context": answers.get("visit_context"),
        "visit_type": draft.visit_type,
        "participants": answers.get("participants"),
        "visit_date": str(draft.visit_date) if draft.visit_date else None,
        "target_topic": answers.get("target_topic"),
        "info_text": draft.summary,
        "agreement_text": draft.outcome,
        "next_action": draft.next_action,
        "next_appointment_date": (
            str(draft.follow_up_date) if draft.follow_up_date else None
        ),
        "offer_reference": answers.get("offer_reference"),
        "order_reference": answers.get("order_reference"),
        "strength_text": answers.get("strength_text"),
        "weakness_text": answers.get("weakness_text"),
        "ratings": dict(draft.ratings_json),
        "reminders": reminder_preview_titles(draft),
        "status": draft.report_status,
    }


def clear_ai_cache(draft: ReportDraft) -> None:
    """Clear cached generated review/final text after draft changes."""
    data = draft_data(draft)
    if AI_CACHE_KEY not in data:
        return

    data.pop(AI_CACHE_KEY)
    draft.draft_data_json = data


def _ai_cache(draft: ReportDraft) -> dict[str, str]:
    return dict(draft_data(draft).get(AI_CACHE_KEY, {}))


def store_ai_cache_value(
    draft: ReportDraft,
    cache_key: str,
    generated_text: str,
) -> None:
    """Store one generated AI text in draft JSON data."""
    data = draft_data(draft)
    ai_cache = dict(data.get(AI_CACHE_KEY, {}))
    ai_cache[cache_key] = generated_text
    draft.draft_data_json = {
        **data,
        AI_CACHE_KEY: ai_cache,
    }


def persist_generated_ai_text(
    draft: ReportDraft,
    cache_key: str,
    generated_text: str,
) -> None:
    """Persist generated AI text immediately so GET refreshes do not recall AI."""
    store_ai_cache_value(draft, cache_key, generated_text)
    db.session.commit()
