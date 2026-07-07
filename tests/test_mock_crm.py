"""Tests for the mock CRM/eNVenta service."""

from datetime import date

import pytest

from benno.enums import AccountType, ReminderOwnerType, VisitType
from benno.extensions import db
from benno.models import FinalReport, MockReminder, MockVisitReport, User
from benno.seed import seed_database
from benno.services.mock_crm import (
    create_mock_reminder,
    find_contacts,
    find_offers,
    find_orders,
    list_crm_users,
    list_field_sales_representatives,
    save_mock_visit_report,
    search_accounts,
)


def test_known_accounts_are_found_by_search_name(app) -> None:
    seed_database()

    accounts = search_accounts("Nordlicht")

    assert len(accounts) == 1
    assert accounts[0].account_number == "AKL-K-1001"
    assert accounts[0].account_type == AccountType.CUSTOMER.value


def test_accounts_can_be_filtered_by_type(app) -> None:
    seed_database()

    accounts = search_accounts("UrbanGrid", AccountType.ADDRESS.value)

    assert len(accounts) == 1
    assert accounts[0].account_type == AccountType.ADDRESS.value


def test_unknown_account_returns_empty_result(app) -> None:
    seed_database()

    accounts = search_accounts("Not An Account")

    assert accounts == []


def test_contacts_are_searched_by_account(app) -> None:
    seed_database()
    account = search_accounts("Nordlicht")[0]

    contacts = find_contacts(account.id, "Mara")

    assert len(contacts) == 1
    assert contacts[0].full_name == "Mara Stein"


def test_offers_and_orders_remain_separate(app) -> None:
    seed_database()
    account = search_accounts("Nordlicht")[0]

    offers = find_offers(account.id, "maintenance")
    orders = find_orders(account.id, "maintenance")

    assert offers == []
    assert len(orders) == 1
    assert orders[0].external_order_id == "ORD-23009"


def test_crm_users_and_representatives_are_listed_separately(app) -> None:
    seed_database()

    crm_users = list_crm_users("inside")
    representatives = list_field_sales_representatives("BENNO")

    assert len(crm_users) == 1
    assert crm_users[0].username == "inside.sales"
    assert len(representatives) == 1
    assert representatives[0].representative_number == "REP-001"


def test_save_mock_visit_report_persists_enventa_payload(app) -> None:
    seed_database()
    final_report = _create_final_report()

    visit_report = save_mock_visit_report(
        final_report.id,
        {
            "visit_type": VisitType.IN_PERSON.value,
            "target_topic": "Forecast",
            "info_text": "Forecast besprochen.",
            "agreement_text": "Folgetermin vereinbart.",
            "customer_satisfaction_rating": 8,
            "technical_attractiveness_rating": 7,
            "commercial_attractiveness_rating": 6,
            "priority_rating": 9,
        },
    )
    db.session.commit()

    saved_report = db.session.get(MockVisitReport, visit_report.id)
    assert saved_report.visit_report_number == "VR-00001"
    assert saved_report.target_topic == "Forecast"
    assert saved_report.priority_rating == 9


def test_create_mock_reminder_persists_owner_due_date_message_and_report(app) -> None:
    seed_database()
    final_report = _create_final_report()
    visit_report = save_mock_visit_report(
        final_report.id,
        {
            "visit_type": VisitType.PHONE.value,
            "target_topic": "Lead follow-up",
            "info_text": "Lead needs callback.",
            "agreement_text": "Inside sales calls next week.",
        },
    )

    reminder = create_mock_reminder(
        visit_report.visit_report_number,
        {
            "due_date": date(2026, 7, 14),
            "owner_type": ReminderOwnerType.CRM_USER.value,
            "owner_id": 1,
            "created_by_user_id": final_report.sales_user_id,
            "message": "Bitte Lead anrufen.",
        },
    )
    db.session.commit()

    saved_reminder = db.session.get(MockReminder, reminder.id)
    assert saved_reminder.visit_report_number == visit_report.visit_report_number
    assert saved_reminder.due_date == date(2026, 7, 14)
    assert saved_reminder.message == "Bitte Lead anrufen."


def test_save_mock_visit_report_requires_core_payload(app) -> None:
    seed_database()
    final_report = _create_final_report()

    with pytest.raises(ValueError):
        save_mock_visit_report(final_report.id, {"visit_type": VisitType.PHONE.value})


def _create_final_report() -> FinalReport:
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    final_report = FinalReport(
        chat_id=_create_chat_id(sales_user),
        sales_user=sales_user,
        summary="Summary",
        ratings_json={},
        final_report_text="Report",
    )
    db.session.add(final_report)
    db.session.flush()
    return final_report


def _create_chat_id(sales_user: User) -> int:
    from benno.models import Chat

    chat = Chat(sales_user=sales_user)
    db.session.add(chat)
    db.session.flush()
    return chat.id
