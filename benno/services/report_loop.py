"""Deterministic and AI-assisted visit report loop for Phase 6."""

from typing import Any

from benno.enums import (
    AccountType,
    CustomerContextType,
    MessageSender,
    MessageType,
    ReportSection,
    ReportStatus,
    SectionStatus,
    UserIntent,
)
from benno.extensions import db
from benno.models import (
    Chat,
    ChatMessage,
    FinalReport,
    ReportDraft,
    User,
    utc_now,
)
from benno.services.ai_provider import AiMessageAnalysis, AiProviderError, AiService
from benno.services.ai_registry import get_ai_service
from benno.services.mock_crm import CrmGateway, get_crm_gateway
from benno.services.observability import trace_report_decision, trace_report_turn
from benno.services.report_account_resolution import (
    apply_lead_context_signal,
    resolve_visit_context,
)
from benno.services.report_ai_context import (
    ai_error_code,
    ai_message_context,
    sanitize_ai_analysis,
    store_ai_analysis,
    store_ai_error,
)
from benno.services.report_review import (
    build_report_review,
    clear_ai_cache,
    final_report_text_for_draft,
)
from benno.services.report_shortcuts import (
    classify_reason,
    extract_strength_weakness_answers,
    is_no_reference_message,
    is_none_answer,
    is_not_assessable_rating_answer,
    looks_like_follow_up_action,
    looks_like_rating_answer,
    looks_like_reference,
    mentions_inside_sales_follow_up,
    mentions_lead,
    parse_labeled_rating_values,
    parse_rating_value,
    parse_rating_values,
    parse_visit_date,
    parse_visit_type,
)
from benno.services.report_state import (
    ACCOUNT_TYPE_OVERRIDE_KEY,
    INSIDE_SALES_FOLLOW_UP_KEY,
    REMINDER_SUPPRESSED_KEY,
    clear_crm_reference,
    crm_reference_value,
    draft_data,
    remove_draft_answer,
    set_draft_metadata,
    store_crm_reference,
)
from benno.services.report_steps import (
    RATING_FIELDS,
    REPORT_STEPS,
    REVIEW_STEP,
    ReportStep,
    all_ratings_collected,
    first_incomplete_step,
    initial_section_statuses,
    missing_sections,
    rating_question,
    refresh_missing_sections,
    set_section_status,
    step_by_key,
    step_index,
    step_question,
)
from benno.services.report_steps import (
    is_ready_for_review as draft_is_ready_for_review,
)
from benno.services.report_writeback import (
    build_mock_visit_report_payload,
    create_mock_reminders,
)

MUTABLE_REPORT_STATUSES = {
    ReportStatus.IN_PROGRESS.value,
    ReportStatus.READY_FOR_REVIEW.value,
}
EMPTY_CORRECTION_KEYS = {
    "next_appointment_date",
    "offer_reference",
    "order_reference",
    "strength_text",
    "weakness_text",
    "reminder_message",
}
__all__ = [
    "apply_report_correction",
    "apply_report_corrections",
    "build_report_review",
    "cancel_report",
    "confirm_report",
    "is_ready_for_review",
    "process_report_message",
    "process_report_message_with_ai",
    "process_report_turn",
    "start_report_chat",
]


def start_report_chat(sales_user: User) -> Chat:
    """Create a new report chat and initial draft."""
    initial_step = REPORT_STEPS[0]
    initial_question = step_question(initial_step, sales_user.preferred_language)
    initial_message = _initial_report_message(sales_user, initial_question)
    section_statuses = initial_section_statuses()

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
        missing_sections_json=missing_sections(section_statuses),
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
    return process_report_turn(chat, message_text, get_ai_service())


def process_report_message_with_ai(
    chat: Chat,
    message_text: str,
    ai_service: AiService | None,
    crm_gateway: CrmGateway | None = None,
) -> Chat:
    """Compatibility wrapper for tests and older service callers."""
    return process_report_turn(chat, message_text, ai_service, crm_gateway)


def process_report_turn(
    chat: Chat,
    message_text: str,
    ai_service: AiService | None,
    crm_gateway: CrmGateway | None = None,
) -> Chat:
    """Store a user answer and advance the assisted report state."""
    draft = _require_mutable_draft(chat)
    gateway = crm_gateway or get_crm_gateway()
    normalized_message = _normalize_message_text(message_text)
    _record_user_message(chat, message_text)

    current_step = _current_step(draft)
    if current_step is None:
        return _complete_report_turn(chat, _review_ready_message(chat))

    with trace_report_turn(chat, draft, current_step.key, normalized_message):
        analysis = _analyze_user_message(
            draft,
            current_step,
            normalized_message,
            ai_service,
        )
        applied_steps = _apply_report_answers(
            draft,
            current_step,
            normalized_message,
            analysis,
            gateway,
        )
        next_step = _advance_after_applied_steps(draft, applied_steps)
        next_question = _next_question(chat, next_step, analysis)
        trace_report_decision(
            draft,
            analysis,
            [step.key for step in applied_steps],
            next_step.key if next_step else None,
            next_question,
        )

    return _complete_report_turn(chat, next_question)


