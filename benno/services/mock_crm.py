"""Gateway boundary for CRM/eNVenta lookup and local mock writeback."""

from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol

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


@dataclass(frozen=True)
class AccountReference:
    """CRM account reference independent from the local ORM model."""

    id: int
    account_number: str
    account_type: str
    search_name: str
    display_name: str
    address_text: str | None = None


@dataclass(frozen=True)
class ContactReference:
    """CRM contact reference independent from the local ORM model."""

    id: int
    account_id: int | None
    full_name: str
    role_title: str | None = None
    email: str | None = None
    external_contact_id: str | None = None


@dataclass(frozen=True)
class OfferReference:
    """CRM offer reference independent from the local ORM model."""

    id: int
    account_id: int | None
    external_offer_id: str
    title: str
    status: str


@dataclass(frozen=True)
class OrderReference:
    """CRM order reference independent from the local ORM model."""

    id: int
    account_id: int | None
    external_order_id: str
    title: str
    status: str


@dataclass(frozen=True)
class CrmUserReference:
    """CRM user reference independent from the local ORM model."""

    id: int
    username: str
    display_name: str
    email: str | None = None


@dataclass(frozen=True)
class FieldSalesRepresentativeReference:
    """Field sales representative reference independent from the local ORM model."""

    id: int
    representative_number: str
    display_name: str
    email: str | None = None


@dataclass(frozen=True)
class VisitReportReference:
    """Saved eNVenta-shaped visit report reference."""

    id: int
    visit_report_number: str


@dataclass(frozen=True)
class ReminderReference:
    """Saved eNVenta-shaped reminder reference."""

    id: int
    visit_report_number: str
    message: str
    due_date: date | None = None


class CrmGateway(Protocol):
    """Replaceable CRM/eNVenta boundary used by the report loop."""

    def search_accounts(
        self,
        query: str,
        account_type: str | None = None,
    ) -> list[AccountReference]:
        """Search AKL-like accounts."""

    def find_contacts(
        self,
        account_id: int,
        query: str | None = None,
    ) -> list[ContactReference]:
        """Find contacts linked to an account."""

    def find_offers(
        self,
        account_id: int,
        query: str | None = None,
    ) -> list[OfferReference]:
        """Find offers linked to an account."""

    def find_orders(
        self,
        account_id: int,
        query: str | None = None,
    ) -> list[OrderReference]:
        """Find orders linked to an account."""

    def list_crm_users(self, query: str | None = None) -> list[CrmUserReference]:
        """List CRM users."""

    def list_field_sales_representatives(
        self,
        query: str | None = None,
    ) -> list[FieldSalesRepresentativeReference]:
        """List field sales representatives."""

    def save_visit_report(
        self,
        final_report_id: int,
        payload: dict[str, Any],
    ) -> VisitReportReference:
        """Save or return an eNVenta-shaped visit report."""

    def create_reminder(
        self,
        visit_report_number: str,
        payload: dict[str, Any],
    ) -> ReminderReference:
        """Create a follow-up reminder linked to a visit report."""


class MockCrmGateway:
    """SQLAlchemy-backed CRM/eNVenta gateway for the local mock database."""

    def search_accounts(
        self,
        query: str,
        account_type: str | None = None,
    ) -> list[AccountReference]:
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

        return [
            _account_reference(account)
            for account in account_query.order_by(MockAccount.search_name).all()
        ]

    def find_contacts(
        self,
        account_id: int,
        query: str | None = None,
    ) -> list[ContactReference]:
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

        return [
            _contact_reference(contact)
            for contact in contact_query.order_by(MockContact.full_name).all()
        ]

    def find_offers(
        self,
        account_id: int,
        query: str | None = None,
    ) -> list[OfferReference]:
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

        return [
            _offer_reference(offer)
            for offer in offer_query.order_by(MockOffer.external_offer_id).all()
        ]

    def find_orders(
        self,
        account_id: int,
        query: str | None = None,
    ) -> list[OrderReference]:
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

        return [
            _order_reference(order)
            for order in order_query.order_by(MockOrder.external_order_id).all()
        ]

    def list_crm_users(
        self,
        query: str | None = None,
    ) -> list[CrmUserReference]:
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

        return [
            _crm_user_reference(crm_user)
            for crm_user in crm_user_query.order_by(MockCrmUser.display_name).all()
        ]

    def list_field_sales_representatives(
        self,
        query: str | None = None,
    ) -> list[FieldSalesRepresentativeReference]:
        representative_query = MockFieldSalesRepresentative.query.filter_by(
            is_active=True
        )
        search_term = _like_query(query)

        if search_term is not None:
            representative_query = representative_query.filter(
                or_(
                    MockFieldSalesRepresentative.representative_number.ilike(
                        search_term
                    ),
                    MockFieldSalesRepresentative.display_name.ilike(search_term),
                    MockFieldSalesRepresentative.email.ilike(search_term),
                )
            )

        return [
            _representative_reference(representative)
            for representative in representative_query.order_by(
                MockFieldSalesRepresentative.display_name
            ).all()
        ]

    def save_visit_report(
        self,
        final_report_id: int,
        payload: dict[str, Any],
    ) -> VisitReportReference:
        existing_report = MockVisitReport.query.filter_by(
            final_report_id=final_report_id
        ).one_or_none()
        if existing_report is not None:
            return _visit_report_reference(existing_report)

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
            technical_attractiveness_rating=payload.get(
                "technical_attractiveness_rating"
            ),
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
        return _visit_report_reference(visit_report)

    def create_reminder(
        self,
        visit_report_number: str,
        payload: dict[str, Any],
    ) -> ReminderReference:
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
        return _reminder_reference(reminder)


