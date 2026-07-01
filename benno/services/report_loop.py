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
from benno.services.mock_crm import (
    find_contacts,
    find_customers,
    find_leads,
    find_offers,
    find_orders,
)

REVIEW_STEP = "review"
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


RATING_FIELDS = (
    ("sales_opportunity", "sales opportunity"),
    ("meeting_mood", "meeting mood"),
    ("priority", "priority"),
    ("closing_probability", "closing probability"),
    ("need_for_action", "need for action"),
    ("customer_satisfaction", "customer satisfaction"),
)
BASE_CORRECTION_FIELDS = (
    ("customer_context", "Customer or Lead"),
    ("contacts", "Contacts"),
    ("visit_reason", "Visit Reason"),
    ("summary", "Summary"),
    ("outcome", "Outcome"),
    ("next_action", "Next Action"),
    ("offer_reference", "Offer Reference"),
    ("order_reference", "Order Reference"),
)
CORRECTION_FIELDS = BASE_CORRECTION_FIELDS + tuple(
    (f"rating_{rating_key}", f"Rating: {label}") for rating_key, label in RATING_FIELDS
)

REPORT_STEPS = (
    ReportStep(
        key="customer_context",
        section=ReportSection.CUSTOMER_CONTEXT,
        question=(
            "Which customer or lead was this visit about? "
            "Mention if this is a new lead."
        ),
    ),
    ReportStep(
        key="contacts",
        section=ReportSection.CONTACTS,
        question="Who participated in the meeting?",
    ),
    ReportStep(
        key="visit_reason",
        section=ReportSection.VISIT_REASON,
        question="What was the main reason for the visit?",
    ),
    ReportStep(
        key="summary",
        section=ReportSection.SUMMARY,
        question="Please summarize the key discussion points.",
    ),
    ReportStep(
        key="outcome",
        section=ReportSection.OUTCOME,
        question="What was agreed or decided?",
    ),
    ReportStep(
        key="next_action",
        section=ReportSection.NEXT_ACTION,
        question="What is the next action or follow-up?",
    ),
    ReportStep(
        key="offer_reference",
        section=ReportSection.OFFER_REFERENCE,
        question="Is there an offer reference? If not, answer 'none'.",
    ),
    ReportStep(
        key="order_reference",
        section=ReportSection.ORDER_REFERENCE,
        question="Is there an order reference? If not, answer 'none'.",
    ),
    *(
        ReportStep(
            key=f"rating_{rating_key}",
            section=ReportSection.RATINGS,
            question=f"Rate the {label} from 1 to 10 and add a short reason.",
        )
        for rating_key, label in RATING_FIELDS
    ),
)


def start_report_chat(sales_user: User) -> Chat:
    """Create a new report chat and initial draft."""
    initial_step = REPORT_STEPS[0]
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
        last_question=initial_step.question,
    )

    db.session.add_all([chat, draft])
    db.session.flush()
    _add_assistant_message(chat, initial_step.question)
    db.session.commit()

    return chat


def process_report_message(chat: Chat, message_text: str) -> Chat:
    """Store a user answer and advance the deterministic report state."""
    draft = _require_draft(chat)
    _ensure_report_is_mutable(chat)
    normalized_message = message_text.strip()
    if not normalized_message:
        raise ValueError("Message text must not be empty.")

    _add_user_message(chat, normalized_message)

    current_step = _current_step(draft)
    if current_step is None:
        _add_assistant_message(chat, _review_ready_message(chat))
        db.session.commit()
        return chat

    _apply_step_answer(draft, current_step, normalized_message)
    next_step = _advance_step(draft, current_step)
    next_question = _next_question(chat, next_step)
    _add_assistant_message(chat, next_question)
    db.session.commit()

    return chat


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
    draft.last_question = "Correction saved. Please review the report again."
    draft.draft_data_json = {
        **_draft_data(draft),
        "current_step": REVIEW_STEP,
    }
    _set_section_status(draft, ReportSection.FINAL_REPORT, SectionStatus.DETECTED)
    _add_assistant_message(chat, draft.last_question)
    db.session.commit()

    return chat


