"""Tests for BENNO database models."""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from benno.enums import (
    CustomerContextType,
    InsideSalesTaskType,
    MessageSender,
    MessageType,
    ReasonCode,
    ReportSection,
    ReportStatus,
    SectionStatus,
    SessionLanguage,
    UserRole,
    VisitType,
)
from benno.extensions import db
from benno.models import (
    Chat,
    ChatMessage,
    FinalReport,
    InsideSalesTask,
    MockContact,
    MockCustomer,
    MockOffer,
    MockOrder,
    ReportDraft,
    User,
)


def test_core_tables_are_created(app) -> None:
    inspector = db.inspect(db.engine)

    assert "users" in inspector.get_table_names()
    assert "report_drafts" in inspector.get_table_names()
    assert "mock_customers" in inspector.get_table_names()


def test_user_can_be_saved_with_role_and_password_hash(app) -> None:
    user = User(
        email="tester@example.invalid",
        username="Test User",
        password_hash=generate_password_hash("secret"),
        role=UserRole.SALES_REP.value,
        preferred_language=SessionLanguage.DE.value,
    )

    db.session.add(user)
    db.session.commit()

    saved_user = db.session.query(User).filter_by(email=user.email).one()
    assert saved_user.role == UserRole.SALES_REP.value
    assert check_password_hash(saved_user.password_hash, "secret")


def test_sqlite_foreign_keys_are_enforced(app) -> None:
    invalid_chat = Chat(sales_user_id=999, session_language=SessionLanguage.DE.value)

    db.session.add(invalid_chat)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_chat_message_and_report_draft_can_be_saved(app) -> None:
    user = _create_sales_user()
    chat = Chat(sales_user=user, session_language=SessionLanguage.DE.value)
    message = ChatMessage(
        chat=chat,
        sender=MessageSender.USER.value,
        message_text="Customer visit summary.",
        message_type=MessageType.FREE_INPUT.value,
    )
    draft = ReportDraft(
        chat=chat,
        sales_user=user,
        report_status=ReportStatus.IN_PROGRESS.value,
        session_language=SessionLanguage.DE.value,
        customer_context_type=CustomerContextType.EXISTING_CUSTOMER.value,
        section_statuses_json={
            ReportSection.CUSTOMER_CONTEXT.value: SectionStatus.DETECTED.value,
        },
        missing_sections_json=[ReportSection.SUMMARY.value],
        ratings_json={"priority": {"value": 7, "reason": "Follow-up needed."}},
        draft_data_json={"customer_name": "Demo Customer"},
        last_question="What was agreed as the next step?",
    )

    db.session.add_all([chat, message, draft])
    db.session.commit()

    saved_chat = db.session.get(Chat, chat.id)
    assert saved_chat is not None
    assert saved_chat.messages[0].message_text == "Customer visit summary."
    assert saved_chat.report_draft.missing_sections_json == [
        ReportSection.SUMMARY.value
    ]


def test_final_report_and_inside_sales_task_can_be_linked(app) -> None:
    user = _create_sales_user()
    customer = _create_customer()
    chat = Chat(sales_user=user, session_language=SessionLanguage.DE.value)
    final_report = FinalReport(
        chat=chat,
        sales_user=user,
        customer=customer,
        visit_date=date(2026, 6, 26),
        visit_type=VisitType.ON_SITE.value,
        reason_code=ReasonCode.OFFER_FOLLOW_UP.value,
        summary="The customer reviewed the offer.",
        outcome="The offer remains relevant.",
        next_action="Inside sales should clarify missing master data.",
        ratings_json={"priority": {"value": 8, "reason": "Offer is time-sensitive."}},
        report_language=SessionLanguage.DE.value,
        final_report_text="Confirmed visit report text.",
        status=ReportStatus.INSIDE_SALES_INPUT_REQUIRED.value,
    )
    task = InsideSalesTask(
        final_report=final_report,
        task_type=InsideSalesTaskType.COMPLETE_MASTER_DATA.value,
        title="Complete contact data",
        description="The contact person is new and must be checked.",
        detected_contact_name="New Contact",
        related_customer=customer,
    )

    db.session.add_all([chat, final_report, task])
    db.session.commit()

    saved_report = db.session.get(FinalReport, final_report.id)
    assert saved_report is not None
    assert saved_report.inside_sales_tasks[0].title == "Complete contact data"


def test_mock_customer_relationships_work(app) -> None:
    customer = _create_customer()
    contact = MockContact(
        customer=customer,
        external_contact_id="CONT-TEST",
        full_name="Demo Contact",
    )
    offer = MockOffer(
        customer=customer,
        external_offer_id="OFF-TEST",
        title="Demo offer",
        status="open",
    )
    order = MockOrder(
        customer=customer,
        external_order_id="ORD-TEST",
        title="Demo order",
        status="active",
    )

    db.session.add_all([contact, offer, order])
    db.session.commit()

    saved_customer = db.session.get(MockCustomer, customer.id)
    assert saved_customer is not None
    assert saved_customer.contacts[0].full_name == "Demo Contact"
    assert saved_customer.offers[0].external_offer_id == "OFF-TEST"
    assert saved_customer.orders[0].external_order_id == "ORD-TEST"


def _create_sales_user() -> User:
    user = User(
        email="sales-test@example.invalid",
        username="Sales Test",
        password_hash=generate_password_hash("secret"),
        role=UserRole.SALES_REP.value,
        preferred_language=SessionLanguage.DE.value,
    )
    db.session.add(user)
    db.session.flush()
    return user


def _create_customer() -> MockCustomer:
    customer = MockCustomer(
        external_customer_id="CUST-TEST",
        name="Demo Customer GmbH",
        city="Berlin",
        industry="Testing",
    )
    db.session.add(customer)
    db.session.flush()
    return customer
