"""Account and lead resolution for visit report drafts."""

from benno.enums import AccountType, CustomerContextType, ValidationStatus
from benno.models import ReportDraft
from benno.services.mock_crm import AccountReference, CrmGateway
from benno.services.report_shortcuts import mentions_lead, mentions_new
from benno.services.report_state import clear_crm_reference, store_crm_reference


def resolve_visit_context(
    draft: ReportDraft,
    answer_text: str,
    crm_gateway: CrmGateway,
) -> None:
    """Resolve a visit context answer into account or lead draft state."""
    reset_visit_account_context(draft)
    if mentions_new_lead(answer_text):
        apply_new_lead_context(draft)
        return

    account_matches = crm_gateway.search_accounts(answer_text)
    apply_account_match_result(draft, account_matches)


def apply_lead_context_signal(draft: ReportDraft, message_text: str) -> None:
    """Mark the draft as new lead when a later answer clearly says so."""
    if draft.account_id is not None:
        return
    if not mentions_lead(message_text):
        return

    apply_new_lead_context(draft)


def reset_visit_account_context(draft: ReportDraft) -> None:
    """Clear account and contact state before resolving a new visit context."""
    draft.account_id = None
    draft.customer = None
    draft.lead = None
    draft.contact_id = None
    clear_crm_reference(draft, "account")
    clear_crm_reference(draft, "contact")


def mentions_new_lead(answer_text: str) -> bool:
    """Return whether an answer explicitly describes a new lead."""
    normalized_text = answer_text.lower()
    return mentions_new(normalized_text) or "lead" in normalized_text


def apply_new_lead_context(draft: ReportDraft) -> None:
    """Store the draft state for a confirmed new lead context."""
    draft.customer_context_type = CustomerContextType.NEW_LEAD.value
    draft.validation_status = ValidationStatus.CONFIRMED_NEW.value


def apply_account_match_result(
    draft: ReportDraft,
    account_matches: list[AccountReference],
) -> None:
    """Apply the CRM account search result to the draft."""
    if len(account_matches) == 1:
        apply_matched_account_context(draft, account_matches[0])
        return

    apply_unclear_account_context(draft)


def apply_matched_account_context(
    draft: ReportDraft,
    account: AccountReference,
) -> None:
    """Store the draft state for one matched account."""
    draft.account_id = account.id
    store_crm_reference(draft, "account", account)
    draft.customer_context_type = customer_context_type_for_account(account)
    draft.validation_status = ValidationStatus.MATCHED.value


def apply_unclear_account_context(draft: ReportDraft) -> None:
    """Store the draft state for an unresolved account answer."""
    draft.customer_context_type = CustomerContextType.UNCLEAR.value
    draft.validation_status = ValidationStatus.UNKNOWN.value


def customer_context_type_for_account(account: AccountReference) -> str:
    """Map an AKL account type to BENNO's customer context type."""
    if account.account_type == AccountType.ADDRESS.value:
        return CustomerContextType.EXISTING_LEAD.value

    return CustomerContextType.EXISTING_CUSTOMER.value
