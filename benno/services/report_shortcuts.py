"""Deterministic fallback parsing for the report workflow."""

import re
from datetime import date, timedelta

from benno.enums import ReasonCode, VisitType
from benno.services.report_steps import RATING_FIELDS, is_none_answer

RATING_LABEL_PATTERNS = {
    "customer_satisfaction_rating": (
        r"zufriedenheit",
        r"zufrieden",
    ),
    "technical_attractiveness_rating": (
        r"technische?\s+attraktivit[aä]t",
        r"technisch(?:e|er|en)?",
    ),
    "commercial_attractiveness_rating": (
        r"kaufm[aä]nnische?\s+attraktivit[aä]t",
        r"kaufmaennische?\s+attraktivit[aä]t",
        r"kaufm[aä]nnisch(?:e|er|en)?",
        r"kaufmaennisch(?:e|er|en)?",
        r"kommerziell(?:e|er|en)?",
    ),
    "priority_rating": (
        r"priorit[aä]t",
        r"prioritaet",
    ),
}


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
    if match is not None:
        return int(match.group(1))

    normalized_text = message_text.lower()
    spoken_values = {
        "eins": 1,
        "zwei": 2,
        "drei": 3,
        "vier": 4,
        "fuenf": 5,
        "fünf": 5,
        "sechs": 6,
        "sieben": 7,
        "acht": 8,
        "neun": 9,
        "zehn": 10,
        "zähn": 10,
        "zaehn": 10,
    }
    for word, value in spoken_values.items():
        if re.search(rf"\b{re.escape(word)}\b", normalized_text):
            return value

    return None


def parse_rating_values(message_text: str) -> list[int]:
    """Parse all 1-10 rating values from text."""
    numeric_values = [
        int(match)
        for match in re.findall(r"\b(10|[1-9])\b", message_text)
        if 1 <= int(match) <= 10
    ]
    if numeric_values:
        return numeric_values

    value = parse_rating_value(message_text)
    return [value] if value is not None else []


def parse_labeled_rating_values(message_text: str) -> dict[str, int]:
    """Parse rating values that are explicitly tied to eNVenta rating labels."""
    parsed_values = {}
    for rating_key, segment in _labeled_rating_segments(message_text).items():
        value = parse_rating_value(segment)
        if value is not None:
            parsed_values[rating_key] = value

    return parsed_values


def parse_labeled_rating_clarifications(message_text: str) -> dict[str, str]:
    """Extract qualitative rating hints that still need numeric confirmation."""
    clarifications = {}
    for rating_key, segment in _labeled_rating_segments(message_text).items():
        if parse_rating_value(segment) is not None:
            continue

        clarification = _clean_rating_clarification(segment)
        if clarification is not None:
            clarifications[rating_key] = clarification

    return clarifications


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
    if parse_labeled_rating_clarifications(message_text):
        return True
    if parse_labeled_rating_values(message_text):
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


def _labeled_rating_segments(message_text: str) -> dict[str, str]:
    markers = _rating_label_markers(message_text)
    segments = {}
    for index, marker in enumerate(markers):
        next_start = (
            markers[index + 1]["start"]
            if index + 1 < len(markers)
            else len(message_text)
        )
        segment = message_text[int(marker["end"]) : int(next_start)]
        segments[str(marker["key"])] = segment

    return segments


def _rating_label_markers(message_text: str) -> list[dict[str, int | str]]:
    markers = []
    for rating_key, patterns in RATING_LABEL_PATTERNS.items():
        rating_marker = None
        for pattern in patterns:
            match = re.search(pattern, message_text, re.IGNORECASE)
            if match is not None:
                rating_marker = {
                    "key": rating_key,
                    "start": match.start(),
                    "end": match.end(),
                }
                break
        if rating_marker is not None:
            markers.append(rating_marker)

    return sorted(markers, key=lambda marker: int(marker["start"]))


def _clean_rating_clarification(segment: str) -> str | None:
    cleaned_value = re.sub(r"\s+", " ", segment).strip(" \t\r\n,.;:-")
    cleaned_value = re.sub(
        r"^(?:ist|war|sind|waren|ja|also)\s+",
        "",
        cleaned_value,
        flags=re.IGNORECASE,
    )
    cleaned_value = re.sub(
        r"\s+und\s+(?:die|der|das)?$",
        "",
        cleaned_value,
        flags=re.IGNORECASE,
    )
    if len(cleaned_value) < 3:
        return None
    if not _contains_qualitative_rating_signal(cleaned_value):
        return None

    return cleaned_value[:180]


