"""Lookup and write service for local mock CRM/eNVenta data."""

from typing import Any

from sqlalchemy import or_

from benno.enums import ReminderOwnerType, ReminderStatus, VisitReportStatus
from benno.extensions import db
from benno.models import (
    MockAccount,
    MockContact,
    MockCrmUser,
    MockFieldSalesRepresentative,
    MockOffer,
    MockOrder,
    MockReminder,
    MockVisitReport,
)


def search_accounts(
    query: str,
    account_type: str | None = None,
) -> list[MockAccount]:
    """Search AKL-like mock accounts."""
    search_term = _like_query(query)
    if search_term is None:
        return []

    account_query = MockAccount.query.filter(
        or_(
            MockAccount.account_number.ilike(search_term),
            MockAccount.search_name.ilike(search_term),
            MockAccount.display_name.ilike(search_term),
            MockAccount.address_text.ilike(search_term),
        )
    )
    if account_type is not None:
        account_query = account_query.filter_by(account_type=account_type)

    return account_query.order_by(MockAccount.search_name).all()


def find_contacts(
    account_id: int,
    query: str | None = None,
) -> list[MockContact]:
    """Find contacts for one mock account."""
    contact_query = MockContact.query.filter_by(account_id=account_id)
    search_term = _like_query(query)

    if search_term is not None:
        contact_query = contact_query.filter(
            or_(
                MockContact.full_name.ilike(search_term),
                MockContact.email.ilike(search_term),
                MockContact.external_contact_id.ilike(search_term),
                MockContact.role_title.ilike(search_term),
            )
        )

    return contact_query.order_by(MockContact.full_name).all()


def find_offers(
    account_id: int,
    query: str | None = None,
) -> list[MockOffer]:
    """Find offer references for one mock account."""
    offer_query = MockOffer.query.filter_by(account_id=account_id)
    search_term = _like_query(query)

    if search_term is not None:
        offer_query = offer_query.filter(
            or_(
                MockOffer.external_offer_id.ilike(search_term),
                MockOffer.title.ilike(search_term),
                MockOffer.status.ilike(search_term),
            )
        )

    return offer_query.order_by(MockOffer.external_offer_id).all()


def find_orders(
    account_id: int,
    query: str | None = None,
) -> list[MockOrder]:
    """Find order references for one mock account."""
    order_query = MockOrder.query.filter_by(account_id=account_id)
    search_term = _like_query(query)

    if search_term is not None:
        order_query = order_query.filter(
            or_(
                MockOrder.external_order_id.ilike(search_term),
                MockOrder.title.ilike(search_term),
                MockOrder.status.ilike(search_term),
            )
        )

    return order_query.order_by(MockOrder.external_order_id).all()


def list_crm_users(query: str | None = None) -> list[MockCrmUser]:
    """List active CRM users, optionally filtered by text."""
    crm_user_query = MockCrmUser.query.filter_by(is_active=True)
    search_term = _like_query(query)

    if search_term is not None:
        crm_user_query = crm_user_query.filter(
            or_(
                MockCrmUser.username.ilike(search_term),
                MockCrmUser.display_name.ilike(search_term),
                MockCrmUser.email.ilike(search_term),
            )
        )

    return crm_user_query.order_by(MockCrmUser.display_name).all()


def list_field_sales_representatives(
    query: str | None = None,
) -> list[MockFieldSalesRepresentative]:
    """List active field sales representatives, optionally filtered by text."""
    representative_query = MockFieldSalesRepresentative.query.filter_by(is_active=True)
    search_term = _like_query(query)

    if search_term is not None:
        representative_query = representative_query.filter(
            or_(
                MockFieldSalesRepresentative.representative_number.ilike(search_term),
                MockFieldSalesRepresentative.display_name.ilike(search_term),
                MockFieldSalesRepresentative.email.ilike(search_term),
            )
        )

    return representative_query.order_by(
        MockFieldSalesRepresentative.display_name
    ).all()


