"""Seed data for the BENNO mock database."""

from decimal import Decimal

from werkzeug.security import generate_password_hash

from benno.enums import AiProvider, SessionLanguage, UserRole
from benno.extensions import db
from benno.models import (
    GlobalSetting,
    MockContact,
    MockCustomer,
    MockLead,
    MockOffer,
    MockOrder,
    User,
)


def seed_database() -> None:
    """Create local demo data if it does not already exist."""
    _seed_global_settings()
    _seed_users()
    _seed_mock_crm_data()
    db.session.commit()


def _seed_global_settings() -> None:
    existing_setting = db.session.query(GlobalSetting).first()
    if existing_setting:
        return

    db.session.add(
        GlobalSetting(
            default_language=SessionLanguage.DE.value,
            ai_provider=AiProvider.OPENAI.value,
        )
    )


def _seed_users() -> None:
    _create_user_if_missing(
        email="admin@benno.local",
        username="BENNO Admin",
        password="admin-demo-password",
        role=UserRole.ADMIN.value,
    )
    _create_user_if_missing(
        email="sales@benno.local",
        username="BENNO Sales Rep",
        password="sales-demo-password",
        role=UserRole.SALES_REP.value,
        external_sales_rep_id="SALES-DEMO-001",
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
    customer_data = [
        {
            "external_customer_id": "CUST-1001",
            "name": "Nordlicht Maschinenbau GmbH",
            "city": "Hamburg",
            "industry": "Mechanical Engineering",
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
            "external_customer_id": "CUST-1002",
            "name": "Solaris Verpackung AG",
            "city": "Freiburg",
            "industry": "Packaging",
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
            "external_customer_id": "CUST-1003",
            "name": "Hafenblick Logistik KG",
            "city": "Bremen",
            "industry": "Logistics",
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
            "external_customer_id": "CUST-1004",
            "name": "Alpina Medizintechnik GmbH",
            "city": "Munich",
            "industry": "Medical Technology",
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
    ]

    for customer_record in customer_data:
        customer = _create_customer_if_missing(customer_record)
        _create_contacts_if_missing(customer, customer_record["contacts"])
        _create_offers_if_missing(customer, customer_record["offers"])
        _create_orders_if_missing(customer, customer_record["orders"])

    _create_lead_if_missing(
        external_lead_id="LEAD-9001",
        company_name="UrbanGrid Mobility GmbH",
        contact_name="Timo Neumann",
        city="Cologne",
        source="trade_fair",
    )


def _create_customer_if_missing(customer_record: dict) -> MockCustomer:
    customer = (
        db.session.query(MockCustomer)
        .filter_by(external_customer_id=customer_record["external_customer_id"])
        .one_or_none()
    )
    if customer:
        return customer

    customer = MockCustomer(
        external_customer_id=customer_record["external_customer_id"],
        name=customer_record["name"],
        city=customer_record["city"],
        industry=customer_record["industry"],
    )
    db.session.add(customer)
    db.session.flush()
    return customer


def _create_contacts_if_missing(
    customer: MockCustomer,
    contact_records: list[dict],
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
                customer_id=customer.id,
                external_contact_id=contact_record["external_contact_id"],
                full_name=contact_record["full_name"],
                email=contact_record["email"],
                role_title=contact_record["role_title"],
            )
        )


def _create_offers_if_missing(
    customer: MockCustomer,
    offer_records: list[dict],
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
                customer_id=customer.id,
                external_offer_id=offer_record["external_offer_id"],
                title=offer_record["title"],
                status=offer_record["status"],
                amount=offer_record["amount"],
            )
        )


def _create_orders_if_missing(
    customer: MockCustomer,
    order_records: list[dict],
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
                customer_id=customer.id,
                external_order_id=order_record["external_order_id"],
                title=order_record["title"],
                status=order_record["status"],
                amount=order_record["amount"],
            )
        )


def _create_lead_if_missing(
    external_lead_id: str,
    company_name: str,
    contact_name: str,
    city: str,
    source: str,
) -> None:
    lead = (
        db.session.query(MockLead)
        .filter_by(external_lead_id=external_lead_id)
        .one_or_none()
    )
    if lead:
        return

    db.session.add(
        MockLead(
            external_lead_id=external_lead_id,
            company_name=company_name,
            contact_name=contact_name,
            city=city,
            source=source,
        )
    )