def build_report_review(draft: ReportDraft) -> dict[str, Any]:
    """Build a human-readable review from a report draft."""
    draft_data = _draft_data(draft)
    answers = draft_data.get("answers", {})

    return {
        "sections": [
            ("Customer or Lead", _display_value(answers.get("customer_context"))),
            ("Contacts", _display_value(answers.get("contacts"))),
            ("Visit Reason", _display_value(answers.get("visit_reason"))),
            ("Summary", _display_value(draft.summary)),
            ("Outcome", _display_value(draft.outcome)),
            ("Next Action", _display_value(draft.next_action)),
            (
                "Offer Reference",
                _display_value(answers.get("offer_reference"), empty="Not relevant"),
            ),
            (
                "Order Reference",
                _display_value(answers.get("order_reference"), empty="Not relevant"),
            ),
            ("Ratings", _format_ratings(draft.ratings_json)),
            ("Inside Sales Tasks", _format_task_preview(draft)),
        ],
        "final_report_text": _build_final_report_text(draft),
        "correction_fields": CORRECTION_FIELDS,
        "status": draft.report_status,
    }


def confirm_report(chat: Chat) -> FinalReport:
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
        final_report_text=_build_final_report_text(draft),
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


def _advance_step(draft: ReportDraft, current_step: ReportStep) -> ReportStep | None:
    draft_data = _draft_data(draft)
    completed_steps = list(draft_data.get("completed_steps", []))
    if current_step.key not in completed_steps:
        completed_steps.append(current_step.key)

    next_step = _step_after(current_step)
    draft_data["completed_steps"] = completed_steps
    draft_data["current_step"] = next_step.key if next_step else REVIEW_STEP
    draft.draft_data_json = draft_data

    _refresh_missing_sections(draft)
    if next_step is None:
        draft.report_status = ReportStatus.READY_FOR_REVIEW.value
        draft.chat.status = ReportStatus.READY_FOR_REVIEW.value
        _set_section_status(draft, ReportSection.FINAL_REPORT, SectionStatus.DETECTED)

    return next_step


def _step_after(current_step: ReportStep) -> ReportStep | None:
    step_keys = [step.key for step in REPORT_STEPS]
    next_index = step_keys.index(current_step.key) + 1
    if next_index >= len(REPORT_STEPS):
        return None

    return REPORT_STEPS[next_index]


def _next_question(chat: Chat, next_step: ReportStep | None) -> str:
    draft = _require_draft(chat)
    if next_step is None:
        message = _review_ready_message(chat)
    else:
        message = next_step.question

    draft.last_question = message
    return message


def _review_ready_message(chat: Chat) -> str:
    return (
        "All required sections are complete. "
        f"Please review the report at /sales/reports/{chat.id}/review."
    )


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
    return all(rating_key in draft.ratings_json for rating_key, _label in RATING_FIELDS)


def _is_ready_for_review(draft: ReportDraft) -> bool:
    return (
        draft.report_status == ReportStatus.READY_FOR_REVIEW.value
        and draft.missing_sections_json == []
    )


def _build_final_report_text(draft: ReportDraft) -> str:
    answers = _draft_data(draft).get("answers", {})
    report_lines = [
        "Visit Report",
        "",
        f"Customer/Lead: {_display_value(answers.get('customer_context'))}",
        f"Contacts: {_display_value(answers.get('contacts'))}",
        f"Visit Reason: {_display_value(answers.get('visit_reason'))}",
        "",
        f"Summary: {draft.summary or 'Not provided'}",
        f"Outcome: {draft.outcome or 'Not provided'}",
        f"Next Action: {draft.next_action or 'Not provided'}",
        "",
        f"Ratings: {_format_ratings(draft.ratings_json)}",
    ]
    return "\n".join(report_lines)


def _format_ratings(ratings: dict[str, Any]) -> str:
    if not ratings:
        return "Not provided"

    parts = []
    for rating_key, label in RATING_FIELDS:
        rating = ratings.get(rating_key)
        if rating is None:
            continue
        value = rating.get("value") or "not rated"
        reason = rating.get("reason") or "No reason provided"
        parts.append(f"{label}: {value}/10 ({reason})")

    return "; ".join(parts) if parts else "Not provided"


def _format_task_preview(draft: ReportDraft) -> str:
    task_titles = _task_preview_titles(draft)
    if not task_titles:
        return "None"

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