def _contains_qualitative_rating_signal(text: str) -> bool:
    normalized_text = text.lower()
    return any(
        keyword in normalized_text
        for keyword in (
            "attraktiv",
            "durchaus",
            "gut",
            "heiß",
            "heiss",
            "hoch",
            "interessiert",
            "kohle",
            "positiv",
            "potential",
            "potenzial",
            "recht",
            "schwach",
            "stark",
            "unerfahren",
            "unklar",
            "unsicher",
            "zufrieden",
        )
    )


def extract_strength_weakness_answers(message_text: str) -> dict[str, str]:
    """Extract explicitly stated strength and weakness notes."""
    markers = _explicit_strength_weakness_markers(message_text)
    if not markers:
        return {}

    answers = {}
    for index, marker in enumerate(markers):
        next_start = (
            markers[index + 1]["start"]
            if index + 1 < len(markers)
            else len(message_text)
        )
        value = _clean_strength_weakness_value(message_text[marker["end"] : next_start])
        if value:
            answers[marker["key"]] = value

    return answers


def _explicit_strength_weakness_markers(
    message_text: str,
) -> list[dict[str, int | str]]:
    marker_specs = (
        (
            "strength_text",
            r"\b(?:st[äa]rke|staerke|st[äa]rken|staerken|positiv|"
            r"positive punkte|pluspunkt|pluspunkte)\b"
            r"\s*(?:ist|sind|war|waren|:|-)?",
        ),
        (
            "weakness_text",
            r"\b(?:schw[äa]che|schwaeche|schw[äa]chen|schwaechen|"
            r"risiko|risiken|einwand|einw[äa]nde|einwaende|negativ)\b"
            r"\s*(?:ist|sind|war|waren|:|-)?",
        ),
    )
    markers = []
    for key, pattern in marker_specs:
        for match in re.finditer(pattern, message_text, re.IGNORECASE):
            markers.append({"key": key, "start": match.start(), "end": match.end()})

    return sorted(markers, key=lambda marker: int(marker["start"]))


def _clean_strength_weakness_value(value: str) -> str | None:
    cleaned_value = re.sub(r"\s+", " ", value).strip(" \t\r\n,.;:-")
    if not cleaned_value:
        return None

    cleaned_value = re.sub(r"^(?:und|aber|noch)\s+", "", cleaned_value, flags=re.I)
    return cleaned_value[:500]


def parse_iso_date(message_text: str) -> date | None:
    """Parse an ISO date from text."""
    match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", message_text)
    if match is None:
        return None

    return date.fromisoformat(match.group(0))


def parse_german_date(message_text: str) -> date | None:
    """Parse a German date from free text."""
    match = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2}|\d{4})\b", message_text)
    if match is None:
        return None

    day = int(match.group(1))
    month = int(match.group(2))
    year = int(match.group(3))
    if year < 100:
        year += 2000

    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_visit_date(message_text: str) -> date | None:
    """Parse a simple visit or follow-up date from text."""
    parsed_date = parse_iso_date(message_text)
    if parsed_date is not None:
        return parsed_date

    parsed_date = parse_german_date(message_text)
    if parsed_date is not None:
        return parsed_date

    normalized_text = message_text.strip().lower()
    if "heute" in normalized_text or "today" in normalized_text:
        return date.today()
    if "gestern" in normalized_text or "yesterday" in normalized_text:
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
    if any(
        phrase in normalized_text
        for phrase in (
            "kein angebot",
            "keine angebot",
            "keinen auftrag",
            "kein auftrag",
            "keine auftragsnummer",
            "keine angebotsnummer",
            "no offer",
            "no order",
        )
    ):
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
    return re.search(r"\b(?:new|neu|unknown)\b", normalized_text) is not None


def mentions_lead(message_text: str) -> bool:
    """Return whether text explicitly mentions a lead."""
    normalized_text = message_text.lower()
    return any(
        keyword in normalized_text
        for keyword in (
            "lead",
            "interessent",
            "potenzieller kunde",
            "potentieller kunde",
            "prospect",
        )
    )


def mentions_inside_sales_follow_up(message_text: str) -> bool:
    """Return whether text requests an inside-sales follow-up."""
    normalized_text = message_text.lower()
    owner_signal = any(
        keyword in normalized_text
        for keyword in (
            "indienst",
            "in den dienst",
            "in die dienst",
            "inendienst",
            "innen dienst",
            "innendienst",
            "sachbearbeiter",
            "inside sales",
        )
    )
    action_signal = any(
        keyword in normalized_text
        for keyword in (
            "anrufen",
            "ruft",
            "melden",
            "nachfassen",
            "nachhaken",
            "kontaktieren",
            "follow",
        )
    )
    return owner_signal and action_signal


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
