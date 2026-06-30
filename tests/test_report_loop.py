"""Tests for the deterministic Phase 4 report loop."""

from benno.enums import (
    InsideSalesTaskType,
    MessageSender,
    ReportStatus,
    UserRole,
)
from benno.extensions import db
from benno.models import Chat, FinalReport, InsideSalesTask, User
from benno.seed import seed_database
from benno.services.report_loop import (
    confirm_report,
    process_report_message,
    start_report_chat,
)

STANDARD_ANSWERS = [
    "Nordlicht Maschinenbau GmbH",
    "Mara Stein",
    "Offer follow-up for conveyor modernization",
    "We discussed the modernization package and technical timing.",
    "Customer is interested and wants a revised proposal.",
    "Send revised proposal by 2026-07-10.",
    "OFF-24001",
    "none",
    "8 because the opportunity is concrete.",
    "7 because the meeting was constructive.",
    "8 because the customer expects quick follow-up.",
    "6 because budget approval is still open.",
    "8 because sales must act quickly.",
    "7 because the customer sounded satisfied.",
]


def test_service_creates_chat_draft_and_initial_question(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()

    chat = start_report_chat(sales_user)

    assert chat.report_draft is not None
    assert chat.status == ReportStatus.IN_PROGRESS.value
    assert len(chat.messages) == 1
    assert chat.messages[0].sender == MessageSender.ASSISTANT.value
    assert "customer or lead" in chat.messages[0].message_text


def test_service_advances_to_review_and_confirms_once(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    chat = start_report_chat(sales_user)

    for answer in STANDARD_ANSWERS:
        process_report_message(chat, answer)

    assert chat.status == ReportStatus.READY_FOR_REVIEW.value
    assert chat.report_draft.missing_sections_json == []
    assert db.session.query(FinalReport).count() == 0

    first_report = confirm_report(chat)
    second_report = confirm_report(chat)

    assert first_report.id == second_report.id
    assert db.session.query(FinalReport).count() == 1
    assert first_report.status == ReportStatus.CONFIRMED.value
    assert first_report.summary == STANDARD_ANSWERS[3]
    assert first_report.related_offer is not None
    assert "Visit Report" in first_report.final_report_text


def test_confirmed_report_rejects_late_messages(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    chat = start_report_chat(sales_user)

    for answer in STANDARD_ANSWERS:
        process_report_message(chat, answer)

    confirm_report(chat)
    message_count = len(chat.messages)

    try:
        process_report_message(chat, "Please change the summary.")
    except ValueError as error:
        assert str(error) == "This report can no longer be changed."

    assert len(chat.messages) == message_count
    assert chat.status == ReportStatus.CONFIRMED.value


def test_service_creates_inside_sales_tasks_for_clear_cases(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    chat = start_report_chat(sales_user)
    answers = [
        "new lead CloudGate Systems",
        "new contact Paula Brandt",
        *STANDARD_ANSWERS[2:6],
        "unclear offer, maybe OFF-999",
        "none",
        *STANDARD_ANSWERS[8:],
    ]

    for answer in answers:
        process_report_message(chat, answer)

    final_report = confirm_report(chat)
    task_types = {task.task_type for task in final_report.inside_sales_tasks}

    assert db.session.query(InsideSalesTask).count() == 3
    assert InsideSalesTaskType.COMPLETE_MASTER_DATA.value in task_types
    assert InsideSalesTaskType.CLARIFY_DETAILS.value in task_types


def test_normal_known_customer_flow_creates_no_inside_sales_task(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    chat = start_report_chat(sales_user)

    for answer in STANDARD_ANSWERS:
        process_report_message(chat, answer)

    final_report = confirm_report(chat)

    assert final_report.inside_sales_tasks == []


def test_cancel_report_route_marks_work_as_cancelled(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client, "sales@benno.local", "sales-demo-password")
        start_response = client.get("/sales/reports/new")
        chat_id = _chat_id_from_redirect(start_response.location)
        cancel_response = client.post(f"/sales/reports/{chat_id}/cancel")

    chat = db.session.get(Chat, chat_id)
    assert cancel_response.status_code == 302
    assert chat.status == ReportStatus.CANCELLED.value
    assert chat.report_draft.report_status == ReportStatus.CANCELLED.value


def test_report_web_flow_creates_confirmed_final_report(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client, "sales@benno.local", "sales-demo-password")
        start_response = client.get("/sales/reports/new")
        chat_id = _chat_id_from_redirect(start_response.location)

        for answer in STANDARD_ANSWERS:
            response = client.post(
                f"/sales/reports/{chat_id}/messages",
                data={"message": answer},
            )
            assert response.status_code == 302

        review_response = client.get(f"/sales/reports/{chat_id}/review")
        confirm_response = client.post(f"/sales/reports/{chat_id}/confirm")

    final_report = FinalReport.query.filter_by(chat_id=chat_id).one()
    assert review_response.status_code == 200
    assert b"Confirm and Save" in review_response.data
    assert confirm_response.status_code == 302
    assert final_report.status == ReportStatus.CONFIRMED.value


def test_confirmed_report_cannot_be_cancelled(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client, "sales@benno.local", "sales-demo-password")
        start_response = client.get("/sales/reports/new")
        chat_id = _chat_id_from_redirect(start_response.location)

        for answer in STANDARD_ANSWERS:
            client.post(
                f"/sales/reports/{chat_id}/messages",
                data={"message": answer},
            )

        client.post(f"/sales/reports/{chat_id}/confirm")
        cancel_response = client.post(f"/sales/reports/{chat_id}/cancel")

    chat = db.session.get(Chat, chat_id)
    assert cancel_response.status_code == 302
    assert cancel_response.location == f"/sales/reports/{chat_id}"
    assert chat.status == ReportStatus.CONFIRMED.value
    assert chat.report_draft.report_status == ReportStatus.CONFIRMED.value


def test_review_page_is_blocked_until_sections_are_complete(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client, "sales@benno.local", "sales-demo-password")
        start_response = client.get("/sales/reports/new")
        chat_id = _chat_id_from_redirect(start_response.location)
        review_response = client.get(f"/sales/reports/{chat_id}/review")

    assert review_response.status_code == 302
    assert review_response.location == f"/sales/reports/{chat_id}"


def test_report_routes_enforce_sales_boundaries(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    other_user = User(
        email="other-sales@example.invalid",
        username="Other Sales",
        password_hash=sales_user.password_hash,
        role=UserRole.SALES_REP.value,
        preferred_language=sales_user.preferred_language,
    )
    db.session.add(other_user)
    db.session.flush()
    other_chat = start_report_chat(other_user)

    with app.test_client() as client:
        anonymous_response = client.get("/sales/reports/new")
        _login(client, "admin@benno.local", "admin-demo-password")
        admin_response = client.get("/sales/reports/new")
        client.get("/logout")
        _login(client, "sales@benno.local", "sales-demo-password")
        other_chat_response = client.get(f"/sales/reports/{other_chat.id}")

    assert anonymous_response.status_code == 302
    assert anonymous_response.location.startswith("/login")
    assert admin_response.status_code == 403
    assert other_chat_response.status_code == 404


def _login(client, email: str, password: str):
    return client.post(
        "/login",
        data={"email": email, "password": password},
    )


def _chat_id_from_redirect(location: str) -> int:
    return int(location.rsplit("/", maxsplit=1)[-1])
