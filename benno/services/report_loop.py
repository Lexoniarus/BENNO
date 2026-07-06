"""Deterministic text report loop for Phase 4."""

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from benno.enums import (
    CustomerContextType,
    InsideSalesTaskType,
    MessageSender,
    MessageType,
    ReasonCode,
    ReportSection,
    ReportStatus,
    SectionStatus,
    UserIntent,
    ValidationStatus,
)
from benno.extensions import db
from benno.models import (
    Chat,
    ChatMessage,
    FinalReport,
    InsideSalesTask,
    ReportDraft,
    User,
    utc_now,
)
from benno.services.ai_provider import (
    AiMessageAnalysis,
    AiProviderError,
    AiService,
    get_ai_service,
)
from benno.services.mock_crm import (
    find_contacts,
    find_customers,
    find_leads,
    find_offers,
    find_orders,
)

REVIEW_STEP = "review"
AI_CACHE_KEY = "ai_cache"
MUTABLE_REPORT_STATUSES = {
    ReportStatus.IN_PROGRESS.value,
    ReportStatus.READY_FOR_REVIEW.value,
}


@dataclass(frozen=True)
class ReportStep:
    """One deterministic question in the Phase 4 report loop."""

    key: str
    section: ReportSection
    question: str
    question_de: str


RATING_FIELDS = (
    ("sales_opportunity", "sales opportunity", "Verkaufschance"),
    ("meeting_mood", "meeting mood", "Gesprächsstimmung"),
    ("priority", "priority", "Priorität"),
    ("closing_probability", "closing probability", "Abschlusswahrscheinlichkeit"),
    ("need_for_action", "need for action", "Handlungsbedarf"),
    ("customer_satisfaction", "customer satisfaction", "Kundenzufriedenheit"),
)
BASE_CORRECTION_FIELDS = (
    ("customer_context", "Kunde oder Lead"),
    ("contacts", "Teilnehmer"),
    ("visit_reason", "Besuchsgrund"),
    ("summary", "Zusammenfassung"),
    ("outcome", "Ergebnis"),
    ("next_action", "Nächster Schritt"),
    ("offer_reference", "Angebotsbezug"),
    ("order_reference", "Auftragsbezug"),
)
CORRECTION_FIELDS = BASE_CORRECTION_FIELDS + tuple(
    (f"rating_{rating_key}", f"Bewertung: {label_de}")
    for rating_key, _label_en, label_de in RATING_FIELDS
)

REPORT_STEPS = (
    ReportStep(
        key="customer_context",
        section=ReportSection.CUSTOMER_CONTEXT,
        question=(
            "Which customer or lead was this visit about? "
            "Mention if this is a new lead."
        ),
        question_de=(
            "Um welchen Kunden oder Lead ging es bei diesem Besuch? "
            "Erwähne bitte, falls es ein neuer Lead ist."
        ),
    ),
    ReportStep(
        key="contacts",
        section=ReportSection.CONTACTS,
        question="Who participated in the meeting?",
        question_de="Wer hat an dem Gespräch teilgenommen?",
    ),
    ReportStep(
        key="visit_reason",
        section=ReportSection.VISIT_REASON,
        question="What was the main reason for the visit?",
        question_de="Was war der Hauptgrund für den Besuch?",
    ),
    ReportStep(
        key="summary",
        section=ReportSection.SUMMARY,
        question="Please summarize the key discussion points.",
        question_de="Fasse bitte die wichtigsten Gesprächspunkte zusammen.",
    ),
    ReportStep(
        key="outcome",
        section=ReportSection.OUTCOME,
        question="What was agreed or decided?",
        question_de="Was wurde vereinbart oder entschieden?",
    ),
    ReportStep(
        key="next_action",
        section=ReportSection.NEXT_ACTION,
        question="What is the next action or follow-up?",
        question_de="Was ist der nächste Schritt oder die Wiedervorlage?",
    ),
    ReportStep(
        key="offer_reference",
        section=ReportSection.OFFER_REFERENCE,
        question="Is there an offer reference? If not, answer 'none'.",
        question_de=(
            "Gibt es einen Angebotsbezug? Falls nicht, antworte mit 'keiner'."
        ),
    ),
    ReportStep(
        key="order_reference",
        section=ReportSection.ORDER_REFERENCE,
        question="Is there an order reference? If not, answer 'none'.",
        question_de=(
            "Gibt es einen Auftragsbezug? Falls nicht, antworte mit 'keiner'."
        ),
    ),
    *(
        ReportStep(
            key=f"rating_{rating_key}",
            section=ReportSection.RATINGS,
            question=f"Rate the {label} from 1 to 10 and add a short reason.",
            question_de=(
                f"Bewerte {label_de} von 1 bis 10 und ergänze eine kurze Begründung."
            ),
        )
        for rating_key, label, label_de in RATING_FIELDS
    ),
)


