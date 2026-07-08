"""Writeback mapping for eNVenta-shaped mock visit reports."""

from typing import Any

from benno.enums import AccountType, ReminderOwnerType, VisitReportStatus, VisitType
from benno.models import FinalReport, ReportDraft
from benno.services.mock_crm import CrmGateway
from benno.services.report_review import reminder_message
from benno.services.report_state import (
    INSIDE_SALES_FOLLOW_UP_KEY,
    crm_reference,
    draft_answer,
    draft_data,
)


def mock_visit_report_payload(
    draft: ReportDraft,
    final_report: FinalReport,
    crm_gateway: CrmGateway,
) -> dict[str, Any]:
    """Build the eNVenta-shaped mock visit report payload."""
    answers = dict(draft_data(draft).get("answers", {}))
    account = crm_reference(draft, "account")
    contact = crm_reference(draft, "contact")
    representative = default_field_sales_representative(crm_gateway)
    responsible_user = default_crm_user(crm_gateway)
    ratings = dict(draft.ratings_json)
    return {
        "visit_type": draft.visit_type or VisitType.IN_PERSON.value,
        "visit_report_status": VisitReportStatus.CLOSED.value,
        "report_status": VisitReportStatus.CLOSED.value,
        "account_id": draft.account_id or (account.get("id") if account else None),
        "account_number": account.get("account_number") if account else None,
        "account_type": (
            account.get("account_type") if account else AccountType.ADDRESS.value
        ),
        "account_search_name": account.get("search_name") if account else None,
        "contact_id": draft.contact_id or (contact.get("id") if contact else None),
        "contact_name": draft_answer(draft, "participants"),
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
        "customer_satisfaction_rating": rating_value(
            ratings,
            "customer_satisfaction_rating",
        ),
        "technical_attractiveness_rating": rating_value(
            ratings,
            "technical_attractiveness_rating",
        ),
        "commercial_attractiveness_rating": rating_value(
            ratings,
            "commercial_attractiveness_rating",
        ),
        "priority_rating": rating_value(ratings, "priority_rating"),
        "next_appointment_date": draft.follow_up_date,
        "offer_reference": answers.get("offer_reference"),
        "order_reference": answers.get("order_reference")
        or draft_data(draft).get("order_reference_raw"),
    }


def create_mock_reminders(
    draft: ReportDraft,
    mock_visit_report: Any,
    crm_gateway: CrmGateway,
) -> list[Any]:
    """Create follow-up reminders through the CRM gateway."""
    if not draft_data(draft).get(INSIDE_SALES_FOLLOW_UP_KEY):
        return []

    owner = default_crm_user(crm_gateway)
    if owner is None:
        return []

    reminder = crm_gateway.create_reminder(
        mock_visit_report.visit_report_number,
        {
            "due_date": draft.follow_up_date,
            "owner_type": ReminderOwnerType.CRM_USER.value,
            "owner_id": owner.id,
            "created_by_user_id": draft.sales_user_id,
            "message": reminder_message(draft),
        },
    )
    return [reminder]


def default_crm_user(crm_gateway: CrmGateway) -> Any | None:
    """Return the first active mock CRM user."""
    users = crm_gateway.list_crm_users()
    return users[0] if users else None


def default_field_sales_representative(crm_gateway: CrmGateway) -> Any | None:
    """Return the first active mock field-sales representative."""
    representatives = crm_gateway.list_field_sales_representatives()
    return representatives[0] if representatives else None


def rating_value(ratings: dict[str, Any], rating_key: str) -> int | None:
    """Return a numeric rating value if available."""
    rating = ratings.get(rating_key)
    if not isinstance(rating, dict):
        return None

    value = rating.get("value")
    return value if isinstance(value, int) else None
