"""Account and lead resolution for visit report drafts."""

import re

from benno.enums import AccountType, CustomerContextType, ValidationStatus
from benno.models import ReportDraft
from benno.services.mock_crm import AccountReference, CrmGateway
from benno.services.report_shortcuts import mentions_lead, mentions_new
from benno.services.report_state import (
    ACCOUNT_TYPE_OVERRIDE_KEY,
    clear_crm_reference,
    set_draft_metadata,
    store_crm_reference,
)

CLASSIFICATION_WORDS = frozenset(
    {
        "adresse",
        "address",
        "akl",
        "eintrag",
        "kunde",
        "kunden",
        "lead",
        "leads",
        "lieb",
        "lieferant",
        "lieferanten",
        "interessent",
        "interessenten",
        "potenzieller",
        "potentielle",
        "potentieller",
        "prospect",
        "neu",
        "neue",
        "neuer",
        "neues",
        "bestehend",
        "bestehende",
        "bestehender",
    }
)
CONTEXT_FILLER_WORDS = frozenset(
    {
        "also",
        "das",
        "der",
        "die",
        "ein",
        "eine",
        "einem",
        "einen",
        "einer",
        "es",
        "geht",
        "ist",
        "sind",
        "um",
    }
)


def resolve_visit_context(
    draft: ReportDraft,
    answer_text: str,
    crm_gateway: CrmGateway,
) -> None:
    """Resolve a visit context answer into account or lead draft state."""
    reset_visit_account_context(draft)
    if mentions_address_or_lead_context(answer_text):
        apply_new_lead_context(draft)
        set_draft_metadata(draft, ACCOUNT_TYPE_OVERRIDE_KEY, AccountType.ADDRESS.value)
        return

    account_matches = crm_gateway.search_accounts(answer_text)
    apply_account_match_result(draft, account_matches)


def apply_lead_context_signal(draft: ReportDraft, message_text: str) -> None:
    """Mark the draft as new lead when a later answer clearly says so."""
    if draft.account_id is not None:
        return
    if not mentions_address_or_lead_context(message_text):
        return

    apply_new_lead_context(draft)
    set_draft_metadata(draft, ACCOUNT_TYPE_OVERRIDE_KEY, AccountType.ADDRESS.value)


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


def mentions_address_or_lead_context(answer_text: str) -> bool:
    """Return whether an answer classifies the AKL context as an address/lead."""
    normalized_text = answer_text.lower()
    return (
        mentions_lead(normalized_text)
        or mentions_new_lead(normalized_text)
        or re.search(r"\badresse\b", normalized_text) is not None
    )


def extract_visit_context_name(answer_text: str) -> str | None:
    """Extract a concrete AKL name, keeping type-only answers incomplete."""
    cleaned_text = _clean_context_candidate(answer_text)
    for pattern in _name_patterns():
        match = re.search(pattern, cleaned_text, flags=re.IGNORECASE)
        if match is None:
            continue

        candidate = _clean_context_candidate(match.group("name"))
        if _is_concrete_context_name(candidate):
            return candidate

    candidate = _strip_context_prefix(cleaned_text)
    if _is_concrete_context_name(candidate):
        return candidate

    return None


def _name_patterns() -> tuple[str, ...]:
    return (
        r"\b(?:firma|adresse|interessent|kunde|lieferant|lead)\s+"
        r"(?:hei[ßs]t|heisst|namens|ist|sind)\s+(?P<name>.+)",
        r"\b(?:die|der|das)\s+(?:hei[ßs]en|heissen|hei[ßs]t|heisst)\s+" r"(?P<name>.+)",
        r"\b(?:bei|mit)\s+(?P<name>[A-ZÄÖÜ][\wÄÖÜäöüß&.-]*"
        r"(?:\s+[A-ZÄÖÜ][\wÄÖÜäöüß&.-]*){0,4})\b",
    )


def _strip_context_prefix(answer_text: str) -> str:
    return re.sub(
        r"^(?:es\s+geht\s+um|das\s+ist|es\s+ist|bei|mit)\s+",
        "",
        answer_text,
        flags=re.IGNORECASE,
    ).strip()


def _is_concrete_context_name(candidate: str) -> bool:
    if not candidate:
        return False

    tokens = [token.lower() for token in re.findall(r"[\wÄÖÜäöüß&.-]+", candidate)]
    meaningful_tokens = [
        token
        for token in tokens
        if token not in CONTEXT_FILLER_WORDS and token not in CLASSIFICATION_WORDS
    ]
    if not meaningful_tokens:
        return False

    if len(tokens) > 8 and not _contains_company_signal(candidate):
        return False

    return True


def _contains_company_signal(candidate: str) -> bool:
    return bool(
        re.search(
            r"\b(?:gmbh|ag|kg|ohg|ug|se|solar|energy|energie|maschinenbau)\b",
            candidate,
            flags=re.IGNORECASE,
        )
        or re.search(r"\b[A-ZÄÖÜ][a-zäöüß]+[A-Z][\wÄÖÜäöüß&.-]*\b", candidate)
    )


def _clean_context_candidate(value: str) -> str:
    cleaned_value = re.sub(r"\s+", " ", value).strip(" \t\r\n,.;:-")
    cleaned_value = re.sub(
        r"\b(?:und|aber|also)\s+(?:ich|das|der|die|es)\b.*$",
        "",
        cleaned_value,
        flags=re.IGNORECASE,
    )
    return cleaned_value.strip(" \t\r\n,.;:-")


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
