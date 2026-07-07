"""Deterministic and AI-assisted visit report loop for Phase 6."""

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from benno.enums import (
    AccountType,
    CustomerContextType,
    MessageSender,
    MessageType,
    ReasonCode,
    ReminderOwnerType,
    ReportSection,
    ReportStatus,
    SectionStatus,
    UserIntent,
    ValidationStatus,
    VisitReportStatus,
    VisitType,
)
from benno.extensions import db
from benno.models import (
    Chat,
    ChatMessage,
    FinalReport,
    MockReminder,
    MockVisitReport,
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
    create_mock_reminder,
    find_contacts,
    find_offers,
    find_orders,
    list_crm_users,
    list_field_sales_representatives,
    save_mock_visit_report,
    search_accounts,
)

REVIEW_STEP = "review"
AI_CACHE_KEY = "ai_cache"
INSIDE_SALES_FOLLOW_UP_KEY = "inside_sales_follow_up_requested"
OPTIONAL_STEP_KEYS = {"strength_text", "weakness_text", "reminders"}
OPTIONAL_REPORT_SECTIONS = {
    ReportSection.STRENGTHS.value,
    ReportSection.WEAKNESSES.value,
    ReportSection.REMINDERS.value,
}
MUTABLE_REPORT_STATUSES = {
    ReportStatus.IN_PROGRESS.value,
    ReportStatus.READY_FOR_REVIEW.value,
}


@dataclass(frozen=True)
class ReportStep:
    """One deterministic question in the Phase 6 report loop."""

    key: str
    section: ReportSection
    question: str
    question_de: str


RATING_FIELDS = (
    ("customer_satisfaction_rating", "customer satisfaction", "Zufriedenheit"),
    (
        "technical_attractiveness_rating",
        "technical attractiveness",
        "Technische Attraktivit\u00e4t",
    ),
    (
        "commercial_attractiveness_rating",
        "commercial attractiveness",
        "Kaufm\u00e4nnische Attraktivit\u00e4t",
    ),
    ("priority_rating", "priority", "Priorit\u00e4t"),
)
BASE_CORRECTION_FIELDS = (
    ("visit_context", "Besuchskontext"),
    ("visit_type", "Besuchsart"),
    ("participants", "Teilnehmer"),
    ("visit_date", "Besuchsdatum"),
    ("target_topic", "Ziel/Thema"),
    ("info_text", "Info"),
    ("agreement_text", "Vereinbarung"),
    ("next_action", "N\u00e4chster Schritt"),
    ("next_appointment_date", "Termin ab"),
    ("offer_reference", "Angebotsbezug"),
    ("order_reference", "Auftragsbezug"),
    ("strength_text", "St\u00e4rke"),
    ("weakness_text", "Schw\u00e4che"),
    ("ratings", "Bewertungen"),
    ("reminders", "Wiedervorlagen"),
)
CORRECTION_FIELDS = BASE_CORRECTION_FIELDS
REQUIREMENT_LABELS = {
    "visit_context": "Besuchskontext",
    "visit_type": "Besuchsart",
    "participants": "Teilnehmer",
    "visit_date": "Besuchsdatum",
    "target_topic": "Ziel/Thema",
    "info_text": "Info",
    "agreement_text": "Vereinbarung",
    "next_action": "N\u00e4chster Schritt",
    "next_appointment_date": "Termin ab",
    "offer_reference": "Angebotsbezug",
    "order_reference": "Auftragsbezug",
    "strength_text": "St\u00e4rke",
    "weakness_text": "Schw\u00e4che",
    "ratings": "Bewertungen",
    "reminders": "Wiedervorlagen",
}

