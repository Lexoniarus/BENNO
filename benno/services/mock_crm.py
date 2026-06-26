"""Lookup service for the local placeholder CRM/ERP data."""

from sqlalchemy import or_

from benno.models import MockContact, MockCustomer, MockLead, MockOffer, MockOrder


def find_customers(query: str) -> list[MockCustomer]:
    """Find mock customers by name, external id, city, or industry."""
    search_term = _like_query(query)
    if search_term is None:
        return []

    return (
        MockCustomer.query.filter(
            or_(
                MockCustomer.name.ilike(search_term),
                MockCustomer.external_customer_id.ilike(search_term),
                MockCustomer.city.ilike(search_term),
                MockCustomer.industry.ilike(search_term),
            )
        )
        .order_by(MockCustomer.name)
        .all()
    )


def find_leads(query: str) -> list[MockLead]:
    """Find mock leads by company, contact, external id, city, or source."""
    search_term = _like_query(query)
    if search_term is None:
        return []

    return (
        MockLead.query.filter(
            or_(
                MockLead.company_name.ilike(search_term),
                MockLead.contact_name.ilike(search_term),
                MockLead.external_lead_id.ilike(search_term),
                MockLead.city.ilike(search_term),
                MockLead.source.ilike(search_term),
            )
        )
        .order_by(MockLead.company_name)
        .all()
    )


def find_contacts(
    customer_id: int,
    query: str | None = None,
) -> list[MockContact]:
    """Find contacts for one mock customer."""
    contact_query = MockContact.query.filter_by(customer_id=customer_id)
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
    customer_id: int,
    query: str | None = None,
) -> list[MockOffer]:
    """Find offer references for one mock customer."""
    offer_query = MockOffer.query.filter_by(customer_id=customer_id)
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
    customer_id: int,
    query: str | None = None,
) -> list[MockOrder]:
    """Find order references for one mock customer."""
    order_query = MockOrder.query.filter_by(customer_id=customer_id)
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


def _like_query(query: str | None) -> str | None:
    if query is None:
        return None

    normalized_query = query.strip()
    if not normalized_query:
        return None

    return f"%{normalized_query}%"
