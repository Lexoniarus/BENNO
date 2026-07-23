"""Phase 6 report requirement definitions and progress helpers."""

from dataclasses import dataclass
from typing import Any

from benno.enums import ReportSection, ReportStatus, SectionStatus
from benno.models import ReportDraft
from benno.services.report_state import RATING_CLARIFICATIONS_KEY, draft_data

REVIEW_STEP = "review"
OPTIONAL_STEP_KEYS = {"strength_text", "weakness_text", "reminders"}
CONDITIONAL_STEP_KEYS = {
    "next_appointment_date",
    "offer_reference",
    "order_reference",
}
NON_BLOCKING_STEP_KEYS = OPTIONAL_STEP_KEYS | CONDITIONAL_STEP_KEYS
OPTIONAL_REPORT_SECTIONS = {
    ReportSection.STRENGTHS.value,
    ReportSection.WEAKNESSES.value,
    ReportSection.REMINDERS.value,
}
CONDITIONAL_REPORT_SECTIONS = {
    ReportSection.NEXT_APPOINTMENT_DATE.value,
    ReportSection.OFFER_REFERENCE.value,
    ReportSection.ORDER_REFERENCE.value,
}
NON_BLOCKING_REPORT_SECTIONS = OPTIONAL_REPORT_SECTIONS | CONDITIONAL_REPORT_SECTIONS


@dataclass(frozen=True)
class ReportStep:
    """One deterministic question in the Phase 6 report loop."""

    key: str
    section: ReportSection
    question: str
    question_de: str


RATING_FIELDS = (
    ("customer_satisfaction_rating", "customer satisfaction", "Zufriedenheit"),
    (
        "technical_attractiveness_rating",
        "technical attractiveness",
        "Technische Attraktivität",
    ),
    (
        "commercial_attractiveness_rating",
        "commercial attractiveness",
        "Kaufmännische Attraktivität",
    ),
    ("priority_rating", "priority", "Priorität"),
)
BASE_CORRECTION_FIELDS = (
    ("visit_context", "Besuchskontext"),
    ("visit_type", "Besuchsart"),
    ("participants", "Teilnehmer"),
    ("visit_date", "Besuchsdatum"),
    ("target_topic", "Ziel/Thema"),
    ("info_text", "Info"),
    ("agreement_text", "Vereinbarung"),
    ("next_action", "Nächster Schritt"),
    ("next_appointment_date", "Termin ab"),
    ("offer_reference", "Angebotsbezug"),
    ("order_reference", "Auftragsbezug"),
    ("strength_text", "Stärke"),
    ("weakness_text", "Schwäche"),
    ("ratings", "Bewertungen"),
    ("reminders", "Wiedervorlagen"),
)
CORRECTION_FIELDS = BASE_CORRECTION_FIELDS
REQUIREMENT_LABELS = {
    "visit_context": "Besuchskontext",
    "visit_type": "Besuchsart",
    "participants": "Teilnehmer",
    "visit_date": "Besuchsdatum",
    "target_topic": "Ziel/Thema",
    "info_text": "Info",
    "agreement_text": "Vereinbarung",
    "next_action": "Nächster Schritt",
    "next_appointment_date": "Termin ab",
    "offer_reference": "Angebotsbezug",
    "order_reference": "Auftragsbezug",
    "strength_text": "Stärke",
    "weakness_text": "Schwäche",
    "ratings": "Bewertungen",
    "reminders": "Wiedervorlagen",
}