def start_report_chat(sales_user: User) -> Chat:
    """Create a new report chat and initial draft."""
    initial_step = REPORT_STEPS[0]
    initial_question = _step_question(initial_step, sales_user.preferred_language)
    initial_message = _initial_report_message(sales_user, initial_question)
    section_statuses = _initial_section_statuses()

    chat = Chat(
        sales_user=sales_user,
        session_language=sales_user.preferred_language,
        status=ReportStatus.IN_PROGRESS.value,
    )
    draft = ReportDraft(
        chat=chat,
        sales_user=sales_user,
        report_status=ReportStatus.IN_PROGRESS.value,
        session_language=sales_user.preferred_language,
        section_statuses_json=section_statuses,
        missing_sections_json=_missing_sections(section_statuses),
        ratings_json={},
        draft_data_json={
            "current_step": initial_step.key,
            "completed_steps": [],
            "answers": {},
        },
        last_question=initial_message,
    )

    db.session.add_all([chat, draft])
    db.session.flush()
    _add_assistant_message(chat, initial_message)
    db.session.commit()

    return chat


def process_report_message(chat: Chat, message_text: str) -> Chat:
    """Store a user answer and advance the deterministic report state."""
    return process_report_message_with_ai(chat, message_text, get_ai_service())


def process_report_message_with_ai(
    chat: Chat,
    message_text: str,
    ai_service: AiService | None,
) -> Chat:
    """Store a user answer and advance the assisted report state."""
    draft = _require_draft(chat)
    _ensure_report_is_mutable(chat)
    normalized_message = message_text.strip()
    if not normalized_message:
        raise ValueError("Message text must not be empty.")

    _add_user_message(chat, message_text)

    current_step = _current_step(draft)
    if current_step is None:
        _add_assistant_message(chat, _review_ready_message(chat))
        db.session.commit()
        return chat

    analysis = _analyze_report_message(
        draft,
        current_step,
        normalized_message,
        ai_service,
    )
    applied_steps = _apply_assisted_answers(
        draft,
        current_step,
        normalized_message,
        analysis,
    )
    next_step = _advance_after_applied_steps(draft, applied_steps)
    next_question = _next_question(chat, next_step, analysis)
    _add_assistant_message(chat, next_question)
    db.session.commit()

    return chat


def _initial_report_message(sales_user: User, initial_question: str) -> str:
    username = sales_user.username or "du"
    return (
        f"Hallo {username}, ich bin bereit für deinen Besuchsbericht. "
        f"{initial_question}"
    )


def apply_report_correction(
    chat: Chat,
    field_key: str,
    correction_text: str,
) -> Chat:
    """Apply a targeted correction during final review."""
    draft = _require_draft(chat)
    _ensure_report_is_mutable(chat)
    if not _is_ready_for_review(draft):
        raise ValueError("Corrections are only available during final review.")

    normalized_correction = correction_text.strip()
    if not normalized_correction:
        raise ValueError("Correction text must not be empty.")

    correction_step = _correction_step(field_key)
    _add_correction_message(chat, correction_step.key, normalized_correction)
    _apply_step_answer(draft, correction_step, normalized_correction)
    _refresh_missing_sections(draft)
    draft.report_status = ReportStatus.READY_FOR_REVIEW.value
    chat.status = ReportStatus.READY_FOR_REVIEW.value
    draft.last_question = "Korrektur gespeichert. Bitte prüfe den Bericht erneut."
    draft.draft_data_json = {
        **_draft_data(draft),
        "current_step": REVIEW_STEP,
    }
    _set_section_status(draft, ReportSection.FINAL_REPORT, SectionStatus.DETECTED)
    _add_assistant_message(chat, draft.last_question)
    db.session.commit()

    return chat


