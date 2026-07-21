"""Tests for role navigation and content boundaries."""

from datetime import date

from werkzeug.security import generate_password_hash

from benno.enums import (
    MessageSender,
    MessageType,
    ReminderOwnerType,
    ReminderStatus,
    ReportStatus,
    SessionLanguage,
    UserRole,
    VisitType,
)
from benno.extensions import db
from benno.models import (
    Chat,
    ChatMessage,
    FinalReport,
    MockReminder,
    MockVisitReport,
    User,
)
from benno.seed import seed_database


def test_sales_open_reports_only_include_own_chats(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    other_user = _create_sales_user("other-sales@example.invalid")
    own_chat = Chat(sales_user=sales_user, status=ReportStatus.IN_PROGRESS.value)
    other_chat = Chat(sales_user=other_user, status=ReportStatus.IN_PROGRESS.value)
    db.session.add_all([own_chat, other_chat])
    db.session.commit()

    with app.test_client() as client:
        _login(client, "sales@benno.local", "sales-demo-password")
        response = client.get("/sales/reports/open")

    assert response.status_code == 200
    assert f'data-chat-id="{own_chat.id}"'.encode() in response.data
    assert f'data-chat-id="{other_chat.id}"'.encode() not in response.data


def test_sales_completed_reports_only_include_own_reports(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    other_user = _create_sales_user("other-sales@example.invalid")
    own_chat = Chat(sales_user=sales_user, status=ReportStatus.CONFIRMED.value)
    other_chat = Chat(sales_user=other_user, status=ReportStatus.CONFIRMED.value)
    own_report = _create_final_report(own_chat, sales_user, "Own report text")
    other_report = _create_final_report(other_chat, other_user, "Other report text")
    own_visit_report = MockVisitReport(
        visit_report_number="VR-OWN-001",
        final_report=own_report,
        visit_type=VisitType.IN_PERSON.value,
        account_search_name="Nordlicht Solar",
        target_topic="Angebot und Wartung",
        info_text="Project discussion.",
        agreement_text="Follow up.",
    )
    db.session.add_all(
        [own_chat, other_chat, own_report, other_report, own_visit_report]
    )
    db.session.commit()

    with app.test_client() as client:
        _login(client, "sales@benno.local", "sales-demo-password")
        response = client.get("/sales/reports/completed")

    assert response.status_code == 200
    assert f'data-report-id="{own_report.id}"'.encode() in response.data
    assert b"Nordlicht Solar" in response.data
    assert b"Angebot und Wartung" in response.data
    assert b"VR-OWN-001" in response.data
    assert f'data-report-id="{other_report.id}"'.encode() not in response.data


def test_admin_pages_do_not_render_chat_or_report_content(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    chat = Chat(sales_user=sales_user, status=ReportStatus.IN_PROGRESS.value)
    message = ChatMessage(
        chat=chat,
        sender=MessageSender.USER.value,
        message_text="SECRET CHAT TEXT",
        message_type=MessageType.FREE_INPUT.value,
    )
    report = _create_final_report(chat, sales_user, "SECRET REPORT TEXT")
    db.session.add_all([chat, message, report])
    db.session.commit()

    with app.test_client() as client:
        _login(client, "admin@benno.local", "admin-demo-password")
        responses = [
            client.get("/admin"),
            client.get("/admin/users"),
            client.get("/admin/settings"),
        ]

    for response in responses:
        assert response.status_code == 200
        assert b"SECRET CHAT TEXT" not in response.data
        assert b"SECRET REPORT TEXT" not in response.data


def test_admin_dashboard_counts_phase_6_mock_reminders(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    chat = Chat(sales_user=sales_user, status=ReportStatus.CONFIRMED.value)
    report = _create_final_report(chat, sales_user, "Reminder report text")
    visit_report = MockVisitReport(
        visit_report_number="VR-TEST-001",
        final_report=report,
        visit_type=VisitType.PHONE.value,
        target_topic="Follow-up",
        info_text="Follow-up discussion.",
        agreement_text="Inside sales should call back.",
    )
    reminder = MockReminder(
        visit_report_number="VR-TEST-001",
        owner_type=ReminderOwnerType.CRM_USER.value,
        owner_id=1,
        message="Bitte nachfassen.",
        status=ReminderStatus.OPEN.value,
    )
    db.session.add_all([chat, report, visit_report, reminder])
    db.session.commit()

    with app.test_client() as client:
        _login(client, "admin@benno.local", "admin-demo-password")
        response = client.get("/admin")

    assert response.status_code == 200
    assert b"Offene Wiedervorlagen" in response.data
    assert b"1" in response.data


def _create_sales_user(email: str) -> User:
    user = User(
        email=email,
        username=email,
        password_hash=generate_password_hash("secret"),
        role=UserRole.SALES_REP.value,
        preferred_language=SessionLanguage.DE.value,
    )
    db.session.add(user)
    db.session.flush()
    return user


def _create_final_report(
    chat: Chat,
    sales_user: User,
    final_report_text: str,
) -> FinalReport:
    return FinalReport(
        chat=chat,
        sales_user=sales_user,
        visit_date=date(2026, 6, 30),
        summary="Short summary",
        ratings_json={},
        report_language=SessionLanguage.DE.value,
        final_report_text=final_report_text,
        status=ReportStatus.CONFIRMED.value,
    )


def _login(client, email: str, password: str):
    return client.post(
        "/login",
        data={"email": email, "password": password},
    )