REPORT_STEPS = (
    ReportStep(
        key="visit_context",
        section=ReportSection.CUSTOMER_CONTEXT,
        question="Which AKL account was this visit about?",
        question_de=(
            "Um welchen AKL-Eintrag ging es: Adresse, Kunde oder Lieferant? "
            "Falls es ein neuer Interessent ist, sag das bitte dazu."
        ),
    ),
    ReportStep(
        key="visit_type",
        section=ReportSection.VISIT_TYPE,
        question="Was the visit in person, virtual, or by phone?",
        question_de="War der Besuch persönlich, virtuell oder telefonisch?",
    ),
    ReportStep(
        key="participants",
        section=ReportSection.CONTACTS,
        question="Who participated in the meeting?",
        question_de="Wer hat an dem Gespräch teilgenommen?",
    ),
    ReportStep(
        key="visit_date",
        section=ReportSection.VISIT_DATE,
        question="Was the visit today or on another date?",
        question_de="War der Besuch heute oder an einem anderen Datum?",
    ),
    ReportStep(
        key="target_topic",
        section=ReportSection.VISIT_REASON,
        question="What was the goal or main topic of the visit?",
        question_de="Was war das Ziel oder Hauptthema des Besuchs?",
    ),
    ReportStep(
        key="info_text",
        section=ReportSection.SUMMARY,
        question="What was discussed? You can describe it freely.",
        question_de="Was wurde besprochen? Du kannst es frei erzählen.",
    ),
    ReportStep(
        key="agreement_text",
        section=ReportSection.OUTCOME,
        question="What was agreed or decided?",
        question_de="Was wurde konkret vereinbart oder entschieden?",
    ),
    ReportStep(
        key="next_action",
        section=ReportSection.NEXT_ACTION,
        question="What is the next step, and who should own it?",
        question_de="Was ist der nächste Schritt, und wer soll ihn übernehmen?",
    ),
    ReportStep(
        key="next_appointment_date",
        section=ReportSection.NEXT_APPOINTMENT_DATE,
        question="Is there a concrete follow-up appointment or reminder date?",
        question_de="Gibt es einen konkreten Folgetermin oder Wiedervorlage-Termin?",
    ),
    ReportStep(
        key="offer_reference",
        section=ReportSection.OFFER_REFERENCE,
        question="Is there an offer or offer number? If not, answer 'none'.",
        question_de=(
            "Gibt es dazu ein Angebot oder eine Angebotsnummer? "
            "Falls nicht, antworte mit 'keine'."
        ),
    ),
    ReportStep(
        key="order_reference",
        section=ReportSection.ORDER_REFERENCE,
        question="Is there an order or order number? If not, answer 'none'.",
        question_de=(
            "Gibt es dazu einen Auftrag oder eine Auftragsnummer? "
            "Falls nicht, antworte mit 'keine'."
        ),
    ),
    ReportStep(
        key="strength_text",
        section=ReportSection.STRENGTHS,
        question="Are there notable strengths or positive points?",
        question_de="Gibt es aus deiner Sicht besondere Stärken oder positive Punkte?",
    ),
    ReportStep(
        key="weakness_text",
        section=ReportSection.WEAKNESSES,
        question="Are there risks, objections, or weaknesses to record?",
        question_de=(
            "Gibt es Risiken, Einwände oder Schwächen, "
            "die festgehalten werden sollen?"
        ),
    ),
    ReportStep(
        key="ratings",
        section=ReportSection.RATINGS,
        question=(
            "Rate customer satisfaction, technical attractiveness, commercial "
            "attractiveness, and priority from 1 to 10."
        ),
        question_de=(
            "Wie bewertest du Zufriedenheit, technische Attraktivität, "
            "kaufmännische Attraktivität und Priorität jeweils von 1 bis 10?"
        ),
    ),
    ReportStep(
        key="reminders",
        section=ReportSection.REMINDERS,
        question="Should this create a follow-up reminder?",
        question_de=(
            "Soll daraus eine Wiedervorlage entstehen? Falls ja: für wen, "
            "bis wann und mit welcher Nachricht?"
        ),
    ),
)


def allowed_update_keys() -> list[str]:
    """Return section keys that AI providers may propose."""
    return [step.key for step in REPORT_STEPS] + [
        rating_key for rating_key, _label_en, _label_de in RATING_FIELDS
    ]