def build_report_review(
    draft: ReportDraft,
    ai_service: AiService | None = None,
) -> dict[str, Any]:
    """Build a human-readable review from a report draft."""
    draft_data = _draft_data(draft)
    answers = draft_data.get("answers", {})
    review_text = _review_text(draft, ai_service)
    final_report_text = _final_report_text(draft, ai_service)

    return {
        "review_text": review_text,
        "sections": [
            ("Kunde oder Lead", _display_value(answers.get("customer_context"))),
            ("Teilnehmer", _display_value(answers.get("contacts"))),
            ("Besuchsgrund", _display_value(answers.get("visit_reason"))),
            ("Zusammenfassung", _display_value(draft.summary)),
            ("Ergebnis", _display_value(draft.outcome)),
            ("Nächster Schritt", _display_value(draft.next_action)),
            (
                "Angebotsbezug",
                _display_value(answers.get("offer_reference"), empty="Nicht relevant"),
            ),
            (
                "Auftragsbezug",
                _display_value(answers.get("order_reference"), empty="Nicht relevant"),
            ),
            ("Bewertungen", _format_ratings(draft.ratings_json)),
            ("Innendienst-Aufgaben", _format_task_preview(draft)),
        ],
        "final_report_text": final_report_text,
        "correction_fields": CORRECTION_FIELDS,
        "status": draft.report_status,
    }


def confirm_report(
    chat: Chat,
    ai_service: AiService | None = None,
) -> FinalReport:
    """Create or return the confirmed final report for a completed chat."""
    draft = _require_draft(chat)
    if chat.final_report is not None:
        return chat.final_report

    if not _is_ready_for_review(draft):
        raise ValueError("Report is not ready for confirmation.")

    final_report = FinalReport(
        chat=chat,
        sales_user=chat.sales_user,
        customer_id=draft.customer_id,
        lead_id=draft.lead_id,
        contact_id=draft.contact_id,
        visit_date=draft.visit_date,
        visit_type=draft.visit_type,
        reason_code=draft.reason_code,
        related_offer_id=draft.related_offer_id,
        related_order_id=draft.related_order_id,
        external_offer_reference=draft.external_offer_reference,
        summary=draft.summary or "",
        outcome=draft.outcome,
        next_action=draft.next_action,
        follow_up_date=draft.follow_up_date,
        ratings_json=dict(draft.ratings_json),
        report_language=draft.session_language,
        final_report_text=_final_report_text(draft, ai_service),
        status=ReportStatus.CONFIRMED.value,
        confirmed_at=utc_now(),
    )
    db.session.add(final_report)
    db.session.flush()

    for task in _build_inside_sales_tasks(draft, final_report):
        db.session.add(task)

    chat.status = ReportStatus.CONFIRMED.value
    draft.report_status = ReportStatus.CONFIRMED.value
    _set_section_status(draft, ReportSection.USER_CONFIRMATION, SectionStatus.CONFIRMED)
    _add_assistant_message(chat, "The visit report has been confirmed and saved.")
    db.session.commit()

    return final_report


def cancel_report(chat: Chat) -> None:
    """Cancel unfinished report work."""
    draft = _require_draft(chat)
    _ensure_report_is_mutable(chat)
    chat.status = ReportStatus.CANCELLED.value
    draft.report_status = ReportStatus.CANCELLED.value
    _add_assistant_message(chat, "The visit report has been cancelled.")
    db.session.commit()


def is_ready_for_review(chat: Chat) -> bool:
    """Return whether the chat can show the final review."""
    return chat.report_draft is not None and _is_ready_for_review(chat.report_draft)


def _require_draft(chat: Chat) -> ReportDraft:
    if chat.report_draft is None:
        raise ValueError("Report chat has no draft.")

    return chat.report_draft


def _ensure_report_is_mutable(chat: Chat) -> None:
    if chat.status not in MUTABLE_REPORT_STATUSES:
        raise ValueError("This report can no longer be changed.")


def _current_step(draft: ReportDraft) -> ReportStep | None:
    current_key = _draft_data(draft).get("current_step")
    if current_key == REVIEW_STEP:
        return None

    return next((step for step in REPORT_STEPS if step.key == current_key), None)


def _correction_step(field_key: str) -> ReportStep:
    correction_step = next(
        (step for step in REPORT_STEPS if step.key == field_key),
        None,
    )
    if correction_step is None:
        raise ValueError("Unknown correction field.")

    return correction_step