def _complete_report_turn(chat: Chat, assistant_reply: str) -> Chat:
    _record_assistant_reply(chat, assistant_reply)
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
    crm_gateway: CrmGateway | None = None,
) -> Chat:
    """Apply a targeted correction during final review."""
    return apply_report_corrections(chat, [(field_key, correction_text)], crm_gateway)


def apply_report_corrections(
    chat: Chat,
    corrections: list[tuple[str, str]],
    crm_gateway: CrmGateway | None = None,
) -> Chat:
    """Apply targeted review corrections as one atomic change."""
    draft = _require_draft(chat)
    _ensure_report_is_mutable(chat)
    gateway = crm_gateway or get_crm_gateway()
    if not draft_is_ready_for_review(draft):
        raise ValueError("Corrections are only available during final review.")

    normalized_corrections = _normalized_report_corrections(corrections)
    if not normalized_corrections:
        raise ValueError("No correction changes were provided.")

    try:
        with db.session.begin_nested():
            for field_key, correction_text in normalized_corrections:
                _apply_report_correction_value(
                    draft,
                    field_key,
                    correction_text,
                    gateway,
                )

            _record_saved_corrections(chat, normalized_corrections)

        db.session.commit()
    except ValueError:
        db.session.rollback()
        raise

    return chat


