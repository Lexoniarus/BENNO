"""Seed data for the BENNO mock database."""

from decimal import Decimal
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from benno.enums import AccountType, AiProvider, SessionLanguage, UserRole
from benno.extensions import db
from benno.models import (
    GlobalSetting,
    MockAccount,
    MockContact,
    MockCrmUser,
    MockFieldSalesRepresentative,
    MockOffer,
    MockOrder,
    User,
)

MOCK_ACCOUNT_DATA: list[dict[str, Any]] = [
    {
        "account_number": "AKL-K-1001",
        "account_type": AccountType.CUSTOMER.value,
        "search_name": "NORDLICHT",
        "display_name": "Nordlicht Maschinenbau GmbH",
        "address_text": "Hamburg",
        "address_restriction": None,
        "contacts": [
            {
                "external_contact_id": "CONT-1001",
                "full_name": "Mara Stein",
                "email": "mara.stein@example.invalid",
                "role_title": "Head of Procurement",
            },
            {
                "external_contact_id": "CONT-1002",
                "full_name": "Jonas Keller",
                "email": "jonas.keller@example.invalid",
                "role_title": "Operations Manager",
            },
        ],
        "offers": [
            {
                "external_offer_id": "OFF-24001",
                "title": "Conveyor modernization package",
                "status": "open",
                "amount": Decimal("48000.00"),
            },
            {
                "external_offer_id": "OFF-24011",
                "title": "Conveyor spare parts package",
                "status": "open",
                "amount": Decimal("8200.00"),
            },
        ],
        "orders": [
            {
                "external_order_id": "ORD-23009",
                "title": "Annual maintenance contract",
                "status": "active",
                "amount": Decimal("18500.00"),
            }
        ],
    },
    {
        "account_number": "AKL-K-1002",
        "account_type": AccountType.CUSTOMER.value,
        "search_name": "SOLARIS",
        "display_name": "Solaris Verpackung AG",
        "address_text": "Freiburg",
        "address_restriction": None,
        "contacts": [
            {
                "external_contact_id": "CONT-2001",
                "full_name": "Lea Hartmann",
                "email": "lea.hartmann@example.invalid",
                "role_title": "Plant Manager",
            }
        ],
        "offers": [
            {
                "external_offer_id": "OFF-24005",
                "title": "Line inspection and optimization",
                "status": "sent",
                "amount": Decimal("12600.00"),
            }
        ],
        "orders": [],
    },
    {
        "account_number": "AKL-K-1003",
        "account_type": AccountType.CUSTOMER.value,
        "search_name": "HAFENBLICK",
        "display_name": "Hafenblick Logistik KG",
        "address_text": "Bremen",
        "address_restriction": None,
        "contacts": [],
        "offers": [],
        "orders": [
            {
                "external_order_id": "ORD-24002",
                "title": "Warehouse scanner rollout",
                "status": "in_fulfillment",
                "amount": Decimal("31500.00"),
            }
        ],
    },
    {
        "account_number": "AKL-K-1004",
        "account_type": AccountType.CUSTOMER.value,
        "search_name": "ALPINA",
        "display_name": "Alpina Medizintechnik GmbH",
        "address_text": "Munich",
        "address_restriction": None,
        "contacts": [
            {
                "external_contact_id": "CONT-4001",
                "full_name": "Nina Vogel",
                "email": "nina.vogel@example.invalid",
                "role_title": "Technical Buyer",
            }
        ],
        "offers": [],
        "orders": [],
    },
    {
        "account_number": "AKL-A-9001",
        "account_type": AccountType.ADDRESS.value,
        "search_name": "URBANGRID",
        "display_name": "UrbanGrid Mobility GmbH",
        "address_text": "Cologne",
        "address_restriction": None,
        "contacts": [
            {
                "external_contact_id": "CONT-9001",
                "full_name": "Timo Neumann",
                "email": "timo.neumann@example.invalid",
                "role_title": "Business Development",
            }
        ],
        "offers": [],
        "orders": [],
    },
    {
        "account_number": "AKL-L-3001",
        "account_type": AccountType.SUPPLIER.value,
        "search_name": "RHEINTECH",
        "display_name": "RheinTech Komponenten OHG",
        "address_text": "Düsseldorf",
        "address_restriction": "Supplier demo record",
        "contacts": [],
        "offers": [],
        "orders": [],
    },
]


MOCK_CRM_USERS = [
    {
        "username": "inside.sales",
        "display_name": "Inside Sales Team",
        "email": "inside.sales@solar-sales.example",
    },
    {
        "username": "service.backoffice",
        "display_name": "Service Backoffice",
        "email": "service.backoffice@solar-sales.example",
    },
]


MOCK_FIELD_SALES_REPRESENTATIVES = [
    {
        "representative_number": "REP-001",
        "display_name": "Laura Schneider",
        "email": "laura.schneider@solar-sales.example",
    },
    {
        "representative_number": "REP-002",
        "display_name": "Markus Weber",
        "email": "markus.weber@solar-sales.example",
    },
    {
        "representative_number": "REP-003",
        "display_name": "Sophie Klein",
        "email": "sophie.klein@solar-sales.example",
    },
    {
        "representative_number": "REP-004",
        "display_name": "Tobias Fischer",
        "email": "tobias.fischer@solar-sales.example",
    },
]


def seed_database() -> None:
    """Create local demo data if it does not already exist."""
    _seed_global_settings()
    _seed_users()
    _seed_mock_crm_data()
    db.session.commit()


def _seed_global_settings() -> None:
    existing_setting = db.session.query(GlobalSetting).first()
    if existing_setting:
        if existing_setting.ai_provider == AiProvider.OPENAI.value:
            existing_setting.ai_provider = AiProvider.GEMINI.value
        return

    db.session.add(
        GlobalSetting(
            default_language=SessionLanguage.DE.value,
            ai_provider=AiProvider.GEMINI.value,
        )
    )