def _apply_step_answer(
    draft: ReportDraft,
    step: ReportStep,
    message_text: str,
) -> None:
    _clear_ai_cache(draft)
    draft_data = _draft_data(draft)
    answers = dict(draft_data.get("answers", {}))
    answers[step.key] = message_text
    draft_data["answers"] = answers
    draft.draft_data_json = draft_data

    if step.key == "customer_context":
        _update_customer_context(draft, message_text)
    elif step.key == "contacts":
        _update_contacts(draft, message_text)
    elif step.key == "visit_reason":
        draft.reason_code = _classify_reason(message_text)
    elif step.key == "summary":
        draft.summary = message_text
    elif step.key == "outcome":
        draft.outcome = message_text
    elif step.key == "next_action":
        draft.next_action = message_text
        draft.follow_up_date = _parse_iso_date(message_text)
    elif step.key == "offer_reference":
        _update_offer_reference(draft, message_text)
    elif step.key == "order_reference":
        _update_order_reference(draft, message_text)
    elif step.key.startswith("rating_"):
        _update_rating(draft, step.key, message_text)

    _set_section_status(draft, step.section, _section_status_for_answer(step, draft))


def _analyze_report_message(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    ai_service: AiService | None,
) -> AiMessageAnalysis | None:
    if ai_service is None:
        return None

    context = _ai_message_context(draft, current_step)
    try:
        analysis = ai_service.analyze_report_message(context, message_text)
    except AiProviderError as error:
        _store_ai_error(draft, _ai_error_code(error))
        return None

    if analysis is None:
        return None

    sanitized_analysis = _sanitize_ai_analysis(analysis)
    _store_ai_analysis(draft, sanitized_analysis)
    return sanitized_analysis


def _ai_message_context(
    draft: ReportDraft,
    current_step: ReportStep,
) -> dict[str, Any]:
    return {
        "current_step": current_step.key,
        "current_question": _step_question(current_step, draft.session_language),
        "missing_sections": list(draft.missing_sections_json),
        "known_answers": dict(_draft_data(draft).get("answers", {})),
        "ratings": dict(draft.ratings_json),
        "allowed_section_update_keys": _allowed_update_keys(),
    }


def _sanitize_ai_analysis(analysis: AiMessageAnalysis) -> AiMessageAnalysis:
    allowed_keys = set(_allowed_update_keys())
    return AiMessageAnalysis(
        intent=analysis.intent,
        intent_confidence=analysis.intent_confidence,
        target_sections=[
            section for section in analysis.target_sections if section in allowed_keys
        ],
        section_updates={
            key: value.strip()
            for key, value in analysis.section_updates.items()
            if key in allowed_keys and isinstance(value, str) and value.strip()
        },
        suggested_next_section=_clean_section_key(analysis.suggested_next_section),
        suggested_next_question=_clean_ai_text(analysis.suggested_next_question, 500),
    )


def _apply_assisted_answers(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    analysis: AiMessageAnalysis | None,
) -> list[ReportStep]:
    completed_before_message = set(_draft_data(draft).get("completed_steps", []))
    applied_steps = []
    current_answer = _answer_for_step(current_step, message_text, analysis)
    if current_answer is not None:
        _apply_step_answer(draft, current_step, current_answer)
        applied_steps.append(current_step)

    for step in _additional_ai_steps(
        current_step,
        analysis,
        completed_before_message,
    ):
        _apply_step_answer(draft, step, analysis.section_updates[step.key])
        applied_steps.append(step)

    return applied_steps


def _answer_for_step(
    step: ReportStep,
    message_text: str,
    analysis: AiMessageAnalysis | None,
) -> str | None:
    if analysis is None:
        return message_text

    suggested_value = analysis.section_updates.get(step.key)
    if not suggested_value:
        if analysis.intent == UserIntent.CORRECTION:
            return None
        return message_text

    return suggested_value


def _additional_ai_steps(
    current_step: ReportStep,
    analysis: AiMessageAnalysis | None,
    completed_before_message: set[str],
) -> list[ReportStep]:
    if analysis is None:
        return []

    current_index = _step_index(current_step)
    return [
        step
        for step in REPORT_STEPS
        if step.key != current_step.key
        and step.key in analysis.section_updates
        and _can_apply_ai_update(
            step,
            current_index,
            analysis,
            completed_before_message,
        )
    ]


