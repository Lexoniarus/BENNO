"""Tests for report account and lead resolution."""

from benno.enums import CustomerContextType, ValidationStatus
from benno.models import User
from benno.seed import seed_database
from benno.services.mock_crm import AccountReference, ContactReference
from benno.services.report_account_resolution import (
    apply_lead_context_signal,
    resolve_visit_context,
)
from benno.services.report_loop import start_report_chat
from benno.services.report_state import crm_reference, store_crm_reference


def test_resolve_visit_context_matches_one_account(app) -> None:
    chat = _start_sales_chat()
    draft = chat.report_draft

    resolve_visit_context(draft, "Nordlicht", _FakeAccountGateway())

    assert draft.account_id == 7
    assert draft.customer_context_type == CustomerContextType.EXISTING_CUSTOMER.value
    assert draft.validation_status == ValidationStatus.MATCHED.value
    assert crm_reference(draft, "account")["account_number"] == "AKL-K-7000"


def test_resolve_visit_context_resets_stale_contact_reference(app) -> None:
    chat = _start_sales_chat()
    draft = chat.report_draft
    draft.contact_id = 99
    store_crm_reference(
        draft,
        "contact",
        ContactReference(
            id=99,
            account_id=7,
            full_name="Alte Kontaktperson",
        ),
    )

    resolve_visit_context(draft, "Unbekannt", _NoAccountGateway())

    assert draft.contact_id is None
    assert crm_reference(draft, "contact") is None
    assert draft.customer_context_type == CustomerContextType.UNCLEAR.value
    assert draft.validation_status == ValidationStatus.UNKNOWN.value


def test_lead_signal_does_not_override_matched_account(app) -> None:
    chat = _start_sales_chat()
    draft = chat.report_draft
    resolve_visit_context(draft, "Nordlicht", _FakeAccountGateway())

    apply_lead_context_signal(draft, "Das ist doch ein Lead")

    assert draft.account_id == 7
    assert draft.customer_context_type == CustomerContextType.EXISTING_CUSTOMER.value
    assert draft.validation_status == ValidationStatus.MATCHED.value


def _start_sales_chat():
    seed_database()
    sales_user = User.query.filter_by(email="laura.schneider@solar-sales.example").one()
    return start_report_chat(sales_user)


class _FakeAccountGateway:
    def search_accounts(
        self,
        query: str,
        account_type: str | None = None,
    ) -> list[AccountReference]:
        return [
            AccountReference(
                id=7,
                account_number="AKL-K-7000",
                account_type="K",
                search_name="NORDLICHT",
                display_name="Nordlicht Maschinenbau GmbH",
            )
        ]


class _NoAccountGateway:
    def search_accounts(
        self,
        query: str,
        account_type: str | None = None,
    ) -> list[AccountReference]:
        return []