def _seed_users() -> None:
    _create_user_if_missing(
        email="admin@solar-sales.local",
        username="Nina Hartmann",
        password="Admin123",
        role=UserRole.ADMIN.value,
    )
    _create_user_if_missing(
        email="laura.schneider@solar-sales.example",
        username="Laura Schneider",
        password="Sales123",
        role=UserRole.SALES_REP.value,
        external_sales_rep_id="REP-001",
    )
    _create_user_if_missing(
        email="markus.weber@solar-sales.example",
        username="Markus Weber",
        password="Sales123",
        role=UserRole.SALES_REP.value,
        external_sales_rep_id="REP-002",
    )
    _create_user_if_missing(
        email="sophie.klein@solar-sales.example",
        username="Sophie Klein",
        password="Sales123",
        role=UserRole.SALES_REP.value,
        external_sales_rep_id="REP-003",
    )
    _create_user_if_missing(
        email="tobias.fischer@solar-sales.example",
        username="Tobias Fischer",
        password="Sales123",
        role=UserRole.SALES_REP.value,
        external_sales_rep_id="REP-004",
    )


def _create_user_if_missing(
    email: str,
    username: str,
    password: str,
    role: str,
    external_sales_rep_id: str | None = None,
) -> None:
    existing_user = db.session.query(User).filter_by(email=email).one_or_none()
    if existing_user:
        existing_user.username = username
        existing_user.role = role
        existing_user.preferred_language = SessionLanguage.DE.value
        existing_user.external_sales_rep_id = external_sales_rep_id
        existing_user.is_active = True
        if not check_password_hash(existing_user.password_hash, password):
            existing_user.password_hash = generate_password_hash(password)
        return

    db.session.add(
        User(
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
            preferred_language=SessionLanguage.DE.value,
            external_sales_rep_id=external_sales_rep_id,
            is_active=True,
        )
    )


def _seed_mock_crm_data() -> None:
    for account_record in MOCK_ACCOUNT_DATA:
        account = _create_account_if_missing(account_record)
        _create_contacts_if_missing(account, account_record["contacts"])
        _create_offers_if_missing(account, account_record["offers"])
        _create_orders_if_missing(account, account_record["orders"])

    for crm_user_record in MOCK_CRM_USERS:
        _create_crm_user_if_missing(**crm_user_record)

    for representative_record in MOCK_FIELD_SALES_REPRESENTATIVES:
        _create_field_sales_representative_if_missing(**representative_record)


def _create_account_if_missing(account_record: dict[str, Any]) -> MockAccount:
    account = (
        db.session.query(MockAccount)
        .filter_by(account_number=account_record["account_number"])
        .one_or_none()
    )
    if account:
        return account

    account = MockAccount(
        account_number=account_record["account_number"],
        account_type=account_record["account_type"],
        search_name=account_record["search_name"],
        display_name=account_record["display_name"],
        address_text=account_record["address_text"],
        address_restriction=account_record["address_restriction"],
    )
    db.session.add(account)
    db.session.flush()
    return account


def _create_contacts_if_missing(
    account: MockAccount,
    contact_records: list[dict[str, Any]],
) -> None:
    for contact_record in contact_records:
        contact = (
            db.session.query(MockContact)
            .filter_by(external_contact_id=contact_record["external_contact_id"])
            .one_or_none()
        )
        if contact:
            continue

        db.session.add(
            MockContact(
                account_id=account.id,
                external_contact_id=contact_record["external_contact_id"],
                full_name=contact_record["full_name"],
                email=contact_record["email"],
                role_title=contact_record["role_title"],
            )
        )


def _create_offers_if_missing(
    account: MockAccount,
    offer_records: list[dict[str, Any]],
) -> None:
    for offer_record in offer_records:
        offer = (
            db.session.query(MockOffer)
            .filter_by(external_offer_id=offer_record["external_offer_id"])
            .one_or_none()
        )
        if offer:
            continue

        db.session.add(
            MockOffer(
                account_id=account.id,
                external_offer_id=offer_record["external_offer_id"],
                title=offer_record["title"],
                status=offer_record["status"],
                amount=offer_record["amount"],
            )
        )


def _create_orders_if_missing(
    account: MockAccount,
    order_records: list[dict[str, Any]],
) -> None:
    for order_record in order_records:
        order = (
            db.session.query(MockOrder)
            .filter_by(external_order_id=order_record["external_order_id"])
            .one_or_none()
        )
        if order:
            continue

        db.session.add(
            MockOrder(
                account_id=account.id,
                external_order_id=order_record["external_order_id"],
                title=order_record["title"],
                status=order_record["status"],
                amount=order_record["amount"],
            )
        )


def _create_crm_user_if_missing(
    username: str,
    display_name: str,
    email: str,
) -> None:
    crm_user = db.session.query(MockCrmUser).filter_by(username=username).one_or_none()
    if crm_user:
        crm_user.display_name = display_name
        crm_user.email = email
        crm_user.is_active = True
        return

    db.session.add(
        MockCrmUser(
            username=username,
            display_name=display_name,
            email=email,
            is_active=True,
        )
    )


def _create_field_sales_representative_if_missing(
    representative_number: str,
    display_name: str,
    email: str,
) -> None:
    representative = (
        db.session.query(MockFieldSalesRepresentative)
        .filter_by(representative_number=representative_number)
        .one_or_none()
    )
    if representative:
        representative.display_name = display_name
        representative.email = email
        representative.is_active = True
        return

    db.session.add(
        MockFieldSalesRepresentative(
            representative_number=representative_number,
            display_name=display_name,
            email=email,
            is_active=True,
        )
    )
