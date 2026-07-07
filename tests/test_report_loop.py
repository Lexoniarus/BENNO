"""Tests for the Phase 6 eNVenta-oriented report loop."""

from benno.enums import MessageSender, ReportStatus, UserIntent, VisitType
from benno.models import MockReminder, MockVisitReport, User
from benno.seed import seed_database
from benno.services.ai_provider import AiMessageAnalysis, AiProviderError
from benno.services.report_loop import (
    _ai_message_context,
    _step_by_key,
    build_report_review,
    confirm_report,
    process_report_message_with_ai,
    start_report_chat,
)


def test_service_creates_phase_6_chat_draft_and_initial_question(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()

    chat = start_report_chat(sales_user)

    assert chat.report_draft is not None
    assert chat.status == ReportStatus.IN_PROGRESS.value
    assert len(chat.messages) == 1
    assert chat.messages[0].sender == MessageSender.ASSISTANT.value
    assert "BENNO Sales Rep" in chat.messages[0].message_text
    assert "Kunden, Lead oder Kontakt" in chat.messages[0].message_text


def test_fresh_ai_context_lists_phase_6_report_requirements(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    chat = start_report_chat(sales_user)

    context = _ai_message_context(chat.report_draft, _step_by_key("visit_context"))
    requirements = context["report_requirements"]
    requirement_keys = {requirement["key"] for requirement in requirements}

    assert {
        "visit_context",
        "visit_type",
        "participants",
        "visit_date",
        "target_topic",
        "info_text",
        "agreement_text",
        "next_action",
        "ratings",
    }.issubset(requirement_keys)
    assert _requirement_from(requirements, "strength_text")["required"] is False
    assert _requirement_from(requirements, "offer_reference")["required"] is False
    assert _requirement_from(requirements, "ratings")["status"] == "missing"


def test_ai_analysis_can_fill_multiple_phase_6_sections_from_one_message(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    chat = start_report_chat(sales_user)
    ai_service = _FakeAiService(
        analysis=AiMessageAnalysis(
            intent=UserIntent.ADDITIONAL_INFO,
            intent_confidence=0.95,
            target_sections=[
                "visit_context",
                "visit_type",
                "participants",
                "target_topic",
            ],
            section_updates={
                "visit_context": "Nordlicht Maschinenbau GmbH",
                "visit_type": "persönlich",
                "participants": "Mara Stein",
                "target_topic": "Forecast",
            },
            suggested_next_section="visit_date",
            suggested_next_question="War der Besuch heute oder an einem anderen Datum?",
        )
    )

    visit_message = (
        "Ich war persönlich bei Nordlicht und habe mit Mara Stein "
        "über den Forecast gesprochen."
    )
    process_report_message_with_ai(chat, visit_message, ai_service)

    draft = chat.report_draft
    answers = draft.draft_data_json["answers"]
    assert ai_service.analysis_calls == 1
    assert answers["visit_context"] == "Nordlicht Maschinenbau GmbH"
    assert answers["participants"] == "Mara Stein"
    assert answers["target_topic"] == "Forecast"
    assert draft.visit_type == VisitType.IN_PERSON.value
    assert draft.account.account_number == "AKL-K-1001"
    assert draft.contact.full_name == "Mara Stein"
    assert draft.draft_data_json["current_step"] == "visit_date"
    assert chat.messages[-1].message_text == (
        "War der Besuch heute oder an einem anderen Datum?"
    )


def test_four_enventa_ratings_complete_rating_section(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    _process_all_required_until_ratings(chat)

    process_report_message_with_ai(
        chat,
        "Zufriedenheit 8, technisch 7, kaufmännisch 6, Priorität 9.",
        _FakeAiService(
            analysis=AiMessageAnalysis(
                intent=UserIntent.ANSWER,
                intent_confidence=0.9,
                target_sections=["ratings"],
                section_updates={
                    "ratings": (
                        "Zufriedenheit 8, technisch 7, " "kaufmännisch 6, Priorität 9."
                    )
                },
            )
        ),
    )

    ratings = chat.report_draft.ratings_json
    assert set(ratings) == {
        "customer_satisfaction_rating",
        "technical_attractiveness_rating",
        "commercial_attractiveness_rating",
        "priority_rating",
    }
    assert ratings["priority_rating"]["value"] == 9
    assert chat.report_draft.draft_data_json["current_step"] == "review"


def test_partial_rating_answer_keeps_rating_step_open(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    _process_all_required_until_ratings(chat)

    process_report_message_with_ai(chat, "Zufriedenheit 8", _FakeAiService())

    draft = chat.report_draft
    assert draft.ratings_json["customer_satisfaction_rating"]["value"] == 8
    assert "technical_attractiveness_rating" not in draft.ratings_json
    assert draft.draft_data_json["current_step"] == "ratings"


def test_not_assessable_rating_answer_can_complete_rating_step(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    _process_all_required_until_ratings(chat)

    process_report_message_with_ai(
        chat,
        "Alle vier Bewertungen sind noch nicht bewertbar.",
        _FakeAiService(),
    )

    ratings = chat.report_draft.ratings_json
    assert all(rating["not_assessable"] is True for rating in ratings.values())
    assert chat.report_draft.draft_data_json["current_step"] == "review"


def test_unclear_visit_type_does_not_default_to_in_person(app) -> None:
    seed_database()
    chat = _start_sales_chat()

    process_report_message_with_ai(
        chat, "Nordlicht Maschinenbau GmbH", _FakeAiService()
    )
    process_report_message_with_ai(chat, "weiss ich gerade nicht", _FakeAiService())

    assert chat.report_draft.visit_type is None
    assert chat.report_draft.draft_data_json["current_step"] == "visit_type"


def test_unclear_visit_date_does_not_default_to_today(app) -> None:
    seed_database()
    chat = _start_sales_chat()

    for answer in ["Nordlicht Maschinenbau GmbH", "persoenlich", "Mara Stein"]:
        process_report_message_with_ai(chat, answer, _FakeAiService())
    process_report_message_with_ai(chat, "irgendwann letzte Woche", _FakeAiService())

    assert chat.report_draft.visit_date is None
    assert chat.report_draft.draft_data_json["current_step"] == "visit_date"


def test_lead_without_offer_or_order_skips_document_reference_questions(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    _process_until_offer_reference(chat)

    process_report_message_with_ai(
        chat,
        "nee die sind Lead, da gibt es noch kein Angebot oder Auftrag",
        _FakeAiService(
            analysis=AiMessageAnalysis(
                intent=UserIntent.ANSWER,
                intent_confidence=0.88,
                target_sections=[],
                section_updates={},
            )
        ),
    )

    answers = chat.report_draft.draft_data_json["answers"]
    assert answers["offer_reference"] == "keiner"
    assert answers["order_reference"] == "keiner"
    assert chat.report_draft.customer_context_type == "new_lead"
    assert chat.report_draft.draft_data_json["current_step"] == "ratings"


def test_confirm_report_creates_mock_visit_report_and_reminder(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    _process_complete_report_with_reminder(chat)

    final_report = confirm_report(chat)

    mock_visit_report = MockVisitReport.query.filter_by(
        final_report_id=final_report.id
    ).one()
    reminder = MockReminder.query.filter_by(
        visit_report_number=mock_visit_report.visit_report_number
    ).one()
    assert mock_visit_report.target_topic == "Forecast"
    assert mock_visit_report.info_text == "Forecast und Lieferfähigkeit besprochen."
    assert mock_visit_report.agreement_text == "Revidiertes Angebot wird geschickt."
    assert mock_visit_report.priority_rating == 9
    assert reminder.message
    assert chat.status == ReportStatus.CONFIRMED.value


def test_review_shows_enventa_target_sections(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    _process_complete_report_with_reminder(chat)

    review = build_report_review(chat.report_draft)
    labels = [label for label, _value in review["sections"]]

    assert "Ziel/Thema" in labels
    assert "Info" in labels
    assert "Vereinbarung" in labels
    assert "Stärke" in labels
    assert "Schwäche" in labels
    assert "Wiedervorlagen" in labels


def test_provider_error_falls_back_to_deterministic_flow(app) -> None:
    seed_database()
    chat = _start_sales_chat()

    process_report_message_with_ai(
        chat,
        "Nordlicht Maschinenbau GmbH",
        _FakeAiService(analysis_error=AiProviderError("fake provider failure")),
    )

    assert chat.report_draft.draft_data_json["answers"]["visit_context"] == (
        "Nordlicht Maschinenbau GmbH"
    )
    assert chat.report_draft.draft_data_json["last_ai_error"] == (
        "message_analysis_failed"
    )


def _start_sales_chat():
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    return start_report_chat(sales_user)


def _process_all_required_until_ratings(chat) -> None:
    answers = [
        "Nordlicht Maschinenbau GmbH",
        "persönlich",
        "Mara Stein",
        "2026-07-07",
        "Forecast",
        "Forecast und Lieferfähigkeit besprochen.",
        "Revidiertes Angebot wird geschickt.",
        "Innendienst soll nächste Woche nachfassen.",
        "2026-07-14",
        "OFF-24001",
        "keine",
    ]
    for answer in answers:
        process_report_message_with_ai(chat, answer, _FakeAiService())


def _process_until_offer_reference(chat) -> None:
    answers = [
        "Neuer Lead SunSolar",
        "telefonisch",
        "Herr Walther",
        "2026-07-07",
        "Erstkontakt",
        "Vorstellung der Systeme.",
        "Werbematerial zusenden.",
        "Innendienst soll anrufen.",
        "keine",
    ]
    for answer in answers:
        process_report_message_with_ai(chat, answer, _FakeAiService())


def _process_complete_report_with_reminder(chat) -> None:
    _process_all_required_until_ratings(chat)
    process_report_message_with_ai(
        chat,
        "8 7 6 9",
        _FakeAiService(
            analysis=AiMessageAnalysis(
                intent=UserIntent.ANSWER,
                intent_confidence=0.95,
                target_sections=["ratings", "strength_text", "weakness_text"],
                section_updates={
                    "ratings": "8 7 6 9",
                    "strength_text": "Guter Bedarf und konstruktive Stimmung.",
                    "weakness_text": "Budgetfreigabe ist noch offen.",
                    "reminders": "Innendienst soll nächste Woche nachfassen.",
                },
            )
        ),
    )


def _requirement_from(
    requirements: list[dict[str, object]],
    requirement_key: str,
) -> dict[str, object]:
    return next(
        requirement
        for requirement in requirements
        if requirement["key"] == requirement_key
    )


class _FakeAiService:
    def __init__(
        self,
        analysis: AiMessageAnalysis | None = None,
        review_text: str | None = None,
        final_report_text: str | None = None,
        analysis_error: AiProviderError | None = None,
    ) -> None:
        self.analysis = analysis
        self.review_text = review_text
        self.final_report_text = final_report_text
        self.analysis_error = analysis_error
        self.analysis_calls = 0
        self.next_question_calls = 0
        self.review_calls = 0
        self.final_report_calls = 0
        self.last_analysis_context = None

    def analyze_report_message(
        self,
        context,
        message_text: str,
    ) -> AiMessageAnalysis | None:
        self.analysis_calls += 1
        self.last_analysis_context = context
        if self.analysis_error is not None:
            raise self.analysis_error

        return self.analysis

    def draft_next_question(self, question_context) -> str | None:
        self.next_question_calls += 1
        return None

    def draft_review_text(self, draft_context) -> str | None:
        self.review_calls += 1
        return self.review_text

    def draft_final_report_text(self, draft_context) -> str | None:
        self.final_report_calls += 1
        return self.final_report_text
