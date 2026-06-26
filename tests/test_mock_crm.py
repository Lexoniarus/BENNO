"""Tests for the mock CRM/ERP lookup service."""

from benno.seed import seed_database
from benno.services.mock_crm import (
    find_contacts,
    find_customers,
    find_leads,
    find_offers,
    find_orders,
)


def test_known_customers_are_found(app) -> None:
    seed_database()

    customers = find_customers("Nordlicht")

    assert len(customers) == 1
    assert customers[0].external_customer_id == "CUST-1001"


def test_unknown_customer_returns_empty_result(app) -> None:
    seed_database()

    customers = find_customers("Not A Customer")

    assert customers == []


def test_contacts_are_searched_by_customer(app) -> None:
    seed_database()
    customer = find_customers("Nordlicht")[0]

    contacts = find_contacts(customer.id, "Mara")

    assert len(contacts) == 1
    assert contacts[0].full_name == "Mara Stein"


def test_offers_and_orders_remain_separate(app) -> None:
    seed_database()
    customer = find_customers("Nordlicht")[0]

    offers = find_offers(customer.id, "maintenance")
    orders = find_orders(customer.id, "maintenance")

    assert offers == []
    assert len(orders) == 1
    assert orders[0].external_order_id == "ORD-23009"


def test_unclear_offer_reference_can_return_multiple_matches(app) -> None:
    seed_database()
    customer = find_customers("Nordlicht")[0]

    offers = find_offers(customer.id, "Conveyor")

    assert len(offers) == 2


def test_leads_can_be_found_separately_from_customers(app) -> None:
    seed_database()

    leads = find_leads("UrbanGrid")

    assert len(leads) == 1
    assert leads[0].external_lead_id == "LEAD-9001"
