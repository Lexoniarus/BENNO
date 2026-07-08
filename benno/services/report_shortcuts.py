"""Deterministic fallback parsing for the report workflow."""

import re
from datetime import date, timedelta

from benno.enums import ReasonCode, VisitType
from benno.services.report_steps import RATING_FIELDS, is_none_answer


def classify_reason(message_text: str) -> str:
    """Classify a visit reason from simple keyword hints."""
    normalized_text = message_text.lower()
    if "offer" in normalized_text or "angebot" in normalized_text:
        return ReasonCode.OFFER_FOLLOW_UP.value
    if "complaint" in normalized_text or "beschwer" in normalized_text:
        return ReasonCode.COMPLAINT_RELATED.value
    if "contract" in normalized_text or "vertrag" in normalized_text:
        return ReasonCode.CONTRACT_DISCUSSION.value
    if "lead" in normalized_text or "first" in normalized_text:
        return ReasonCode.LEAD_INITIAL_CONTACT.value
    if "relationship" in normalized_text or "beziehung" in normalized_text:
        return ReasonCode.RELATIONSHIP_MEETING.value

    return ReasonCode.OTHER.value


def parse_visit_type(message_text: str) -> str | None:
    """Parse visit type from a German or English free-text answer."""
    normalized_text = message_text.lower()
    if any(value in normalized_text for value in ("telefon", "phone", "call")):
        return VisitType.PHONE.value
    if any(
        value in normalized_text for value in ("virtuell", "video", "teams", "zoom")
    ):
        return VisitType.VIRTUAL.value
    if any(
        value in normalized_text
        for value in ("persön", "persoen", "personlich", "vor ort", "beim", "bei ")
    ):
        return VisitType.IN_PERSON.value
    if message_text in {visit_type.value for visit_type in VisitType}:
        return message_text

    return None


def parse_rating_value(message_text: str) -> int | None:
    """Parse the first 1-10 rating value from text."""
    match = re.search(r"\b(10|[1-9])\b", message_text)
    if match is None:
        return None

    return int(match.group(1))


def parse_rating_values(message_text: str) -> list[int]:
    """Parse all 1-10 rating values from text."""
    return [
        int(match)
        for match in re.findall(r"\b(10|[1-9])\b", message_text)
        if 1 <= int(match) <= 10
    ]


def is_not_assessable_rating_answer(message_text: str) -> bool:
    """Return whether the user explicitly refuses a numeric rating."""
    normalized_text = message_text.lower()
    return any(
        phrase in normalized_text
        for phrase in (
            "nicht bewertbar",
            "noch nicht bewertbar",
            "zu früh",
            "zu frueh",
            "too early",
            "not assessable",
            "kann ich nicht bewerten",
        )
    )


def looks_like_rating_answer(message_text: str) -> bool:
    """Return whether text probably contains the combined rating answer."""
    normalized_text = message_text.lower()
    if is_not_assessable_rating_answer(message_text):
        return True

    rating_values = parse_rating_values(message_text)
    if len(rating_values) < len(RATING_FIELDS):
        return False

    return any(
        keyword in normalized_text
        for keyword in (
            "zufriedenheit",
            "attraktiv",
            "priorit",
            "rating",
            "bewertung",
        )
    )


def parse_iso_date(message_text: str) -> date | None:
    """Parse an ISO date from text."""
    match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", message_text)
    if match is None:
        return None

    return date.fromisoformat(match.group(0))


def parse_visit_date(message_text: str) -> date | None:
    """Parse a simple visit or follow-up date from text."""
    parsed_date = parse_iso_date(message_text)
    if parsed_date is not None:
        return parsed_date

    normalized_text = message_text.strip().lower()
    if normalized_text in {"heute", "today"}:
        return date.today()
    if normalized_text in {"gestern", "yesterday"}:
        return date.today() - timedelta(days=1)
    if "nächste woche" in normalized_text or "naechste woche" in normalized_text:
        return date.today() + timedelta(days=7)
    if "in zwei wochen" in normalized_text or "in 2 wochen" in normalized_text:
        return date.today() + timedelta(days=14)

    return None


def is_no_reference_message(message_text: str) -> bool:
    """Return whether text says no offer/order reference exists."""
    normalized_text = message_text.strip().lower()
    if is_none_answer(normalized_text):
        return True
    if normalized_text.startswith(("nee", "nein", "no ")):
        return True

    return mentions_lead(message_text) and not looks_like_reference(normalized_text)


def looks_like_reference(normalized_text: str) -> bool:
    """Return whether text resembles an offer/order reference."""
    reference_pattern = r"\b(?:off|ang|angebot|auftrag|ord)[-_ ]?\d+\b"
    return bool(re.search(reference_pattern, normalized_text))


def mentions_new(normalized_text: str) -> bool:
    """Return whether normalized text indicates new master data."""
    return any(keyword in normalized_text for keyword in ("new", "neu", "unknown"))


def mentions_lead(message_text: str) -> bool:
    """Return whether text explicitly mentions a lead."""
    return "lead" in message_text.lower()


def mentions_inside_sales_follow_up(message_text: str) -> bool:
    """Return whether text requests an inside-sales follow-up."""
    normalized_text = message_text.lower()
    return "innendienst" in normalized_text and any(
        keyword in normalized_text
        for keyword in ("anrufen", "melden", "nachfassen", "follow")
    )


def looks_like_follow_up_action(message_text: str) -> bool:
    """Return whether text likely contains a next action."""
    normalized_text = message_text.lower()
    return any(
        keyword in normalized_text
        for keyword in (
            "wiedervorlage",
            "melden",
            "anrufen",
            "nachfassen",
            "follow-up",
            "follow up",
            "in 2 wochen",
            "in zwei wochen",
            "nächste woche",
            "naechste woche",
        )
    )


def is_unclear_answer(normalized_text: str) -> bool:
    """Return whether normalized text signals uncertainty."""
    return any(
        keyword in normalized_text
        for keyword in ("unclear", "unknown", "not sure", "maybe", "unklar")
    )


def extract_explicit_visit_reason(message_text: str) -> str | None:
    """Extract explicitly stated visit reason/topic from text."""
    patterns = (
        r"\b(?:über|ueber)\s+(?:eine[nmr]?|den|die|das)?\s*(?P<topic>.+?)\s+"
        r"(?:gesprochen|unterhalten|geredet)\b",
        r"\b(?:wegen|zum thema)\s+(?P<topic>[^.?!,;]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, message_text, re.IGNORECASE)
        if match is None:
            continue

        topic = clean_explicit_visit_reason(match.group("topic"))
        if topic:
            return topic

    return None


def clean_explicit_visit_reason(value: str) -> str | None:
    """Clean an extracted visit reason."""
    cleaned_value = re.sub(r"\s+", " ", value).strip(" .,!?:;")
    if not cleaned_value:
        return None

    return cleaned_value[:200]