def report_requirements(draft: ReportDraft) -> list[dict[str, Any]]:
    """Return the full checklist sent to AI providers."""
    completed_steps = set(draft_data(draft).get("completed_steps", []))
    answers = dict(draft_data(draft).get("answers", {}))
    return [
        {
            "key": step.key,
            "label": REQUIREMENT_LABELS[step.key],
            "status": requirement_status(draft, step, completed_steps, answers),
            "required": requirement_required(step),
            "current_value": requirement_current_value(draft, step, answers),
            "question": requirement_question(draft, step),
            "section": step.section.value,
        }
        for step in REPORT_STEPS
    ]


def requirement_required(step: ReportStep) -> bool:
    """Return whether a step is mandatory for review readiness."""
    return step.key not in NON_BLOCKING_STEP_KEYS


def requirement_status(
    draft: ReportDraft,
    step: ReportStep,
    completed_steps: set[str],
    answers: dict[str, Any],
) -> str:
    """Return one requirement status for AI context."""
    if step.key == "ratings":
        if all_ratings_collected(draft):
            return "completed"
        if draft.ratings_json:
            return "partially_completed"
        return "missing"

    if step.key in {
        "next_appointment_date",
        "offer_reference",
        "order_reference",
        "reminders",
    } and is_none_answer(str(answers.get(step.key, ""))):
        return "not_applicable"

    if step.key in completed_steps:
        return "completed"

    return "missing"


def requirement_current_value(
    draft: ReportDraft,
    step: ReportStep,
    answers: dict[str, Any],
) -> Any:
    """Return the current value for one requirement."""
    if step.key == "ratings":
        return dict(draft.ratings_json) if draft.ratings_json else None

    return answers.get(step.key)


def requirement_question(draft: ReportDraft, step: ReportStep) -> str:
    """Return the current user-facing question for one requirement."""
    if step.section == ReportSection.RATINGS:
        return rating_question(draft)

    return step_question(step, draft.session_language)


def step_by_key(step_key: str) -> ReportStep:
    """Return one report step by key."""
    return next(step for step in REPORT_STEPS if step.key == step_key)


def first_incomplete_step(completed_steps: list[str]) -> ReportStep | None:
    """Return the first mandatory step that is not completed."""
    completed_step_set = set(completed_steps)
    return next(
        (
            step
            for step in REPORT_STEPS
            if step.key not in completed_step_set
            and step.key not in NON_BLOCKING_STEP_KEYS
        ),
        None,
    )


def step_index(step: ReportStep) -> int:
    """Return the deterministic order index for a report step."""
    step_keys = [report_step.key for report_step in REPORT_STEPS]
    return step_keys.index(step.key)


def step_question(step: ReportStep, session_language: str | None) -> str:
    """Return a localized step question."""
    if session_language == "de":
        return step.question_de

    return step.question


def rating_question(draft: ReportDraft) -> str:
    """Return the compact German rating question."""
    missing_labels = missing_rating_labels(draft)
    clarification_summary = rating_clarification_summary(draft)
    if clarification_summary:
        return (
            f"Ich habe verstanden: {clarification_summary}. "
            "Welche Zahlen von 1 bis 10 soll ich für die noch fehlenden "
            "Bewertungen eintragen? Wenn etwas nicht bewertbar ist, sag das "
            "kurz dazu."
        )
    if len(missing_labels) == len(RATING_FIELDS):
        return (
            "Wie bewertest du Zufriedenheit, technische Attraktivität, "
            "kaufmännische Attraktivität und Priorität jeweils von 1 bis 10? "
            "Wenn etwas noch nicht bewertbar ist, sag das kurz dazu."
        )

    if len(missing_labels) == 1:
        return (
            "Eine Bewertung fehlt noch: "
            f"{missing_labels[0]}. Wie schätzt du das von 1 bis 10 ein?"
        )

    return (
        "Ein paar Bewertungen fehlen noch: "
        f"{', '.join(missing_labels)}. Kannst du sie kurz von 1 bis 10 einschätzen?"
    )


def missing_rating_labels(draft: ReportDraft) -> list[str]:
    """Return German labels for missing rating fields."""
    missing_keys = set(missing_rating_keys(draft))
    return [
        label_de
        for rating_key, _label_en, label_de in RATING_FIELDS
        if rating_key in missing_keys
    ]