def get_crm_gateway() -> CrmGateway:
    """Return the current CRM/eNVenta gateway implementation."""
    return MockCrmGateway()


def search_accounts(
    query: str,
    account_type: str | None = None,
) -> list[AccountReference]:
    """Compatibility wrapper for AKL-like account search."""
    return get_crm_gateway().search_accounts(query, account_type)


def find_contacts(
    account_id: int,
    query: str | None = None,
) -> list[ContactReference]:
    """Compatibility wrapper for account-scoped contact search."""
    return get_crm_gateway().find_contacts(account_id, query)


def find_offers(
    account_id: int,
    query: str | None = None,
) -> list[OfferReference]:
    """Compatibility wrapper for account-scoped offer search."""
    return get_crm_gateway().find_offers(account_id, query)


def find_orders(
    account_id: int,
    query: str | None = None,
) -> list[OrderReference]:
    """Compatibility wrapper for account-scoped order search."""
    return get_crm_gateway().find_orders(account_id, query)


def list_crm_users(query: str | None = None) -> list[CrmUserReference]:
    """Compatibility wrapper for CRM user listing."""
    return get_crm_gateway().list_crm_users(query)


def list_field_sales_representatives(
    query: str | None = None,
) -> list[FieldSalesRepresentativeReference]:
    """Compatibility wrapper for field sales representative listing."""
    return get_crm_gateway().list_field_sales_representatives(query)


def save_mock_visit_report(
    final_report_id: int,
    payload: dict[str, Any],
) -> VisitReportReference:
    """Compatibility wrapper for mock eNVenta visit report writeback."""
    return get_crm_gateway().save_visit_report(final_report_id, payload)


def create_mock_reminder(
    visit_report_number: str,
    payload: dict[str, Any],
) -> ReminderReference:
    """Compatibility wrapper for mock eNVenta reminder writeback."""
    return get_crm_gateway().create_reminder(visit_report_number, payload)


def find_customers(query: str) -> list[AccountReference]:
    """Legacy wrapper for old customer lookup calls."""
    return search_accounts(query)


def find_leads(query: str) -> list[AccountReference]:
    """Legacy wrapper for old lead lookup calls."""
    return search_accounts(query)


def _account_reference(account: MockAccount) -> AccountReference:
    return AccountReference(
        id=account.id,
        account_number=account.account_number,
        account_type=account.account_type,
        search_name=account.search_name,
        display_name=account.display_name,
        address_text=account.address_text,
    )


def _contact_reference(contact: MockContact) -> ContactReference:
    return ContactReference(
        id=contact.id,
        account_id=contact.account_id,
        full_name=contact.full_name,
        role_title=contact.role_title,
        email=contact.email,
        external_contact_id=contact.external_contact_id,
    )


def _offer_reference(offer: MockOffer) -> OfferReference:
    return OfferReference(
        id=offer.id,
        account_id=offer.account_id,
        external_offer_id=offer.external_offer_id,
        title=offer.title,
        status=offer.status,
    )


def _order_reference(order: MockOrder) -> OrderReference:
    return OrderReference(
        id=order.id,
        account_id=order.account_id,
        external_order_id=order.external_order_id,
        title=order.title,
        status=order.status,
    )


def _crm_user_reference(crm_user: MockCrmUser) -> CrmUserReference:
    return CrmUserReference(
        id=crm_user.id,
        username=crm_user.username,
        display_name=crm_user.display_name,
        email=crm_user.email,
    )


def _representative_reference(
    representative: MockFieldSalesRepresentative,
) -> FieldSalesRepresentativeReference:
    return FieldSalesRepresentativeReference(
        id=representative.id,
        representative_number=representative.representative_number,
        display_name=representative.display_name,
        email=representative.email,
    )


def _visit_report_reference(visit_report: MockVisitReport) -> VisitReportReference:
    return VisitReportReference(
        id=visit_report.id,
        visit_report_number=visit_report.visit_report_number,
    )


def _reminder_reference(reminder: MockReminder) -> ReminderReference:
    return ReminderReference(
        id=reminder.id,
        visit_report_number=reminder.visit_report_number,
        message=reminder.message,
        due_date=reminder.due_date,
    )


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