def _can_apply_ai_update(
    step: ReportStep,
    current_index: int,
    analysis: AiMessageAnalysis,
    completed_before_message: set[str],
) -> bool:
    if analysis.intent == UserIntent.CORRECTION and _analysis_targets_step(
        analysis,
        step,
    ):
        return True

    if step.key in completed_before_message:
        return False

    return _step_index(step) > current_index


def _analysis_targets_step(
    analysis: AiMessageAnalysis,
    step: ReportStep,
) -> bool:
    return step.key in analysis.target_sections or step.section.value in (
        analysis.target_sections
    )


def _suggested_question(
    next_step: ReportStep,
    analysis: AiMessageAnalysis | None,
) -> str | None:
    if analysis is None:
        return None

    suggested_question = analysis.suggested_next_question
    if not suggested_question:
        return None
    if analysis.suggested_next_section != next_step.key:
        return None

    return suggested_question


def _allowed_update_keys() -> list[str]:
    return [step.key for step in REPORT_STEPS]


def _store_ai_analysis(
    draft: ReportDraft,
    analysis: AiMessageAnalysis,
) -> None:
    draft.draft_data_json = {
        **_draft_data(draft),
        "last_ai_analysis": analysis.model_dump(mode="json"),
    }


def _store_ai_error(draft: ReportDraft, error_code: str) -> None:
    draft.draft_data_json = {
        **_draft_data(draft),
        "last_ai_error": error_code,
    }


def _ai_error_code(error: AiProviderError) -> str:
    error_text = _error_chain_text(error)
    if "additionalproperties" in error_text or "schema" in error_text:
        return "message_analysis_schema_failed"
    if "rate" in error_text or "quota" in error_text:
        return "message_analysis_rate_limited"
    if "api key" in error_text or "authentication" in error_text:
        return "message_analysis_auth_failed"

    return "message_analysis_failed"


def _error_chain_text(error: BaseException) -> str:
    messages = []
    current_error: BaseException | None = error
    while current_error is not None:
        messages.append(str(current_error).lower())
        current_error = current_error.__cause__

    return " ".join(messages)