def rating_clarification_summary(draft: ReportDraft) -> str | None:
    """Return a compact German summary of qualitative rating hints."""
    clarifications = dict(draft_data(draft).get(RATING_CLARIFICATIONS_KEY, {}))
    missing_keys = set(missing_rating_keys(draft))
    parts = [
        f"{label_de}: {clarifications[rating_key]}"
        for rating_key, _label_en, label_de in RATING_FIELDS
        if rating_key in missing_keys and clarifications.get(rating_key)
    ]
    if not parts:
        return None

    return "; ".join(parts)


def initial_section_statuses() -> dict[str, str]:
    """Return initial section statuses for a new report draft."""
    return {
        section.value: SectionStatus.OPEN.value
        for section in ReportSection
        if section != ReportSection.USER_CONFIRMATION
    } | {ReportSection.USER_CONFIRMATION.value: SectionStatus.OPEN.value}


def set_section_status(
    draft: ReportDraft,
    section: ReportSection,
    status: SectionStatus,
) -> None:
    """Set one report section status."""
    section_statuses = dict(draft.section_statuses_json)
    section_statuses[section.value] = status.value
    draft.section_statuses_json = section_statuses


def refresh_missing_sections(draft: ReportDraft) -> None:
    """Refresh missing section keys on a draft."""
    draft.missing_sections_json = missing_sections_for_draft(draft)


def missing_sections(section_statuses: dict[str, str]) -> list[str]:
    """Return missing required report sections."""
    return [
        section
        for section, status in section_statuses.items()
        if status == SectionStatus.OPEN.value
        and section
        not in {
            ReportSection.FINAL_REPORT.value,
            ReportSection.USER_CONFIRMATION.value,
            *NON_BLOCKING_REPORT_SECTIONS,
        }
    ]


def missing_sections_for_draft(draft: ReportDraft) -> list[str]:
    """Return missing required sections for a current draft."""
    missing_section_keys = missing_sections(draft.section_statuses_json)
    if ReportSection.RATINGS.value not in missing_section_keys:
        missing_section_keys.extend(missing_rating_step_keys(draft))

    return missing_section_keys


def missing_step_keys(draft: ReportDraft) -> list[str]:
    """Return missing required report step keys."""
    completed_steps = set(draft_data(draft).get("completed_steps", []))
    return [
        step.key
        for step in REPORT_STEPS
        if step.key not in completed_steps and step.key not in NON_BLOCKING_STEP_KEYS
    ]


def missing_rating_keys(draft: ReportDraft) -> list[str]:
    """Return missing eNVenta rating keys."""
    return [
        rating_key
        for rating_key, _label_en, _label_de in RATING_FIELDS
        if not rating_is_handled(draft.ratings_json.get(rating_key))
    ]


def missing_rating_step_keys(draft: ReportDraft) -> list[str]:
    """Return the synthetic ratings step key when ratings are incomplete."""
    if all_ratings_collected(draft):
        return []

    return ["ratings"]


def all_ratings_collected(draft: ReportDraft) -> bool:
    """Return whether all eNVenta ratings are handled."""
    return all(
        rating_is_handled(draft.ratings_json.get(rating_key))
        for rating_key, _label_en, _label_de in RATING_FIELDS
    )


def rating_is_handled(rating: Any) -> bool:
    """Return whether one rating has a value or explicit not-assessable marker."""
    if not isinstance(rating, dict):
        return False

    value = rating.get("value")
    return isinstance(value, int) or rating.get("not_assessable") is True


def is_ready_for_review(draft: ReportDraft) -> bool:
    """Return whether a draft can be reviewed."""
    return (
        draft.report_status == ReportStatus.READY_FOR_REVIEW.value
        and draft.missing_sections_json == []
    )


def is_none_answer(message_text: str) -> bool:
    """Return whether a text explicitly means no/not applicable."""
    return message_text.strip().lower() in {
        "no",
        "none",
        "not relevant",
        "n/a",
        "na",
        "kein",
        "keine",
        "keiner",
        "nein",
    }
