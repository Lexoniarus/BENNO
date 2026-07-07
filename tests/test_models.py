"""Tests for BENNO database models."""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from benno.enums import (
    AccountType,
    MessageSender,
    MessageType,
    ReminderOwnerType,
    ReportStatus,
    SessionLanguage,
    UserRole,
    VisitReportStatus,
    VisitType,
)
from benno.extensions import db
from benno.models import (
    Chat,
    ChatMessage,
    FinalReport,
    MockAccount,
    MockContact,
    MockCrmUser,
    MockFieldSalesRepresentative,
    MockOffer,
    MockOrder,
    MockReminder,
    MockVisitReport,
    ReportDraft,
    User,
)


def test_core_tables_are_created(app) -> None:
    inspector = db.inspect(db.engine)

    assert "users" in inspector.get_table_names()
    assert "report_drafts" in inspector.get_table_names()
    assert "mock_accounts" in inspector.get_table_names()
    assert "mock_visit_reports" in inspector.get_table_names()
    assert "mock_reminders" in inspector.get_table_names()


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
    account = _create_account()
    chat = Chat(sales_user=user, session_language=SessionLanguage.DE.value)
    message = ChatMessage(
        chat=chat,
        sender=MessageSender.USER.value,
        message_text="Besuch bei Demo Account.",
        message_type=MessageType.FREE_INPUT.value,
    )
    draft = ReportDraft(
        chat=chat,
        sales_user=user,
        account=account,
        report_status=ReportStatus.IN_PROGRESS.value,
        session_language=SessionLanguage.DE.value,
        section_statuses_json={},
        missing_sections_json=["info_text"],
        ratings_json={"priority_rating": {"value": 7, "reason": "Important."}},
        draft_data_json={"answers": {"visit_context": "Demo Account"}},
        last_question="Was wurde besprochen?",
    )

    db.session.add_all([chat, message, draft])
    db.session.commit()

    saved_chat = db.session.get(Chat, chat.id)
    assert saved_chat is not None
    assert saved_chat.messages[0].message_text == "Besuch bei Demo Account."
    assert saved_chat.report_draft.account.account_number == "AKL-K-TEST"


def test_phase_6_mock_account_relationships_work(app) -> None:
    account = _create_account()
    contact = MockContact(
        account=account,
        external_contact_id="CONT-TEST",
        full_name="Demo Contact",
    )
    offer = MockOffer(
        account=account,
        external_offer_id="OFF-TEST",
        title="Demo offer",
        status="open",
    )
    order = MockOrder(
        account=account,
        external_order_id="ORD-TEST",
        title="Demo order",
        status="active",
    )

    db.session.add_all([contact, offer, order])
    db.session.commit()

    saved_account = db.session.get(MockAccount, account.id)
    assert saved_account is not None
    assert saved_account.contacts[0].full_name == "Demo Contact"
    assert saved_account.offers[0].external_offer_id == "OFF-TEST"
    assert saved_account.orders[0].external_order_id == "ORD-TEST"


def test_crm_users_and_field_sales_representatives_are_independent(app) -> None:
    crm_user = MockCrmUser(
        username="inside.test",
        display_name="Inside Test",
        email="inside@example.invalid",
    )
    representative = MockFieldSalesRepresentative(
        representative_number="REP-TEST",
        display_name="Rep Test",
        email="rep@example.invalid",
    )

    db.session.add_all([crm_user, representative])
    db.session.commit()

    assert db.session.query(MockCrmUser).count() == 1
    assert db.session.query(MockFieldSalesRepresentative).count() == 1


def test_mock_visit_report_and_reminder_can_be_linked_by_report_number(app) -> None:
    user = _create_sales_user()
    account = _create_account()
    crm_user = MockCrmUser(username="inside", display_name="Inside Sales")
    representative = MockFieldSalesRepresentative(
        representative_number="REP-001",
        display_name="Sales Rep",
    )
    chat = Chat(sales_user=user, session_language=SessionLanguage.DE.value)
    final_report = FinalReport(
        chat=chat,
        sales_user=user,
        account=account,
        visit_date=date(2026, 7, 7),
        visit_type=VisitType.IN_PERSON.value,
        summary="Demo summary",
        ratings_json={},
        report_language=SessionLanguage.DE.value,
        final_report_text="Confirmed report",
        status=ReportStatus.CONFIRMED.value,
    )
    visit_report = MockVisitReport(
        visit_report_number="VR-TEST",
        final_report=final_report,
        visit_type=VisitType.IN_PERSON.value,
        visit_report_status=VisitReportStatus.CLOSED.value,
        report_status=VisitReportStatus.CLOSED.value,
        account=account,
        account_number=account.account_number,
        account_type=account.account_type,
        account_search_name=account.search_name,
        field_sales_representative=representative,
        responsible_user=crm_user,
        visit_date=date(2026, 7, 7),
        target_topic="Demo topic",
        info_text="Demo info",
        agreement_text="Demo agreement",
    )
    reminder = MockReminder(
        visit_report=visit_report,
        due_date=date(2026, 7, 14),
        owner_type=ReminderOwnerType.CRM_USER.value,
        owner_id=1,
        created_by_user=user,
        message="Please follow up.",
    )

    db.session.add_all(
        [crm_user, representative, chat, final_report, visit_report, reminder]
    )
    db.session.commit()

    saved_visit_report = db.session.get(MockVisitReport, visit_report.id)
    assert saved_visit_report.visit_report_status == VisitReportStatus.CLOSED.value
    assert saved_visit_report.report_status == VisitReportStatus.CLOSED.value
    assert saved_visit_report.reminders[0].message == "Please follow up."


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


def _create_account() -> MockAccount:
    account = MockAccount(
        account_number="AKL-K-TEST",
        account_type=AccountType.CUSTOMER.value,
        search_name="DEMO",
        display_name="Demo Account GmbH",
        address_text="Berlin",
    )
    db.session.add(account)
    db.session.flush()
    return account