def _clean_ai_text(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None

    cleaned_value = value.strip()
    if not cleaned_value:
        return None

    return cleaned_value[:max_length]


def _clean_section_key(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned_value = value.strip()
    if cleaned_value not in _allowed_update_keys():
        return None

    return cleaned_value


def _advance_after_applied_steps(
    draft: ReportDraft,
    applied_steps: list[ReportStep],
) -> ReportStep | None:
    draft_data = _draft_data(draft)
    completed_steps = list(draft_data.get("completed_steps", []))
    for step in applied_steps:
        if step.key not in completed_steps:
            completed_steps.append(step.key)

    next_step = _first_incomplete_step(completed_steps)
    draft_data["completed_steps"] = completed_steps
    draft_data["current_step"] = next_step.key if next_step else REVIEW_STEP
    draft.draft_data_json = draft_data

    _refresh_missing_sections(draft)
    if next_step is None:
        draft.report_status = ReportStatus.READY_FOR_REVIEW.value
        draft.chat.status = ReportStatus.READY_FOR_REVIEW.value
        _set_section_status(draft, ReportSection.FINAL_REPORT, SectionStatus.DETECTED)

    return next_step


def _first_incomplete_step(completed_steps: list[str]) -> ReportStep | None:
    completed_step_set = set(completed_steps)
    return next(
        (step for step in REPORT_STEPS if step.key not in completed_step_set),
        None,
    )


def _step_index(step: ReportStep) -> int:
    step_keys = [report_step.key for report_step in REPORT_STEPS]
    return step_keys.index(step.key)


def _next_question(
    chat: Chat,
    next_step: ReportStep | None,
    analysis: AiMessageAnalysis | None,
) -> str:
    draft = _require_draft(chat)
    if next_step is None:
        message = _review_ready_message(chat)
    else:
        message = _suggested_question(next_step, analysis) or _step_question(
            next_step,
            draft.session_language,
        )

    draft.last_question = message
    return message


def _review_ready_message(chat: Chat) -> str:
    return (
        "Alle Pflichtbereiche sind vollständig. "
        f"Bitte prüfe den Bericht unter /sales/reports/{chat.id}/review."
    )


def _step_question(step: ReportStep, session_language: str | None) -> str:
    if session_language == "de":
        return step.question_de

    return step.question


def _update_customer_context(draft: ReportDraft, message_text: str) -> None:
    normalized_text = message_text.lower()
    customer_matches = find_customers(message_text)
    lead_matches = find_leads(message_text)
    draft.customer = None
    draft.lead = None
    draft.contact = None

    if _mentions_new(normalized_text) or "lead" in normalized_text:
        draft.customer_context_type = CustomerContextType.NEW_LEAD.value
        draft.validation_status = ValidationStatus.CONFIRMED_NEW.value
        return

    if len(customer_matches) == 1:
        draft.customer = customer_matches[0]
        draft.customer_context_type = CustomerContextType.EXISTING_CUSTOMER.value
        draft.validation_status = ValidationStatus.MATCHED.value
        return

    if len(lead_matches) == 1:
        draft.lead = lead_matches[0]
        draft.customer_context_type = CustomerContextType.EXISTING_LEAD.value
        draft.validation_status = ValidationStatus.MATCHED.value
        return

    draft.customer_context_type = CustomerContextType.UNCLEAR.value
    draft.validation_status = ValidationStatus.UNKNOWN.value


def _update_contacts(draft: ReportDraft, message_text: str) -> None:
    draft.contact = None
    if draft.customer_id is None:
        return

    contact_matches = find_contacts(draft.customer_id, message_text)
    if len(contact_matches) == 1:
        draft.contact = contact_matches[0]


def _update_offer_reference(draft: ReportDraft, message_text: str) -> None:
    draft.related_offer = None
    if _is_none_answer(message_text):
        draft.external_offer_reference = None
        return

    draft.external_offer_reference = message_text
    if draft.customer_id is None:
        return

    offer_matches = find_offers(draft.customer_id, message_text)
    if len(offer_matches) == 1:
        draft.related_offer = offer_matches[0]


def _update_order_reference(draft: ReportDraft, message_text: str) -> None:
    draft.related_order = None
    if _is_none_answer(message_text):
        draft.draft_data_json = {
            **_draft_data(draft),
            "order_reference_raw": None,
        }
        return

    draft.draft_data_json = {
        **_draft_data(draft),
        "order_reference_raw": message_text,
    }
    if draft.customer_id is None:
        return

    order_matches = find_orders(draft.customer_id, message_text)
    if len(order_matches) == 1:
        draft.related_order = order_matches[0]


def _update_rating(draft: ReportDraft, step_key: str, message_text: str) -> None:
    rating_key = step_key.removeprefix("rating_")
    ratings = dict(draft.ratings_json)
    ratings[rating_key] = {
        "value": _parse_rating_value(message_text),
        "reason": message_text,
    }
    draft.ratings_json = ratings


def _classify_reason(message_text: str) -> str:
    normalized_text = message_text.lower()
    if "offer" in normalized_text or "angebot" in normalized_text:
        return ReasonCode.OFFER_FOLLOW_UP.value
    if "complaint" in normalized_text or "beschwer" in normalized_text:
        return ReasonCode.COMPLAINT_RELATED.value
    if "contract" in normalized_text or "vertrag" in normalized_text:
        return ReasonCode.CONTRACT_DISCUSSION.value
    if "lead" in normalized_text or "first" in normalized_text:
        return ReasonCode.LEAD_INITIAL_CONTACT.value
    if "relationship" in normalized_text or "beziehung" in normalized_text:
        return ReasonCode.RELATIONSHIP_MEETING.value

    return ReasonCode.OTHER.value


def _parse_rating_value(message_text: str) -> int | None:
    match = re.search(r"\b(10|[1-9])\b", message_text)
    if match is None:
        return None

    return int(match.group(1))


def _parse_iso_date(message_text: str) -> date | None:
    match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", message_text)
    if match is None:
        return None

    return date.fromisoformat(match.group(0))


def _section_status_for_answer(
    step: ReportStep,
    draft: ReportDraft,
) -> SectionStatus:
    if step.key in {"offer_reference", "order_reference"}:
        answer = _draft_data(draft).get("answers", {}).get(step.key, "")
        if _is_none_answer(answer):
            return SectionStatus.NOT_APPLICABLE

    if step.section == ReportSection.RATINGS and not _all_ratings_collected(draft):
        return SectionStatus.DETECTED

    return SectionStatus.CONFIRMED


def _initial_section_statuses() -> dict[str, str]:
    return {
        section.value: SectionStatus.OPEN.value
        for section in ReportSection
        if section != ReportSection.USER_CONFIRMATION
    } | {ReportSection.USER_CONFIRMATION.value: SectionStatus.OPEN.value}


def _set_section_status(
    draft: ReportDraft,
    section: ReportSection,
    status: SectionStatus,
) -> None:
    section_statuses = dict(draft.section_statuses_json)
    section_statuses[section.value] = status.value
    draft.section_statuses_json = section_statuses


def _refresh_missing_sections(draft: ReportDraft) -> None:
    draft.missing_sections_json = _missing_sections(draft.section_statuses_json)


def _missing_sections(section_statuses: dict[str, str]) -> list[str]:
    return [
        section
        for section, status in section_statuses.items()
        if status == SectionStatus.OPEN.value
        and section
        not in {
            ReportSection.FINAL_REPORT.value,
            ReportSection.USER_CONFIRMATION.value,
        }
    ]


def _all_ratings_collected(draft: ReportDraft) -> bool:
    return all(
        rating_key in draft.ratings_json
        for rating_key, _label_en, _label_de in RATING_FIELDS
    )


def _is_ready_for_review(draft: ReportDraft) -> bool:
    return (
        draft.report_status == ReportStatus.READY_FOR_REVIEW.value
        and draft.missing_sections_json == []
    )


def _review_text(draft: ReportDraft, ai_service: AiService | None) -> str | None:
    return _cached_ai_text(
        draft=draft,
        cache_key="review_text",
        fallback_text=None,
        ai_service=ai_service,
        generator_name="draft_review_text",
    )


def _final_report_text(draft: ReportDraft, ai_service: AiService | None) -> str:
    fallback_text = _build_final_report_text(draft)
    generated_text = _cached_ai_text(
        draft=draft,
        cache_key="final_report_text",
        fallback_text=fallback_text,
        ai_service=ai_service,
        generator_name="draft_final_report_text",
    )

    return generated_text or fallback_text


def _cached_ai_text(
    draft: ReportDraft,
    cache_key: str,
    fallback_text: str | None,
    ai_service: AiService | None,
    generator_name: str,
) -> str | None:
    ai_cache = _ai_cache(draft)
    cached_text = ai_cache.get(cache_key)
    if cached_text:
        return cached_text

    if ai_service is None:
        return fallback_text

    generator = getattr(ai_service, generator_name)
    try:
        generated_text = generator(_draft_context(draft))
    except AiProviderError:
        _store_ai_error(draft, f"{cache_key}_generation_failed")
        return fallback_text

    cleaned_text = _clean_ai_text(generated_text, 8000)
    if not cleaned_text:
        return fallback_text

    _store_ai_cache_value(draft, cache_key, cleaned_text)
    db.session.commit()
    return cleaned_text


def _ai_cache(draft: ReportDraft) -> dict[str, str]:
    return dict(_draft_data(draft).get(AI_CACHE_KEY, {}))


def _store_ai_cache_value(
    draft: ReportDraft,
    cache_key: str,
    generated_text: str,
) -> None:
    draft_data = _draft_data(draft)
    ai_cache = dict(draft_data.get(AI_CACHE_KEY, {}))
    ai_cache[cache_key] = generated_text
    draft.draft_data_json = {
        **draft_data,
        AI_CACHE_KEY: ai_cache,
    }


def _clear_ai_cache(draft: ReportDraft) -> None:
    draft_data = _draft_data(draft)
    if AI_CACHE_KEY not in draft_data:
        return

    draft_data.pop(AI_CACHE_KEY)
    draft.draft_data_json = draft_data


def _draft_context(draft: ReportDraft) -> dict[str, Any]:
    answers = dict(_draft_data(draft).get("answers", {}))
    return {
        "customer_or_lead": answers.get("customer_context"),
        "contacts": answers.get("contacts"),
        "visit_reason": answers.get("visit_reason"),
        "summary": draft.summary,
        "outcome": draft.outcome,
        "next_action": draft.next_action,
        "offer_reference": answers.get("offer_reference"),
        "order_reference": answers.get("order_reference"),
        "ratings": dict(draft.ratings_json),
        "inside_sales_tasks": _task_preview_titles(draft),
        "status": draft.report_status,
    }


def _build_final_report_text(draft: ReportDraft) -> str:
    answers = _draft_data(draft).get("answers", {})
    report_lines = [
        "Besuchsbericht",
        "",
        f"Kunde/Lead: {_display_value(answers.get('customer_context'))}",
        f"Teilnehmer: {_display_value(answers.get('contacts'))}",
        f"Besuchsgrund: {_display_value(answers.get('visit_reason'))}",
        "",
        f"Zusammenfassung: {draft.summary or 'Nicht angegeben'}",
        f"Ergebnis: {draft.outcome or 'Nicht angegeben'}",
        f"Nächster Schritt: {draft.next_action or 'Nicht angegeben'}",
        "",
        f"Bewertungen: {_format_ratings(draft.ratings_json)}",
    ]
    return "\n".join(report_lines)


def _format_ratings(ratings: dict[str, Any]) -> str:
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


def _format_task_preview(draft: ReportDraft) -> str:
    task_titles = _task_preview_titles(draft)
    if not task_titles:
        return "Keine"

    return "; ".join(task_titles)


def _build_inside_sales_tasks(
    draft: ReportDraft,
    final_report: FinalReport,
) -> list[InsideSalesTask]:
    tasks = []
    for title, task_type, description in _task_definitions(draft):
        tasks.append(
            InsideSalesTask(
                final_report=final_report,
                task_type=task_type,
                title=title,
                description=description,
                detected_customer_name=_draft_answer(draft, "customer_context"),
                detected_contact_name=_draft_answer(draft, "contacts"),
                related_customer_id=draft.customer_id,
            )
        )

    return tasks


def _task_preview_titles(draft: ReportDraft) -> list[str]:
    return [title for title, _task_type, _description in _task_definitions(draft)]


def _task_definitions(draft: ReportDraft) -> list[tuple[str, str, str]]:
    definitions = []
    if draft.customer_context_type == CustomerContextType.NEW_LEAD.value:
        definitions.append(
            (
                "Review new lead",
                InsideSalesTaskType.COMPLETE_MASTER_DATA.value,
                "A new lead was mentioned and must be reviewed before CRM creation.",
            )
        )

    contact_answer = _draft_answer(draft, "contacts").lower()
    if _mentions_new(contact_answer):
        definitions.append(
            (
                "Review new contact",
                InsideSalesTaskType.COMPLETE_MASTER_DATA.value,
                "A new contact was mentioned and must be checked by inside sales.",
            )
        )

    offer_answer = _draft_answer(draft, "offer_reference").lower()
    if _is_unclear_answer(offer_answer):
        definitions.append(
            (
                "Clarify offer reference",
                InsideSalesTaskType.CLARIFY_DETAILS.value,
                "The offer reference is unclear and needs inside sales follow-up.",
            )
        )

    return definitions


def _draft_answer(draft: ReportDraft, key: str) -> str:
    answer = _draft_data(draft).get("answers", {}).get(key)
    return answer or ""


def _draft_data(draft: ReportDraft) -> dict[str, Any]:
    return dict(draft.draft_data_json or {})


def _display_value(value: Any, empty: str = "Not provided") -> str:
    if value is None:
        return empty

    text = str(value).strip()
    return text or empty


def _is_none_answer(message_text: str) -> bool:
    return message_text.strip().lower() in {
        "no",
        "none",
        "not relevant",
        "n/a",
        "na",
        "kein",
        "keine",
        "keiner",
        "nein",
    }


def _mentions_new(normalized_text: str) -> bool:
    return any(keyword in normalized_text for keyword in ("new", "neu", "unknown"))


def _is_unclear_answer(normalized_text: str) -> bool:
    return any(
        keyword in normalized_text
        for keyword in ("unclear", "unknown", "not sure", "maybe", "unklar")
    )


def _add_user_message(chat: Chat, message_text: str) -> None:
    _add_message(chat, MessageSender.USER, message_text, MessageType.FREE_INPUT)


def _add_correction_message(chat: Chat, field_key: str, message_text: str) -> None:
    _add_message(
        chat,
        MessageSender.USER,
        f"{field_key}: {message_text}",
        MessageType.CORRECTION,
    )


def _add_assistant_message(chat: Chat, message_text: str) -> None:
    _add_message(
        chat,
        MessageSender.ASSISTANT,
        message_text,
        MessageType.ASSISTANT_QUESTION,
    )


def _add_message(
    chat: Chat,
    sender: MessageSender,
    message_text: str,
    message_type: MessageType,
) -> None:
    db.session.add(
        ChatMessage(
            chat=chat,
            sender=sender.value,
            message_text=message_text,
            message_type=message_type.value,
        )
    )