def _normalized_report_corrections(
    corrections: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    normalized_corrections = []
    for field_key, correction_text in corrections:
        clean_field_key = field_key.strip()
        clean_correction_text = correction_text.strip()
        if not clean_field_key:
            raise ValueError("Unknown correction field.")
        if not clean_correction_text and clean_field_key not in EMPTY_CORRECTION_KEYS:
            raise ValueError("Correction text must not be empty.")

        normalized_corrections.append((clean_field_key, clean_correction_text))

    return normalized_corrections


def _apply_report_correction_value(
    draft: ReportDraft,
    field_key: str,
    correction_text: str,
    crm_gateway: CrmGateway,
) -> None:
    if not correction_text:
        _apply_empty_report_correction(draft, field_key)
        return

    if _apply_special_report_correction(draft, field_key, correction_text):
        return

    correction_step = _correction_step(field_key)
    if not _apply_requirement_answer(
        draft,
        correction_step,
        correction_text,
        crm_gateway,
    ):
        raise ValueError(_invalid_correction_message(correction_step))


def _invalid_correction_message(correction_step: ReportStep) -> str:
    if correction_step.key == "visit_type":
        return (
            "Ungültige Besuchsart. Erlaubt sind Vor Ort, Virtuell " "oder Telefonisch."
        )
    if correction_step.key in {"visit_date", "next_appointment_date"}:
        return "Ungültiges Datum. Bitte gib ein gültiges Datum ein."

    return f"Ungültiger Wert für {correction_step.question_de}"


def _apply_empty_report_correction(
    draft: ReportDraft,
    field_key: str,
) -> None:
    if field_key not in EMPTY_CORRECTION_KEYS:
        raise ValueError("Correction text must not be empty.")

    clear_ai_cache(draft)
    if field_key == "next_appointment_date":
        _clear_next_appointment_correction(draft)
    elif field_key == "offer_reference":
        _clear_offer_reference_correction(draft)
    elif field_key == "order_reference":
        _clear_order_reference_correction(draft)
    elif field_key in {"strength_text", "weakness_text"}:
        _clear_optional_text_correction(draft, field_key)
    elif field_key == "reminder_message":
        _clear_reminder_correction(draft)


def _clear_next_appointment_correction(draft: ReportDraft) -> None:
    draft.follow_up_date = None
    _replace_requirement_answer(draft, "next_appointment_date", "keine")
    set_section_status(
        draft,
        ReportSection.NEXT_APPOINTMENT_DATE,
        SectionStatus.NOT_APPLICABLE,
    )


def _clear_offer_reference_correction(draft: ReportDraft) -> None:
    draft.related_offer_id = None
    draft.external_offer_reference = None
    clear_crm_reference(draft, "offer")
    _replace_requirement_answer(draft, "offer_reference", "keiner")
    set_section_status(
        draft, ReportSection.OFFER_REFERENCE, SectionStatus.NOT_APPLICABLE
    )


def _clear_order_reference_correction(draft: ReportDraft) -> None:
    draft.related_order_id = None
    clear_crm_reference(draft, "order")
    data = draft_data(draft)
    data["order_reference_raw"] = None
    draft.draft_data_json = data
    _replace_requirement_answer(draft, "order_reference", "keiner")
    set_section_status(
        draft, ReportSection.ORDER_REFERENCE, SectionStatus.NOT_APPLICABLE
    )


def _clear_optional_text_correction(draft: ReportDraft, field_key: str) -> None:
    data = draft_data(draft)
    data.pop(field_key, None)
    draft.draft_data_json = data
    remove_draft_answer(draft, field_key)
    if field_key == "strength_text":
        set_section_status(draft, ReportSection.STRENGTHS, SectionStatus.OPEN)
    else:
        set_section_status(draft, ReportSection.WEAKNESSES, SectionStatus.OPEN)


def _clear_reminder_correction(draft: ReportDraft) -> None:
    data = draft_data(draft)
    data.pop(INSIDE_SALES_FOLLOW_UP_KEY, None)
    data.pop("reminder_message", None)
    data[REMINDER_SUPPRESSED_KEY] = True
    draft.draft_data_json = data
    remove_draft_answer(draft, "reminders")
    set_section_status(draft, ReportSection.REMINDERS, SectionStatus.OPEN)


def _record_saved_corrections(
    chat: Chat,
    corrections: list[tuple[str, str]],
) -> None:
    draft = _require_draft(chat)
    refresh_missing_sections(draft)
    draft.report_status = ReportStatus.READY_FOR_REVIEW.value
    chat.status = ReportStatus.READY_FOR_REVIEW.value
    draft.last_question = "Korrektur gespeichert. Bitte prüfe den Bericht erneut."
    draft.draft_data_json = {
        **draft_data(draft),
        "current_step": REVIEW_STEP,
    }
    set_section_status(draft, ReportSection.FINAL_REPORT, SectionStatus.DETECTED)
    _add_correction_message(chat, "review", _correction_summary(corrections))
    _add_assistant_message(chat, draft.last_question)


def _correction_summary(corrections: list[tuple[str, str]]) -> str:
    return "; ".join(
        f"{field_key}: {correction_text or 'leer'}"
        for field_key, correction_text in corrections
    )


def _apply_special_report_correction(
    draft: ReportDraft,
    field_key: str,
    correction_text: str,
) -> bool:
    if field_key == "account_type":
        _apply_account_type_correction(draft, correction_text)
        return True
    if field_key == "reminder_message":
        _apply_reminder_correction(draft, correction_text)
        return True
    if field_key in {rating_key for rating_key, _label_en, _label_de in RATING_FIELDS}:
        _apply_single_rating_correction(draft, field_key, correction_text)
        return True

    return False


def _apply_account_type_correction(
    draft: ReportDraft,
    correction_text: str,
) -> None:
    account_type = correction_text.strip().upper()
    allowed_types = {account_type.value for account_type in AccountType}
    if account_type not in allowed_types:
        raise ValueError("Unknown AKL account type.")

    clear_ai_cache(draft)
    set_draft_metadata(draft, ACCOUNT_TYPE_OVERRIDE_KEY, account_type)
    if account_type == AccountType.ADDRESS.value:
        if draft.account_id is None:
            draft.customer_context_type = CustomerContextType.NEW_LEAD.value
        else:
            draft.customer_context_type = CustomerContextType.EXISTING_LEAD.value
    elif account_type == AccountType.CUSTOMER.value:
        draft.customer_context_type = CustomerContextType.EXISTING_CUSTOMER.value


def _apply_reminder_correction(
    draft: ReportDraft,
    correction_text: str,
) -> None:
    clear_ai_cache(draft)
    data = draft_data(draft)
    if is_none_answer(correction_text):
        data.pop(INSIDE_SALES_FOLLOW_UP_KEY, None)
        data.pop("reminder_message", None)
        data[REMINDER_SUPPRESSED_KEY] = True
        draft.draft_data_json = data
        return

    draft.draft_data_json = {
        **data,
        INSIDE_SALES_FOLLOW_UP_KEY: True,
        REMINDER_SUPPRESSED_KEY: False,
        "reminder_message": correction_text,
    }


def _apply_single_rating_correction(
    draft: ReportDraft,
    field_key: str,
    correction_text: str,
) -> None:
    value = parse_rating_value(correction_text)
    if value is None:
        raise ValueError("Rating correction must contain a value from 1 to 10.")

    clear_ai_cache(draft)
    ratings = dict(draft.ratings_json)
    ratings[field_key] = {
        "value": value,
        "reason": correction_text,
        "not_assessable": False,
    }
    draft.ratings_json = ratings


def confirm_report(
    chat: Chat,
    ai_service: AiService | None = None,
    crm_gateway: CrmGateway | None = None,
) -> FinalReport:
    """Create or return the confirmed final report for a completed chat."""
    draft = _require_draft(chat)
    gateway = crm_gateway or get_crm_gateway()
    if chat.final_report is not None:
        return chat.final_report

    if not draft_is_ready_for_review(draft):
        raise ValueError("Report is not ready for confirmation.")

    final_report = _create_final_report(chat, draft, ai_service)
    mock_visit_report = _write_confirmed_report_to_crm(draft, final_report, gateway)
    create_mock_reminders(draft, mock_visit_report, gateway)
    _mark_report_confirmed(chat, draft)
    _record_confirmation_message(chat)
    db.session.commit()

    return final_report


def _create_final_report(
    chat: Chat,
    draft: ReportDraft,
    ai_service: AiService | None,
) -> FinalReport:
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
        final_report_text=final_report_text_for_draft(draft, ai_service),
        status=ReportStatus.CONFIRMED.value,
        confirmed_at=utc_now(),
    )
    db.session.add(final_report)
    db.session.flush()
    return final_report