def save_mock_visit_report(
    final_report_id: int,
    payload: dict[str, Any],
) -> MockVisitReport:
    """Save or return the eNVenta-shaped mock visit report for a final report."""
    existing_report = MockVisitReport.query.filter_by(
        final_report_id=final_report_id
    ).one_or_none()
    if existing_report is not None:
        return existing_report

    _validate_required_payload(
        payload,
        required_keys=(
            "visit_type",
            "target_topic",
            "info_text",
            "agreement_text",
        ),
    )
    visit_report = MockVisitReport(
        final_report_id=final_report_id,
        visit_report_number=_next_visit_report_number(),
        visit_type=payload["visit_type"],
        visit_report_status=payload.get(
            "visit_report_status",
            VisitReportStatus.CLOSED.value,
        ),
        report_status=payload.get("report_status", VisitReportStatus.CLOSED.value),
        account_id=payload.get("account_id"),
        account_number=payload.get("account_number"),
        account_type=payload.get("account_type"),
        account_search_name=payload.get("account_search_name"),
        contact_id=payload.get("contact_id"),
        contact_name=payload.get("contact_name"),
        field_sales_representative_id=payload.get("field_sales_representative_id"),
        responsible_user_id=payload.get("responsible_user_id"),
        visit_date=payload.get("visit_date"),
        visit_time=payload.get("visit_time"),
        target_topic=payload["target_topic"],
        info_text=payload["info_text"],
        agreement_text=payload["agreement_text"],
        strength_text=payload.get("strength_text"),
        weakness_text=payload.get("weakness_text"),
        customer_satisfaction_rating=payload.get("customer_satisfaction_rating"),
        technical_attractiveness_rating=payload.get("technical_attractiveness_rating"),
        commercial_attractiveness_rating=payload.get(
            "commercial_attractiveness_rating"
        ),
        priority_rating=payload.get("priority_rating"),
        next_appointment_date=payload.get("next_appointment_date"),
        offer_reference=payload.get("offer_reference"),
        order_reference=payload.get("order_reference"),
    )
    db.session.add(visit_report)
    db.session.flush()
    return visit_report


def create_mock_reminder(
    visit_report_number: str,
    payload: dict[str, Any],
) -> MockReminder:
    """Create a mock eNVenta follow-up reminder."""
    _validate_required_payload(
        payload,
        required_keys=("owner_type", "owner_id", "message"),
    )
    owner_type = payload["owner_type"]
    if owner_type not in {owner.value for owner in ReminderOwnerType}:
        raise ValueError("Unknown reminder owner type.")

    reminder = MockReminder(
        visit_report_number=visit_report_number,
        due_date=payload.get("due_date"),
        owner_type=owner_type,
        owner_id=payload["owner_id"],
        created_by_user_id=payload.get("created_by_user_id"),
        message=payload["message"],
        status=payload.get("status", ReminderStatus.OPEN.value),
    )
    db.session.add(reminder)
    db.session.flush()
    return reminder


def find_customers(query: str) -> list[MockAccount]:
    """Legacy wrapper for old customer lookup calls."""
    return search_accounts(query)


def find_leads(query: str) -> list[MockAccount]:
    """Legacy wrapper for old lead lookup calls."""
    return search_accounts(query)


def _validate_required_payload(
    payload: dict[str, Any],
    required_keys: tuple[str, ...],
) -> None:
    missing_keys = [
        key
        for key in required_keys
        if payload.get(key) is None or str(payload.get(key)).strip() == ""
    ]
    if missing_keys:
        raise ValueError(f"Missing required payload keys: {', '.join(missing_keys)}")


def _next_visit_report_number() -> str:
    next_id = (db.session.query(MockVisitReport).count() or 0) + 1
    return f"VR-{next_id:05d}"


def _like_query(query: str | None) -> str | None:
    if query is None:
        return None

    normalized_query = query.strip()
    if not normalized_query:
        return None

    return f"%{normalized_query}%"