REPORT_STEPS = (
    ReportStep(
        key="visit_context",
        section=ReportSection.CUSTOMER_CONTEXT,
        question="Which customer, lead, or contact was this visit about?",
        question_de="Um welchen Kunden, Lead oder Kontakt ging es bei dem Besuch?",
    ),
    ReportStep(
        key="visit_type",
        section=ReportSection.VISIT_TYPE,
        question="Was the visit in person, virtual, or by phone?",
        question_de="War der Besuch pers\u00f6nlich, virtuell oder telefonisch?",
    ),
    ReportStep(
        key="participants",
        section=ReportSection.CONTACTS,
        question="Who participated in the meeting?",
        question_de="Wer hat an dem Gespr\u00e4ch teilgenommen?",
    ),
    ReportStep(
        key="visit_date",
        section=ReportSection.VISIT_DATE,
        question="Was the visit today or on another date?",
        question_de="War der Besuch heute oder an einem anderen Datum?",
    ),
    ReportStep(
        key="target_topic",
        section=ReportSection.VISIT_REASON,
        question="What was the goal or main topic of the visit?",
        question_de="Was war das Ziel oder Hauptthema des Besuchs?",
    ),
    ReportStep(
        key="info_text",
        section=ReportSection.SUMMARY,
        question="What was discussed? You can describe it freely.",
        question_de="Was wurde besprochen? Du kannst es frei erz\u00e4hlen.",
    ),
    ReportStep(
        key="agreement_text",
        section=ReportSection.OUTCOME,
        question="What was agreed or decided?",
        question_de="Was wurde konkret vereinbart oder entschieden?",
    ),
    ReportStep(
        key="next_action",
        section=ReportSection.NEXT_ACTION,
        question="What is the next step, and who should own it?",
        question_de=(
            "Was ist der n\u00e4chste Schritt, " "und wer soll ihn \u00fcbernehmen?"
        ),
    ),
    ReportStep(
        key="next_appointment_date",
        section=ReportSection.NEXT_APPOINTMENT_DATE,
        question="Is there a concrete follow-up appointment or reminder date?",
        question_de="Gibt es einen konkreten Folgetermin oder Wiedervorlage-Termin?",
    ),
    ReportStep(
        key="offer_reference",
        section=ReportSection.OFFER_REFERENCE,
        question="Is there an offer or offer number? If not, answer 'none'.",
        question_de=(
            "Gibt es dazu ein Angebot oder eine Angebotsnummer? "
            "Falls nicht, antworte mit 'keine'."
        ),
    ),
    ReportStep(
        key="order_reference",
        section=ReportSection.ORDER_REFERENCE,
        question="Is there an order or order number? If not, answer 'none'.",
        question_de=(
            "Gibt es dazu einen Auftrag oder eine Auftragsnummer? "
            "Falls nicht, antworte mit 'keine'."
        ),
    ),
    ReportStep(
        key="strength_text",
        section=ReportSection.STRENGTHS,
        question="Are there notable strengths or positive points?",
        question_de=(
            "Gibt es aus deiner Sicht besondere St\u00e4rken " "oder positive Punkte?"
        ),
    ),
    ReportStep(
        key="weakness_text",
        section=ReportSection.WEAKNESSES,
        question="Are there risks, objections, or weaknesses to record?",
        question_de=(
            "Gibt es Risiken, Einw\u00e4nde oder Schw\u00e4chen, "
            "die festgehalten werden sollen?"
        ),
    ),
    ReportStep(
        key="ratings",
        section=ReportSection.RATINGS,
        question=(
            "Rate customer satisfaction, technical attractiveness, commercial "
            "attractiveness, and priority from 1 to 10."
        ),
        question_de=(
            "Wie bewertest du Zufriedenheit, technische Attraktivit\u00e4t, "
            "kaufm\u00e4nnische Attraktivit\u00e4t und Priorit\u00e4t "
            "jeweils von 1 bis 10?"
        ),
    ),
    ReportStep(
        key="reminders",
        section=ReportSection.REMINDERS,
        question="Should this create a follow-up reminder?",
        question_de=(
            "Soll daraus eine Wiedervorlage entstehen? Falls ja: f\u00fcr wen, "
            "bis wann und mit welcher Nachricht?"
        ),
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
            ("Kunde/Lead/Kontakt", _display_value(answers.get("visit_context"))),
            ("Besuchsart", _display_value(draft.visit_type)),
            ("Teilnehmer", _display_value(answers.get("participants"))),
            ("Besuchsdatum", _display_value(draft.visit_date)),
            ("Ziel/Thema", _display_value(answers.get("target_topic"))),
            ("Info", _display_value(draft.summary)),
            ("Vereinbarung", _display_value(draft.outcome)),
            ("Nächster Schritt", _display_value(draft.next_action)),
            (
                "Termin ab",
                _display_value(
                    answers.get("next_appointment_date"),
                    empty="Nicht relevant",
                ),
            ),
            (
                "Angebotsbezug",
                _display_value(answers.get("offer_reference"), empty="Nicht relevant"),
            ),
            (
                "Auftragsbezug",
                _display_value(answers.get("order_reference"), empty="Nicht relevant"),
            ),
            (
                "Stärke",
                _display_value(answers.get("strength_text"), empty="Nicht angegeben"),
            ),
            (
                "Schwäche",
                _display_value(answers.get("weakness_text"), empty="Nicht angegeben"),
            ),
            ("Bewertungen", _format_ratings(draft.ratings_json)),
            ("Wiedervorlagen", _format_task_preview(draft)),
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
        account_id=draft.account_id,
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

    mock_visit_report = save_mock_visit_report(
        final_report.id,
        _mock_visit_report_payload(draft, final_report),
    )
    _create_mock_reminders(draft, mock_visit_report)

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
) -> bool:
    _clear_ai_cache(draft)
    draft_data = _draft_data(draft)
    answers = dict(draft_data.get("answers", {}))
    answers[step.key] = message_text
    draft_data["answers"] = answers
    draft.draft_data_json = draft_data

    if step.key == "visit_context":
        _update_visit_context(draft, message_text)
    elif step.key == "visit_type":
        if not _update_visit_type(draft, message_text):
            _set_section_status(draft, step.section, SectionStatus.OPEN)
            return False
    elif step.key == "participants":
        _update_contacts(draft, message_text)
    elif step.key == "visit_date":
        visit_date = _parse_visit_date(message_text)
        if visit_date is None:
            _set_section_status(draft, step.section, SectionStatus.OPEN)
            return False
        draft.visit_date = visit_date
    elif step.key == "target_topic":
        draft.reason_code = _classify_reason(message_text)
    elif step.key == "info_text":
        draft.summary = message_text
    elif step.key == "agreement_text":
        draft.outcome = message_text
    elif step.key == "next_action":
        draft.next_action = message_text
        draft.follow_up_date = _parse_iso_date(message_text)
    elif step.key == "next_appointment_date":
        draft.follow_up_date = _parse_iso_date(message_text)
    elif step.key == "offer_reference":
        _update_offer_reference(draft, message_text)
    elif step.key == "order_reference":
        _update_order_reference(draft, message_text)
    elif step.key == "strength_text":
        draft_data["strength_text"] = message_text
        draft.draft_data_json = draft_data
    elif step.key == "weakness_text":
        draft_data["weakness_text"] = message_text
        draft.draft_data_json = draft_data
    elif step.key == "ratings":
        _update_ratings(draft, message_text)
        _set_section_status(
            draft, step.section, _section_status_for_answer(step, draft)
        )
        return _all_ratings_collected(draft)
    elif step.key == "reminders":
        _update_reminder_signal(draft, message_text)

    _set_section_status(draft, step.section, _section_status_for_answer(step, draft))
    return True


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

    sanitized_analysis = _sanitize_ai_analysis(analysis, message_text)
    _store_ai_analysis(draft, sanitized_analysis)
    return sanitized_analysis


def _ai_message_context(
    draft: ReportDraft,
    current_step: ReportStep,
) -> dict[str, Any]:
    return {
        "current_step": current_step.key,
        "current_question": _step_question(current_step, draft.session_language),
        "report_requirements": _report_requirements(draft),
        "missing_sections": list(draft.missing_sections_json),
        "missing_step_keys": _missing_step_keys(draft),
        "missing_rating_keys": _missing_rating_keys(draft),
        "known_answers": dict(_draft_data(draft).get("answers", {})),
        "ratings": dict(draft.ratings_json),
        "customer_context_type": draft.customer_context_type,
        "flow_hints": {
            "lead_can_skip_offer_and_order": True,
            "inside_sales_follow_up_can_update_next_action": True,
            "ratings_can_be_answered_together": True,
        },
        "allowed_section_update_keys": _allowed_update_keys(),
    }


def _sanitize_ai_analysis(
    analysis: AiMessageAnalysis,
    message_text: str,
) -> AiMessageAnalysis:
    allowed_keys = set(_allowed_update_keys())
    section_updates = {
        key: value.strip()
        for key, value in analysis.section_updates.items()
        if key in allowed_keys and isinstance(value, str) and value.strip()
    }
    target_sections = [
        section for section in analysis.target_sections if section in allowed_keys
    ]
    _add_explicit_visit_reason_clue(
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
        suggested_next_section=_clean_section_key(analysis.suggested_next_section),
        suggested_next_question=_clean_ai_text(analysis.suggested_next_question, 500),
    )


def _add_explicit_visit_reason_clue(
    section_updates: dict[str, str],
    target_sections: list[str],
    analysis: AiMessageAnalysis,
    message_text: str,
) -> None:
    if analysis.intent == UserIntent.CORRECTION:
        return
    if section_updates.get("target_topic"):
        return

    visit_reason = _extract_explicit_visit_reason(message_text)
    if visit_reason is None:
        return

    section_updates["target_topic"] = visit_reason
    if "target_topic" not in target_sections:
        target_sections.append("target_topic")


def _extract_explicit_visit_reason(message_text: str) -> str | None:
    patterns = (
        r"\b(?:über|ueber)\s+(?:eine[nmr]?|den|die|das)?\s*(?P<topic>.+?)\s+"
        r"(?:gesprochen|unterhalten|geredet)\b",
        r"\b(?:wegen|zum thema)\s+(?P<topic>[^.?!,;]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, message_text, re.IGNORECASE)
        if match is None:
            continue

        topic = _clean_explicit_visit_reason(match.group("topic"))
        if topic:
            return topic

    return None


def _clean_explicit_visit_reason(value: str) -> str | None:
    cleaned_value = re.sub(r"\s+", " ", value).strip(" .,!?:;")
    if not cleaned_value:
        return None

    return cleaned_value[:200]


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
        if _apply_step_answer(draft, current_step, current_answer):
            applied_steps.append(current_step)

    for step in _additional_ai_steps(
        current_step,
        analysis,
        completed_before_message,
    ):
        if _apply_step_answer(draft, step, analysis.section_updates[step.key]):
            applied_steps.append(step)

    _apply_flow_shortcuts(
        draft,
        current_step,
        message_text,
        completed_before_message,
        applied_steps,
    )

    return applied_steps


def _answer_for_step(
    step: ReportStep,
    message_text: str,
    analysis: AiMessageAnalysis | None,
) -> str | None:
    if step.key in {"offer_reference", "order_reference"} and _is_no_reference_message(
        message_text
    ):
        return "keiner"

    if analysis is None:
        return message_text

    suggested_value = analysis.section_updates.get(step.key)
    if not suggested_value:
        if analysis.intent == UserIntent.CORRECTION:
            return None
        return message_text

    return suggested_value


def _apply_flow_shortcuts(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    completed_before_message: set[str],
    applied_steps: list[ReportStep],
) -> None:
    _apply_lead_context_signal(draft, message_text)
    _apply_inside_sales_follow_up_signal(draft, current_step, message_text)
    _apply_no_offer_order_shortcut(
        draft,
        current_step,
        message_text,
        completed_before_message,
        applied_steps,
    )
    _apply_follow_up_shortcut(
        draft,
        current_step,
        message_text,
        completed_before_message,
        applied_steps,
    )


def _apply_lead_context_signal(draft: ReportDraft, message_text: str) -> None:
    if not _mentions_lead(message_text):
        return
    if draft.account_id is not None:
        return

    draft.customer_context_type = CustomerContextType.NEW_LEAD.value
    draft.validation_status = ValidationStatus.CONFIRMED_NEW.value


def _apply_inside_sales_follow_up_signal(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
) -> None:
    if not _mentions_inside_sales_follow_up(message_text):
        return

    draft.draft_data_json = {
        **_draft_data(draft),
        INSIDE_SALES_FOLLOW_UP_KEY: True,
    }


def _apply_no_offer_order_shortcut(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    completed_before_message: set[str],
    applied_steps: list[ReportStep],
) -> None:
    if current_step.key not in {"offer_reference", "order_reference"}:
        return
    if not _is_no_reference_message(message_text):
        return

    for step_key in ("offer_reference", "order_reference"):
        step = _step_by_key(step_key)
        if step.key in completed_before_message:
            continue
        if any(applied_step.key == step.key for applied_step in applied_steps):
            continue

        if _apply_step_answer(draft, step, "keiner"):
            applied_steps.append(step)


def _apply_follow_up_shortcut(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    completed_before_message: set[str],
    applied_steps: list[ReportStep],
) -> None:
    if current_step.key not in {"info_text", "agreement_text"}:
        return
    if current_step.key == "next_action":
        return
    if "next_action" in completed_before_message:
        return
    if any(applied_step.key == "next_action" for applied_step in applied_steps):
        return
    if not _looks_like_follow_up_action(message_text):
        return

    next_action_step = _step_by_key("next_action")
    if _step_index(next_action_step) <= _step_index(current_step):
        return

    if _apply_step_answer(draft, next_action_step, message_text):
        applied_steps.append(next_action_step)


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


def _report_requirements(draft: ReportDraft) -> list[dict[str, Any]]:
    completed_steps = set(_draft_data(draft).get("completed_steps", []))
    answers = dict(_draft_data(draft).get("answers", {}))
    return [
        {
            "key": step.key,
            "label": REQUIREMENT_LABELS[step.key],
            "status": _requirement_status(draft, step, completed_steps, answers),
            "required": _requirement_required(step),
            "current_value": _requirement_current_value(draft, step, answers),
            "question": _requirement_question(draft, step),
            "section": step.section.value,
        }
        for step in REPORT_STEPS
    ]


def _requirement_required(step: ReportStep) -> bool:
    return step.key not in {
        "next_appointment_date",
        "offer_reference",
        "order_reference",
        "strength_text",
        "weakness_text",
        "reminders",
    }


def _requirement_status(
    draft: ReportDraft,
    step: ReportStep,
    completed_steps: set[str],
    answers: dict[str, Any],
) -> str:
    if step.key == "ratings":
        if _all_ratings_collected(draft):
            return "completed"
        if draft.ratings_json:
            return "partially_completed"
        return "missing"

    if step.key in {
        "next_appointment_date",
        "offer_reference",
        "order_reference",
        "reminders",
    } and _is_none_answer(str(answers.get(step.key, ""))):
        return "not_applicable"

    if step.key in completed_steps:
        return "completed"

    if step.key in OPTIONAL_STEP_KEYS:
        return "missing"

    return "missing"


def _requirement_current_value(
    draft: ReportDraft,
    step: ReportStep,
    answers: dict[str, Any],
) -> Any:
    if step.key == "ratings":
        return dict(draft.ratings_json) if draft.ratings_json else None

    return answers.get(step.key)


def _requirement_question(draft: ReportDraft, step: ReportStep) -> str:
    if step.section == ReportSection.RATINGS:
        return _rating_question(draft)

    return _step_question(step, draft.session_language)


def _step_by_key(step_key: str) -> ReportStep:
    return next(step for step in REPORT_STEPS if step.key == step_key)


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
        (
            step
            for step in REPORT_STEPS
            if step.key not in completed_step_set and step.key not in OPTIONAL_STEP_KEYS
        ),
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
    elif next_step.section == ReportSection.RATINGS:
        message = _rating_question(draft)
    else:
        message = _suggested_question(next_step, analysis) or _step_question(
            next_step,
            draft.session_language,
        )

    draft.last_question = message
    return message


def _next_question_context(
    draft: ReportDraft,
    next_step: ReportStep,
) -> dict[str, Any]:
    return {
        "next_step": next_step.key,
        "fallback_question": _step_question(next_step, draft.session_language),
        "report_requirements": _report_requirements(draft),
        "missing_sections": list(draft.missing_sections_json),
        "missing_step_keys": _missing_step_keys(draft),
        "missing_rating_keys": _missing_rating_keys(draft),
        "known_answers": dict(_draft_data(draft).get("answers", {})),
        "ratings": dict(draft.ratings_json),
        "customer_context_type": draft.customer_context_type,
        "report_status": draft.report_status,
    }


def _review_ready_message(chat: Chat) -> str:
    return (
        "Alle Pflichtbereiche sind vollständig. "
        f"Bitte prüfe den Bericht unter /sales/reports/{chat.id}/review."
    )


def _step_question(step: ReportStep, session_language: str | None) -> str:
    if session_language == "de":
        return step.question_de

    return step.question


def _rating_question(draft: ReportDraft) -> str:
    missing_labels = _missing_rating_labels(draft)
    if len(missing_labels) == len(RATING_FIELDS):
        return (
            "Wie bewertest du Zufriedenheit, technische Attraktivität, "
            "kaufmännische Attraktivität und Priorität jeweils von 1 bis 10? "
            "Wenn etwas noch nicht bewertbar ist, sag das kurz dazu."
        )

    if len(missing_labels) == 1:
        return (
            "Eine Bewertung fehlt noch: "
            f"{missing_labels[0]}. Wie schätzt du das von 1 bis 10 ein?"
        )

    return (
        "Ein paar Bewertungen fehlen noch: "
        f"{', '.join(missing_labels)}. Kannst du sie kurz von 1 bis 10 einschätzen?"
    )


def _missing_rating_labels(draft: ReportDraft) -> list[str]:
    missing_keys = set(_missing_rating_keys(draft))
    return [
        label_de
        for rating_key, _label_en, label_de in RATING_FIELDS
        if rating_key in missing_keys
    ]


def _update_visit_context(draft: ReportDraft, message_text: str) -> None:
    normalized_text = message_text.lower()
    account_matches = search_accounts(message_text)
    draft.account = None
    draft.customer = None
    draft.lead = None
    draft.contact = None

    if _mentions_new(normalized_text) or "lead" in normalized_text:
        draft.customer_context_type = CustomerContextType.NEW_LEAD.value
        draft.validation_status = ValidationStatus.CONFIRMED_NEW.value
        return

    if len(account_matches) == 1:
        account = account_matches[0]
        draft.account = account
        draft.customer_context_type = _customer_context_type_for_account(account)
        draft.validation_status = ValidationStatus.MATCHED.value
        return

    draft.customer_context_type = CustomerContextType.UNCLEAR.value
    draft.validation_status = ValidationStatus.UNKNOWN.value


def _customer_context_type_for_account(account: Any) -> str:
    if account.account_type == AccountType.ADDRESS.value:
        return CustomerContextType.EXISTING_LEAD.value

    return CustomerContextType.EXISTING_CUSTOMER.value


def _update_visit_type(draft: ReportDraft, message_text: str) -> bool:
    visit_type = _parse_visit_type(message_text)
    if visit_type is None:
        return False

    draft.visit_type = visit_type
    return True


def _parse_visit_type(message_text: str) -> str | None:
    normalized_text = message_text.lower()
    if any(value in normalized_text for value in ("telefon", "phone", "call")):
        return VisitType.PHONE.value
    if any(
        value in normalized_text for value in ("virtuell", "video", "teams", "zoom")
    ):
        return VisitType.VIRTUAL.value
    if any(
        value in normalized_text
        for value in ("persön", "persoen", "personlich", "vor ort", "beim", "bei ")
    ):
        return VisitType.IN_PERSON.value
    if message_text in {visit_type.value for visit_type in VisitType}:
        return message_text

    return None


def _update_contacts(draft: ReportDraft, message_text: str) -> None:
    draft.contact = None
    account_id = draft.account_id or (draft.account.id if draft.account else None)
    if account_id is None:
        return

    contact_matches = find_contacts(account_id, message_text)
    if len(contact_matches) == 1:
        draft.contact = contact_matches[0]


def _update_offer_reference(draft: ReportDraft, message_text: str) -> None:
    draft.related_offer = None
    if _is_none_answer(message_text):
        draft.external_offer_reference = None
        return

    draft.external_offer_reference = message_text
    if draft.account_id is None:
        return

    offer_matches = find_offers(draft.account_id, message_text)
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
    if draft.account_id is None:
        return

    order_matches = find_orders(draft.account_id, message_text)
    if len(order_matches) == 1:
        draft.related_order = order_matches[0]


def _update_ratings(draft: ReportDraft, message_text: str) -> None:
    ratings = dict(draft.ratings_json)
    parsed_values = _parse_rating_values(message_text)
    is_not_assessable = _is_not_assessable_rating_answer(message_text)
    for index, (rating_key, _label_en, _label_de) in enumerate(RATING_FIELDS):
        value = parsed_values[index] if index < len(parsed_values) else None
        if value is None and not is_not_assessable:
            continue
        if value is None and rating_key in ratings:
            continue

        ratings[rating_key] = {
            "value": value,
            "reason": message_text,
            "not_assessable": value is None and is_not_assessable,
        }

    draft.ratings_json = ratings


def _update_reminder_signal(draft: ReportDraft, message_text: str) -> None:
    if _is_none_answer(message_text):
        return

    draft.draft_data_json = {
        **_draft_data(draft),
        INSIDE_SALES_FOLLOW_UP_KEY: True,
        "reminder_message": message_text,
    }


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


def _parse_rating_values(message_text: str) -> list[int]:
    return [
        int(match)
        for match in re.findall(r"\b(10|[1-9])\b", message_text)
        if 1 <= int(match) <= 10
    ]


def _is_not_assessable_rating_answer(message_text: str) -> bool:
    normalized_text = message_text.lower()
    return any(
        phrase in normalized_text
        for phrase in (
            "nicht bewertbar",
            "noch nicht bewertbar",
            "zu früh",
            "zu frueh",
            "too early",
            "not assessable",
            "kann ich nicht bewerten",
        )
    )


def _parse_iso_date(message_text: str) -> date | None:
    match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", message_text)
    if match is None:
        return None

    return date.fromisoformat(match.group(0))


def _parse_visit_date(message_text: str) -> date | None:
    parsed_date = _parse_iso_date(message_text)
    if parsed_date is not None:
        return parsed_date

    normalized_text = message_text.strip().lower()
    if normalized_text in {"heute", "today"}:
        return date.today()
    if normalized_text in {"gestern", "yesterday"}:
        return date.today() - timedelta(days=1)

    return None


def _section_status_for_answer(
    step: ReportStep,
    draft: ReportDraft,
) -> SectionStatus:
    if step.key in {
        "next_appointment_date",
        "offer_reference",
        "order_reference",
        "reminders",
    }:
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
    draft.missing_sections_json = _missing_sections_for_draft(draft)


def _missing_sections(section_statuses: dict[str, str]) -> list[str]:
    return [
        section
        for section, status in section_statuses.items()
        if status == SectionStatus.OPEN.value
        and section
        not in {
            ReportSection.FINAL_REPORT.value,
            ReportSection.USER_CONFIRMATION.value,
            *OPTIONAL_REPORT_SECTIONS,
        }
    ]


def _missing_sections_for_draft(draft: ReportDraft) -> list[str]:
    missing_sections = _missing_sections(draft.section_statuses_json)
    if ReportSection.RATINGS.value not in missing_sections:
        missing_sections.extend(_missing_rating_step_keys(draft))

    return missing_sections


def _missing_step_keys(draft: ReportDraft) -> list[str]:
    completed_steps = set(_draft_data(draft).get("completed_steps", []))
    return [
        step.key
        for step in REPORT_STEPS
        if step.key not in completed_steps and step.key not in OPTIONAL_STEP_KEYS
    ]


def _missing_rating_keys(draft: ReportDraft) -> list[str]:
    return [
        rating_key
        for rating_key, _label_en, _label_de in RATING_FIELDS
        if not _rating_is_handled(draft.ratings_json.get(rating_key))
    ]


def _missing_rating_step_keys(draft: ReportDraft) -> list[str]:
    if _all_ratings_collected(draft):
        return []

    return ["ratings"]


def _all_ratings_collected(draft: ReportDraft) -> bool:
    return all(
        _rating_is_handled(draft.ratings_json.get(rating_key))
        for rating_key, _label_en, _label_de in RATING_FIELDS
    )


def _rating_is_handled(rating: Any) -> bool:
    if not isinstance(rating, dict):
        return False

    value = rating.get("value")
    return isinstance(value, int) or rating.get("not_assessable") is True


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
        "reminders": _reminder_preview_titles(draft),
        "status": draft.report_status,
    }


def _build_final_report_text(draft: ReportDraft) -> str:
    answers = _draft_data(draft).get("answers", {})
    report_lines = [
        "Besuchsbericht",
        "",
        f"Kunde/Lead/Kontakt: {_display_value(answers.get('visit_context'))}",
        f"Besuchsart: {_display_value(draft.visit_type)}",
        f"Teilnehmer: {_display_value(answers.get('participants'))}",
        f"Besuchsdatum: {_display_value(draft.visit_date)}",
        f"Ziel/Thema: {_display_value(answers.get('target_topic'))}",
        "",
        f"Info: {draft.summary or 'Nicht angegeben'}",
        f"Vereinbarung: {draft.outcome or 'Nicht angegeben'}",
        f"Nächster Schritt: {draft.next_action or 'Nicht angegeben'}",
        f"Stärke: {_display_value(answers.get('strength_text'), 'Nicht angegeben')}",
        f"Schwäche: {_display_value(answers.get('weakness_text'), 'Nicht angegeben')}",
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
    reminder_titles = _reminder_preview_titles(draft)
    if not reminder_titles:
        return "Keine"

    return "; ".join(reminder_titles)


def _mock_visit_report_payload(
    draft: ReportDraft,
    final_report: FinalReport,
) -> dict[str, Any]:
    answers = dict(_draft_data(draft).get("answers", {}))
    account = draft.account
    representative = _default_field_sales_representative()
    responsible_user = _default_crm_user()
    ratings = dict(draft.ratings_json)
    return {
        "visit_type": draft.visit_type or VisitType.IN_PERSON.value,
        "visit_report_status": VisitReportStatus.CLOSED.value,
        "report_status": VisitReportStatus.CLOSED.value,
        "account_id": draft.account_id,
        "account_number": account.account_number if account else None,
        "account_type": account.account_type if account else AccountType.ADDRESS.value,
        "account_search_name": account.search_name if account else None,
        "contact_id": draft.contact_id,
        "contact_name": _draft_answer(draft, "participants"),
        "field_sales_representative_id": (
            representative.id if representative is not None else None
        ),
        "responsible_user_id": responsible_user.id if responsible_user else None,
        "visit_date": draft.visit_date,
        "target_topic": answers.get("target_topic") or final_report.summary,
        "info_text": draft.summary or final_report.summary,
        "agreement_text": draft.outcome or final_report.outcome or "Nicht angegeben",
        "strength_text": answers.get("strength_text"),
        "weakness_text": answers.get("weakness_text"),
        "customer_satisfaction_rating": _rating_value(
            ratings,
            "customer_satisfaction_rating",
        ),
        "technical_attractiveness_rating": _rating_value(
            ratings,
            "technical_attractiveness_rating",
        ),
        "commercial_attractiveness_rating": _rating_value(
            ratings,
            "commercial_attractiveness_rating",
        ),
        "priority_rating": _rating_value(ratings, "priority_rating"),
        "next_appointment_date": draft.follow_up_date,
        "offer_reference": answers.get("offer_reference"),
        "order_reference": answers.get("order_reference")
        or _draft_data(draft).get("order_reference_raw"),
    }


def _create_mock_reminders(
    draft: ReportDraft,
    mock_visit_report: MockVisitReport,
) -> list[MockReminder]:
    if not _draft_data(draft).get(INSIDE_SALES_FOLLOW_UP_KEY):
        return []

    owner = _default_crm_user()
    if owner is None:
        return []

    reminder = create_mock_reminder(
        mock_visit_report.visit_report_number,
        {
            "due_date": draft.follow_up_date,
            "owner_type": ReminderOwnerType.CRM_USER.value,
            "owner_id": owner.id,
            "created_by_user_id": draft.sales_user_id,
            "message": _reminder_message(draft),
        },
    )
    return [reminder]


def _default_crm_user() -> Any | None:
    users = list_crm_users()
    return users[0] if users else None


def _default_field_sales_representative() -> Any | None:
    representatives = list_field_sales_representatives()
    return representatives[0] if representatives else None


def _rating_value(ratings: dict[str, Any], rating_key: str) -> int | None:
    rating = ratings.get(rating_key)
    if not isinstance(rating, dict):
        return None

    value = rating.get("value")
    return value if isinstance(value, int) else None


def _reminder_message(draft: ReportDraft) -> str:
    return (
        _draft_data(draft).get("reminder_message")
        or draft.next_action
        or "Bitte Besuchsbericht prüfen und Folgeaktion übernehmen."
    )


def _reminder_preview_titles(draft: ReportDraft) -> list[str]:
    if not _draft_data(draft).get(INSIDE_SALES_FOLLOW_UP_KEY):
        return []

    message = _reminder_message(draft)
    due_date = (
        draft.follow_up_date.isoformat() if draft.follow_up_date else "ohne Datum"
    )
    return [f"Wiedervorlage Innendienst ({due_date}): {message}"]


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


def _is_no_reference_message(message_text: str) -> bool:
    normalized_text = message_text.strip().lower()
    if _is_none_answer(normalized_text):
        return True
    if normalized_text.startswith(("nee", "nein", "no ")):
        return True

    return _mentions_lead(message_text) and not _looks_like_reference(normalized_text)


def _looks_like_reference(normalized_text: str) -> bool:
    reference_pattern = r"\b(?:off|ang|angebot|auftrag|ord)[-_ ]?\d+\b"
    return bool(re.search(reference_pattern, normalized_text))


def _mentions_new(normalized_text: str) -> bool:
    return any(keyword in normalized_text for keyword in ("new", "neu", "unknown"))


def _mentions_lead(message_text: str) -> bool:
    return "lead" in message_text.lower()


def _mentions_inside_sales_follow_up(message_text: str) -> bool:
    normalized_text = message_text.lower()
    return "innendienst" in normalized_text and any(
        keyword in normalized_text for keyword in ("anrufen", "melden", "follow")
    )


def _looks_like_follow_up_action(message_text: str) -> bool:
    normalized_text = message_text.lower()
    return any(
        keyword in normalized_text
        for keyword in (
            "wiedervorlage",
            "melden",
            "anrufen",
            "nachfassen",
            "follow-up",
            "follow up",
            "in 2 wochen",
            "in zwei wochen",
            "nächste woche",
            "nächste woche",
        )
    )


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