def _write_confirmed_report_to_crm(
    draft: ReportDraft,
    final_report: FinalReport,
    crm_gateway: CrmGateway,
) -> Any:
    mock_visit_report = crm_gateway.save_visit_report(
        final_report.id,
        build_mock_visit_report_payload(draft, final_report, crm_gateway),
    )
    return mock_visit_report


def _mark_report_confirmed(chat: Chat, draft: ReportDraft) -> None:
    chat.status = ReportStatus.CONFIRMED.value
    draft.report_status = ReportStatus.CONFIRMED.value
    set_section_status(draft, ReportSection.USER_CONFIRMATION, SectionStatus.CONFIRMED)


def _record_confirmation_message(chat: Chat) -> None:
    _add_assistant_message(chat, "The visit report has been confirmed and saved.")


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
    return chat.report_draft is not None and draft_is_ready_for_review(
        chat.report_draft
    )


def _require_draft(chat: Chat) -> ReportDraft:
    if chat.report_draft is None:
        raise ValueError("Report chat has no draft.")

    return chat.report_draft


def _require_mutable_draft(chat: Chat) -> ReportDraft:
    draft = _require_draft(chat)
    _ensure_report_is_mutable(chat)
    return draft


def _ensure_report_is_mutable(chat: Chat) -> None:
    if chat.status not in MUTABLE_REPORT_STATUSES:
        raise ValueError("This report can no longer be changed.")


def _normalize_message_text(message_text: str) -> str:
    normalized_message = message_text.strip()
    if not normalized_message:
        raise ValueError("Message text must not be empty.")

    return normalized_message


def _current_step(draft: ReportDraft) -> ReportStep | None:
    current_key = draft_data(draft).get("current_step")
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


def _apply_requirement_answer(
    draft: ReportDraft,
    requirement: ReportStep,
    answer_text: str,
    crm_gateway: CrmGateway,
) -> bool:
    clear_ai_cache(draft)
    _store_requirement_answer(draft, requirement, answer_text)

    if not _apply_requirement_specific_update(
        draft,
        requirement,
        answer_text,
        crm_gateway,
    ):
        _reject_requirement_answer(draft, requirement)
        return False

    _update_requirement_status(draft, requirement)
    return _requirement_is_complete(draft, requirement)


def _store_requirement_answer(
    draft: ReportDraft,
    requirement: ReportStep,
    answer_text: str,
) -> None:
    _replace_requirement_answer(draft, requirement.key, answer_text)


def _replace_requirement_answer(
    draft: ReportDraft,
    requirement_key: str,
    answer_text: str,
) -> None:
    data = draft_data(draft)
    answers = dict(data.get("answers", {}))
    answers[requirement_key] = answer_text
    data["answers"] = answers
    draft.draft_data_json = data


def _apply_requirement_specific_update(
    draft: ReportDraft,
    requirement: ReportStep,
    answer_text: str,
    crm_gateway: CrmGateway,
) -> bool:
    if requirement.key in _GATEWAY_REQUIREMENT_KEYS:
        _apply_gateway_requirement_answer(draft, requirement, answer_text, crm_gateway)
        return True
    if requirement.key == "visit_type":
        if not _apply_visit_type_answer(draft, answer_text):
            return False

        _replace_requirement_answer(draft, requirement.key, draft.visit_type)
        return True
    if requirement.key == "visit_date":
        if not _apply_visit_date_answer(draft, answer_text):
            return False

        _replace_requirement_answer(
            draft,
            requirement.key,
            draft.visit_date.isoformat(),
        )
        return True
    if requirement.key == "next_appointment_date":
        if not _apply_next_appointment_answer(draft, answer_text):
            return False

        _replace_requirement_answer(
            draft,
            requirement.key,
            _canonical_follow_up_date_answer(draft),
        )
        return True

    _apply_local_requirement_answer(draft, requirement, answer_text)
    return True


_GATEWAY_REQUIREMENT_KEYS = {
    "visit_context",
    "participants",
    "offer_reference",
    "order_reference",
}


def _apply_gateway_requirement_answer(
    draft: ReportDraft,
    requirement: ReportStep,
    answer_text: str,
    crm_gateway: CrmGateway,
) -> None:
    if requirement.key == "visit_context":
        _apply_visit_context_answer(draft, answer_text, crm_gateway)
    elif requirement.key == "participants":
        _apply_participants_answer(draft, answer_text, crm_gateway)
    elif requirement.key == "offer_reference":
        _apply_offer_reference_answer(draft, answer_text, crm_gateway)
    elif requirement.key == "order_reference":
        _apply_order_reference_answer(draft, answer_text, crm_gateway)


def _apply_local_requirement_answer(
    draft: ReportDraft,
    requirement: ReportStep,
    answer_text: str,
) -> None:
    if requirement.key == "target_topic":
        _apply_target_topic_answer(draft, answer_text)
    elif requirement.key == "info_text":
        _apply_info_answer(draft, answer_text)
    elif requirement.key == "agreement_text":
        _apply_agreement_answer(draft, answer_text)
    elif requirement.key == "next_action":
        _apply_next_action_answer(draft, answer_text)
    elif requirement.key == "strength_text":
        _store_draft_text_value(draft, "strength_text", answer_text)
    elif requirement.key == "weakness_text":
        _store_draft_text_value(draft, "weakness_text", answer_text)
    elif requirement.key == "ratings":
        _apply_rating_answers(draft, answer_text)
    elif requirement.key == "reminders":
        _apply_reminder_answer(draft, answer_text)


def _apply_visit_date_answer(draft: ReportDraft, answer_text: str) -> bool:
    visit_date = parse_visit_date(answer_text)
    if visit_date is None:
        return False

    draft.visit_date = visit_date
    return True


def _apply_next_appointment_answer(draft: ReportDraft, answer_text: str) -> bool:
    follow_up_date = parse_visit_date(answer_text)
    if follow_up_date is None and not is_none_answer(answer_text):
        return False

    draft.follow_up_date = follow_up_date
    return True


def _canonical_follow_up_date_answer(draft: ReportDraft) -> str:
    if draft.follow_up_date is None:
        return "keine"

    return draft.follow_up_date.isoformat()


def _reject_requirement_answer(draft: ReportDraft, requirement: ReportStep) -> None:
    remove_draft_answer(draft, requirement.key)
    set_section_status(draft, requirement.section, SectionStatus.OPEN)


def _update_requirement_status(draft: ReportDraft, requirement: ReportStep) -> None:
    set_section_status(
        draft,
        requirement.section,
        _section_status_for_answer(requirement, draft),
    )


def _requirement_is_complete(draft: ReportDraft, requirement: ReportStep) -> bool:
    if requirement.key == "ratings":
        return all_ratings_collected(draft)

    return True


def _store_draft_text_value(draft: ReportDraft, key: str, value: str) -> None:
    data = draft_data(draft)
    data[key] = value
    draft.draft_data_json = data


def _analyze_user_message(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    ai_service: AiService | None,
) -> AiMessageAnalysis | None:
    if ai_service is None:
        return None

    context = ai_message_context(draft, current_step)
    try:
        analysis = ai_service.analyze_report_message(context, message_text)
    except AiProviderError as error:
        store_ai_error(draft, ai_error_code(error))
        return None

    if analysis is None:
        return None

    sanitized_analysis = sanitize_ai_analysis(analysis, message_text)
    store_ai_analysis(draft, sanitized_analysis)
    return sanitized_analysis


def _apply_report_answers(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    analysis: AiMessageAnalysis | None,
    crm_gateway: CrmGateway,
) -> list[ReportStep]:
    completed_before_message = set(draft_data(draft).get("completed_steps", []))
    applied_steps = []
    _apply_current_requirement_answer(
        draft,
        current_step,
        message_text,
        analysis,
        applied_steps,
        crm_gateway,
    )
    _apply_ai_requirement_updates(
        draft,
        current_step,
        analysis,
        completed_before_message,
        applied_steps,
        crm_gateway,
    )
    _apply_rule_based_updates(
        draft,
        current_step,
        message_text,
        completed_before_message,
        applied_steps,
        crm_gateway,
    )

    return applied_steps


def _apply_current_requirement_answer(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    analysis: AiMessageAnalysis | None,
    applied_steps: list[ReportStep],
    crm_gateway: CrmGateway,
) -> None:
    current_answer = _answer_for_requirement(current_step, message_text, analysis)
    if current_answer is None:
        return

    if _apply_requirement_answer(draft, current_step, current_answer, crm_gateway):
        applied_steps.append(current_step)


def _apply_ai_requirement_updates(
    draft: ReportDraft,
    current_step: ReportStep,
    analysis: AiMessageAnalysis | None,
    completed_before_message: set[str],
    applied_steps: list[ReportStep],
    crm_gateway: CrmGateway,
) -> None:
    if analysis is None:
        return

    for requirement in _additional_ai_requirements(
        current_step,
        analysis,
        completed_before_message,
    ):
        if _apply_requirement_answer(
            draft,
            requirement,
            analysis.section_updates[requirement.key],
            crm_gateway,
        ):
            applied_steps.append(requirement)


def _answer_for_requirement(
    requirement: ReportStep,
    message_text: str,
    analysis: AiMessageAnalysis | None,
) -> str | None:
    if requirement.key in {
        "offer_reference",
        "order_reference",
    } and is_no_reference_message(message_text):
        return "keiner"

    if analysis is None:
        return message_text

    suggested_value = analysis.section_updates.get(requirement.key)
    if not suggested_value:
        if analysis.intent == UserIntent.CORRECTION:
            return None
        return message_text

    return suggested_value


def _apply_rule_based_updates(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    completed_before_message: set[str],
    applied_steps: list[ReportStep],
    crm_gateway: CrmGateway,
) -> None:
    _apply_lead_context_signal(draft, message_text)
    _apply_inside_sales_follow_up_signal(draft, current_step, message_text)
    for hint_handler in _rule_based_hint_handlers():
        hint_handler(
            draft,
            current_step,
            message_text,
            completed_before_message,
            applied_steps,
            crm_gateway,
        )


def _rule_based_hint_handlers() -> tuple[Any, ...]:
    return (
        _apply_visit_type_hint,
        _apply_no_reference_hint,
        _apply_document_reference_hint,
        _apply_next_appointment_hint,
        _apply_next_action_hint,
        _apply_strength_weakness_hint,
        _apply_rating_hint,
    )


def _apply_lead_context_signal(draft: ReportDraft, message_text: str) -> None:
    apply_lead_context_signal(draft, message_text)


def _apply_inside_sales_follow_up_signal(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
) -> None:
    if not mentions_inside_sales_follow_up(message_text):
        return

    draft.draft_data_json = {
        **draft_data(draft),
        INSIDE_SALES_FOLLOW_UP_KEY: True,
        REMINDER_SUPPRESSED_KEY: False,
    }


def _apply_visit_type_hint(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    completed_before_message: set[str],
    applied_steps: list[ReportStep],
    crm_gateway: CrmGateway,
) -> None:
    if "visit_type" in completed_before_message:
        return
    if any(applied_step.key == "visit_type" for applied_step in applied_steps):
        return
    if parse_visit_type(message_text) is None:
        return

    visit_type_step = step_by_key("visit_type")
    if step_index(visit_type_step) < step_index(current_step):
        return
    if _apply_requirement_answer(draft, visit_type_step, message_text, crm_gateway):
        applied_steps.append(visit_type_step)


def _apply_no_reference_hint(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    completed_before_message: set[str],
    applied_steps: list[ReportStep],
    crm_gateway: CrmGateway,
) -> None:
    if not _should_apply_no_reference_hint(current_step, message_text):
        return

    for step_key in ("offer_reference", "order_reference"):
        step = step_by_key(step_key)
        if step.key in completed_before_message:
            continue
        if any(applied_step.key == step.key for applied_step in applied_steps):
            continue

        if _apply_requirement_answer(draft, step, "keiner", crm_gateway):
            applied_steps.append(step)


def _should_apply_no_reference_hint(
    current_step: ReportStep,
    message_text: str,
) -> bool:
    if not is_no_reference_message(message_text):
        return False
    if current_step.key in {"offer_reference", "order_reference"}:
        return True

    return mentions_lead(message_text) or _mentions_offer_or_order_topic(message_text)


def _mentions_offer_or_order_topic(message_text: str) -> bool:
    normalized_text = message_text.lower()
    return any(
        keyword in normalized_text
        for keyword in ("angebot", "angebots", "auftrag", "auftrags", "offer", "order")
    )


def _apply_document_reference_hint(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    completed_before_message: set[str],
    applied_steps: list[ReportStep],
    crm_gateway: CrmGateway,
) -> None:
    for step_key, detector in (
        ("offer_reference", _looks_like_offer_reference),
        ("order_reference", _looks_like_order_reference),
    ):
        if not detector(message_text):
            continue

        _apply_optional_requirement_hint(
            draft,
            step_key,
            message_text,
            completed_before_message,
            applied_steps,
            crm_gateway,
        )


def _looks_like_offer_reference(message_text: str) -> bool:
    normalized_text = message_text.lower()
    if is_no_reference_message(message_text):
        return False

    return looks_like_reference(normalized_text) and any(
        keyword in normalized_text for keyword in ("off", "ang", "angebot", "offer")
    )


def _looks_like_order_reference(message_text: str) -> bool:
    normalized_text = message_text.lower()
    if is_no_reference_message(message_text):
        return False

    return looks_like_reference(normalized_text) and any(
        keyword in normalized_text for keyword in ("ord", "auftrag", "order")
    )


def _apply_next_appointment_hint(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    completed_before_message: set[str],
    applied_steps: list[ReportStep],
    crm_gateway: CrmGateway,
) -> None:
    if not _looks_like_next_appointment_answer(current_step, message_text):
        return

    _apply_optional_requirement_hint(
        draft,
        "next_appointment_date",
        message_text,
        completed_before_message,
        applied_steps,
        crm_gateway,
    )


def _looks_like_next_appointment_answer(
    current_step: ReportStep,
    message_text: str,
) -> bool:
    if current_step.key == "next_appointment_date":
        return parse_visit_date(message_text) is not None or is_none_answer(
            message_text
        )
    if step_index(current_step) < step_index(step_by_key("next_action")):
        return False

    return parse_visit_date(message_text) is not None and looks_like_follow_up_action(
        message_text
    )


def _apply_optional_requirement_hint(
    draft: ReportDraft,
    step_key: str,
    answer_text: str,
    completed_before_message: set[str],
    applied_steps: list[ReportStep],
    crm_gateway: CrmGateway,
) -> None:
    step = step_by_key(step_key)
    if step.key in completed_before_message:
        return
    if any(applied_step.key == step.key for applied_step in applied_steps):
        return

    if _apply_requirement_answer(draft, step, answer_text, crm_gateway):
        applied_steps.append(step)


def _apply_next_action_hint(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    completed_before_message: set[str],
    applied_steps: list[ReportStep],
    crm_gateway: CrmGateway,
) -> None:
    if current_step.key not in {"info_text", "agreement_text"}:
        return
    if "next_action" in completed_before_message:
        return
    if any(applied_step.key == "next_action" for applied_step in applied_steps):
        return
    if not looks_like_follow_up_action(message_text):
        return

    next_action_step = step_by_key("next_action")
    if step_index(next_action_step) <= step_index(current_step):
        return

    if _apply_requirement_answer(draft, next_action_step, message_text, crm_gateway):
        applied_steps.append(next_action_step)


def _apply_strength_weakness_hint(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    completed_before_message: set[str],
    applied_steps: list[ReportStep],
    crm_gateway: CrmGateway,
) -> None:
    extracted_answers = extract_strength_weakness_answers(message_text)
    if not extracted_answers:
        return

    existing_answers = dict(draft_data(draft).get("answers", {}))
    for step_key in ("strength_text", "weakness_text"):
        if step_key not in extracted_answers:
            continue
        if step_key in completed_before_message or existing_answers.get(step_key):
            continue
        if any(applied_step.key == step_key for applied_step in applied_steps):
            continue

        step = step_by_key(step_key)
        if _apply_requirement_answer(
            draft,
            step,
            extracted_answers[step_key],
            crm_gateway,
        ):
            applied_steps.append(step)


def _apply_rating_hint(
    draft: ReportDraft,
    current_step: ReportStep,
    message_text: str,
    completed_before_message: set[str],
    applied_steps: list[ReportStep],
    crm_gateway: CrmGateway,
) -> None:
    if "ratings" in completed_before_message:
        return
    if any(applied_step.key == "ratings" for applied_step in applied_steps):
        return
    if not looks_like_rating_answer(message_text):
        return

    rating_step = step_by_key("ratings")
    if step_index(rating_step) < step_index(current_step):
        return
    if _apply_requirement_answer(draft, rating_step, message_text, crm_gateway):
        applied_steps.append(rating_step)


def _additional_ai_requirements(
    current_step: ReportStep,
    analysis: AiMessageAnalysis | None,
    completed_before_message: set[str],
) -> list[ReportStep]:
    if analysis is None:
        return []

    current_index = step_index(current_step)
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
    requirement: ReportStep,
    current_index: int,
    analysis: AiMessageAnalysis,
    completed_before_message: set[str],
) -> bool:
    if analysis.intent == UserIntent.CORRECTION and _analysis_targets_requirement(
        analysis,
        requirement,
    ):
        return True

    if requirement.key in completed_before_message:
        return False

    return step_index(requirement) > current_index


def _analysis_targets_requirement(
    analysis: AiMessageAnalysis,
    requirement: ReportStep,
) -> bool:
    return requirement.key in analysis.target_sections or requirement.section.value in (
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


def _advance_after_applied_steps(
    draft: ReportDraft,
    applied_steps: list[ReportStep],
) -> ReportStep | None:
    data = draft_data(draft)
    completed_steps = list(data.get("completed_steps", []))
    for step in applied_steps:
        if step.key not in completed_steps:
            completed_steps.append(step.key)

    next_step = first_incomplete_step(completed_steps)
    data["completed_steps"] = completed_steps
    data["current_step"] = next_step.key if next_step else REVIEW_STEP
    draft.draft_data_json = data

    refresh_missing_sections(draft)
    if next_step is None:
        draft.report_status = ReportStatus.READY_FOR_REVIEW.value
        draft.chat.status = ReportStatus.READY_FOR_REVIEW.value
        set_section_status(draft, ReportSection.FINAL_REPORT, SectionStatus.DETECTED)

    return next_step


def _next_question(
    chat: Chat,
    next_step: ReportStep | None,
    analysis: AiMessageAnalysis | None,
) -> str:
    draft = _require_draft(chat)
    if next_step is None:
        message = _review_ready_message(chat)
    elif next_step.section == ReportSection.RATINGS:
        message = rating_question(draft)
    else:
        message = _suggested_question(next_step, analysis) or step_question(
            next_step,
            draft.session_language,
        )

    draft.last_question = message
    return message


def _review_ready_message(chat: Chat) -> str:
    return (
        "Alle Pflichtbereiche sind vollständig. "
        'Bitte prüfe den Bericht über den Button "Bericht prüfen" '
        "im Schreibzurück-Bereich."
    )


def _apply_visit_context_answer(
    draft: ReportDraft,
    message_text: str,
    crm_gateway: CrmGateway,
) -> None:
    resolve_visit_context(draft, message_text, crm_gateway)


def _apply_visit_type_answer(draft: ReportDraft, message_text: str) -> bool:
    visit_type = parse_visit_type(message_text)
    if visit_type is None:
        return False

    draft.visit_type = visit_type
    return True


def _apply_participants_answer(
    draft: ReportDraft,
    message_text: str,
    crm_gateway: CrmGateway,
) -> None:
    draft.contact_id = None
    clear_crm_reference(draft, "contact")
    account_id = draft.account_id or crm_reference_value(draft, "account", "id")
    if account_id is None:
        return

    contact_matches = crm_gateway.find_contacts(account_id, message_text)
    if len(contact_matches) == 1:
        contact = contact_matches[0]
        draft.contact_id = contact.id
        store_crm_reference(draft, "contact", contact)


def _apply_target_topic_answer(draft: ReportDraft, answer_text: str) -> None:
    draft.reason_code = classify_reason(answer_text)


def _apply_info_answer(draft: ReportDraft, answer_text: str) -> None:
    draft.summary = answer_text


def _apply_agreement_answer(draft: ReportDraft, answer_text: str) -> None:
    draft.outcome = answer_text


def _apply_next_action_answer(draft: ReportDraft, answer_text: str) -> None:
    draft.next_action = answer_text
    draft.follow_up_date = parse_visit_date(answer_text)
    if mentions_inside_sales_follow_up(answer_text):
        draft.draft_data_json = {
            **draft_data(draft),
            INSIDE_SALES_FOLLOW_UP_KEY: True,
            REMINDER_SUPPRESSED_KEY: False,
            "reminder_message": answer_text,
        }


def _apply_offer_reference_answer(
    draft: ReportDraft,
    message_text: str,
    crm_gateway: CrmGateway,
) -> None:
    draft.related_offer_id = None
    clear_crm_reference(draft, "offer")
    if is_none_answer(message_text):
        draft.external_offer_reference = None
        return

    draft.external_offer_reference = message_text
    account_id = draft.account_id or crm_reference_value(draft, "account", "id")
    if account_id is None:
        return

    offer_matches = crm_gateway.find_offers(account_id, message_text)
    if len(offer_matches) == 1:
        offer = offer_matches[0]
        draft.related_offer_id = offer.id
        store_crm_reference(draft, "offer", offer)


def _apply_order_reference_answer(
    draft: ReportDraft,
    message_text: str,
    crm_gateway: CrmGateway,
) -> None:
    draft.related_order_id = None
    clear_crm_reference(draft, "order")
    if is_none_answer(message_text):
        draft.draft_data_json = {
            **draft_data(draft),
            "order_reference_raw": None,
        }
        return

    draft.draft_data_json = {
        **draft_data(draft),
        "order_reference_raw": message_text,
    }
    account_id = draft.account_id or crm_reference_value(draft, "account", "id")
    if account_id is None:
        return

    order_matches = crm_gateway.find_orders(account_id, message_text)
    if len(order_matches) == 1:
        order = order_matches[0]
        draft.related_order_id = order.id
        store_crm_reference(draft, "order", order)


def _apply_rating_answers(draft: ReportDraft, message_text: str) -> None:
    ratings = dict(draft.ratings_json)
    is_not_assessable = is_not_assessable_rating_answer(message_text)
    labeled_values = {}
    parsed_values = []
    if not is_not_assessable:
        labeled_values = parse_labeled_rating_values(message_text)
        parsed_values = parse_rating_values(message_text)
    for index, (rating_key, _label_en, _label_de) in enumerate(RATING_FIELDS):
        value = labeled_values.get(rating_key)
        if value is None and not labeled_values:
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


def _apply_reminder_answer(draft: ReportDraft, message_text: str) -> None:
    if is_none_answer(message_text):
        return

    draft.draft_data_json = {
        **draft_data(draft),
        INSIDE_SALES_FOLLOW_UP_KEY: True,
        REMINDER_SUPPRESSED_KEY: False,
        "reminder_message": message_text,
    }


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
        answer = draft_data(draft).get("answers", {}).get(step.key, "")
        if is_none_answer(answer):
            return SectionStatus.NOT_APPLICABLE

    if step.section == ReportSection.RATINGS and not all_ratings_collected(draft):
        return SectionStatus.DETECTED

    return SectionStatus.CONFIRMED


def _add_user_message(chat: Chat, message_text: str) -> None:
    _add_message(chat, MessageSender.USER, message_text, MessageType.FREE_INPUT)


def _record_user_message(chat: Chat, message_text: str) -> None:
    _add_user_message(chat, message_text)


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


def _record_assistant_reply(chat: Chat, message_text: str) -> None:
    _add_assistant_message(chat, message_text)


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
