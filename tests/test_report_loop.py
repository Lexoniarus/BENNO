"""Tests for the Phase 6 eNVenta-oriented report loop."""

from datetime import date

from benno.enums import MessageSender, ReportStatus, UserIntent, VisitType
from benno.models import MockReminder, MockVisitReport, User
from benno.seed import seed_database
from benno.services.ai_provider import AiMessageAnalysis, AiProviderError
from benno.services.mock_crm import (
    AccountReference,
    ContactReference,
    CrmUserReference,
    FieldSalesRepresentativeReference,
    ReminderReference,
    VisitReportReference,
)
from benno.services.report_ai_context import ai_message_context
from benno.services.report_loop import (
    build_report_review,
    confirm_report,
    process_report_message_with_ai,
    start_report_chat,
)
from benno.services.report_review import normalize_report_display_text
from benno.services.report_shortcuts import (
    extract_strength_weakness_answers,
    parse_visit_date,
)
from benno.services.report_steps import step_by_key


def test_service_creates_phase_6_chat_draft_and_initial_question(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="laura.schneider@solar-sales.example").one()

    chat = start_report_chat(sales_user)

    assert chat.report_draft is not None
    assert chat.status == ReportStatus.IN_PROGRESS.value
    assert len(chat.messages) == 1
    assert chat.messages[0].sender == MessageSender.ASSISTANT.value
    assert "Laura Schneider" in chat.messages[0].message_text
    assert "Kunden, Lead oder Kontakt" in chat.messages[0].message_text


def test_fresh_ai_context_lists_phase_6_report_requirements(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="laura.schneider@solar-sales.example").one()
    chat = start_report_chat(sales_user)

    context = ai_message_context(chat.report_draft, step_by_key("visit_context"))
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
    sales_user = User.query.filter_by(email="laura.schneider@solar-sales.example").one()
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


def test_visit_type_is_inferred_from_free_visit_context_message(app) -> None:
    seed_database()
    chat = _start_sales_chat()

    process_report_message_with_ai(
        chat,
        (
            "ich war bei einem neuen potenziellen Kunden, die waren voll der "
            "Hammer und haben bock auf uns. Innendienst soll mal ein "
            "Musterangebot fuer ein BalkonSolar erstellen und an Frau Mueller "
            "schicken"
        ),
        _FakeAiService(
            analysis=AiMessageAnalysis(
                intent=UserIntent.ANSWER,
                intent_confidence=0.95,
                target_sections=[
                    "visit_context",
                    "next_action",
                    "offer_reference",
                ],
                section_updates={
                    "visit_context": "neuer potenzieller Kunde",
                    "next_action": (
                        "Innendienst soll Musterangebot fuer BalkonSolar an "
                        "Frau Mueller schicken"
                    ),
                    "offer_reference": "Musterangebot",
                },
            )
        ),
    )

    draft = chat.report_draft
    assert draft.visit_type == VisitType.IN_PERSON.value
    assert draft.draft_data_json["answers"]["visit_type"] == VisitType.IN_PERSON.value
    assert "visit_type" in draft.draft_data_json["completed_steps"]
    assert draft.draft_data_json["current_step"] == "participants"
    assert chat.messages[-1].message_text != (
        "War der Besuch persönlich, virtuell oder telefonisch?"
    )


def test_rating_clues_are_extracted_from_later_bundle_without_ai_rating_update(
    app,
) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="laura.schneider@solar-sales.example").one()
    chat = start_report_chat(sales_user)
    ai_service = _FakeAiService(
        analysis=AiMessageAnalysis(
            intent=UserIntent.ADDITIONAL_INFO,
            intent_confidence=0.95,
            target_sections=[
                "visit_context",
                "visit_type",
                "participants",
                "visit_date",
                "target_topic",
                "info_text",
                "agreement_text",
                "next_action",
                "next_appointment_date",
                "offer_reference",
                "order_reference",
            ],
            section_updates={
                "visit_context": "Solaris Verpackung AG",
                "visit_type": "telefonisch",
                "participants": "Lea Hartmann",
                "visit_date": "heute",
                "target_topic": "Line inspection",
                "info_text": "Linieninspektion besprochen.",
                "agreement_text": "Auswertung und Angebot OFF-24005 senden.",
                "next_action": "Vertrieb meldet sich in zwei Wochen.",
                "next_appointment_date": "keine",
                "offer_reference": "OFF-24005",
                "order_reference": "keiner",
            },
        )
    )

    process_report_message_with_ai(
        chat,
        (
            "Telefonischer Besuch heute bei Solaris mit Lea Hartmann. "
            "Zufriedenheit 8, technische Attraktivitaet 8, "
            "kaufmaennische Attraktivitaet 7, Prioritaet 8."
        ),
        ai_service,
    )

    assert set(chat.report_draft.ratings_json) == {
        "customer_satisfaction_rating",
        "technical_attractiveness_rating",
        "commercial_attractiveness_rating",
        "priority_rating",
    }
    assert chat.report_draft.draft_data_json["current_step"] == "review"


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


def test_explicit_strength_and_weakness_are_extracted_by_rules() -> None:
    answers = extract_strength_weakness_answers(
        "Stärke ist hohes Projektvolumen, Schwäche ist unklare Freigabe."
    )

    assert answers == {
        "strength_text": "hohes Projektvolumen",
        "weakness_text": "unklare Freigabe",
    }


def test_strength_weakness_hint_works_during_rating_step(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    _process_all_required_until_ratings(chat)

    process_report_message_with_ai(
        chat,
        "Stärke ist hohes Projektvolumen, Schwäche ist unklare technische Freigabe.",
        _FakeAiService(),
    )

    draft = chat.report_draft
    answers = draft.draft_data_json["answers"]
    assert answers["strength_text"] == "hohes Projektvolumen"
    assert answers["weakness_text"] == "unklare technische Freigabe"
    assert draft.ratings_json == {}
    assert draft.draft_data_json["current_step"] == "ratings"


def test_strength_weakness_hint_does_not_overwrite_existing_answers(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    _process_all_required_until_ratings(chat)

    process_report_message_with_ai(
        chat,
        "Stärke ist hohes Projektvolumen, Schwäche ist unklare technische Freigabe.",
        _FakeAiService(),
    )
    process_report_message_with_ai(
        chat,
        "Stärke ist anderer Bedarf, Schwäche ist anderer Einwand.",
        _FakeAiService(),
    )

    answers = chat.report_draft.draft_data_json["answers"]
    assert answers["strength_text"] == "hohes Projektvolumen"
    assert answers["weakness_text"] == "unklare technische Freigabe"


def test_confirm_writes_rule_based_strength_and_weakness_to_mock_visit_report(
    app,
) -> None:
    seed_database()
    chat = _start_sales_chat()
    _process_all_required_until_ratings(chat)
    process_report_message_with_ai(
        chat,
        "Stärke ist hohes Projektvolumen, Schwäche ist unklare technische Freigabe.",
        _FakeAiService(),
    )
    process_report_message_with_ai(
        chat,
        "Zufriedenheit 8, technisch 7, kaufmaennisch 6, Prioritaet 9.",
        _FakeAiService(),
    )

    final_report = confirm_report(chat)

    assert final_report.mock_visit_report.strength_text == "hohes Projektvolumen"
    assert final_report.mock_visit_report.weakness_text == (
        "unklare technische Freigabe"
    )


def test_report_display_text_removes_markdown_artifacts() -> None:
    markdown_text = (
        "### Besuchsbericht: Nordlicht\n\n"
        "***\n\n"
        "**Datum:** 22.07.2026\n"
        "* **Naechste Schritte:** Innendienst ruft nach.\n"
    )

    normalized_text = normalize_report_display_text(markdown_text)

    assert "###" not in normalized_text
    assert "**" not in normalized_text
    assert "***" not in normalized_text
    assert normalized_text == (
        "Besuchsbericht: Nordlicht\n\n"
        "Datum: 22.07.2026\n"
        "- Naechste Schritte: Innendienst ruft nach."
    )


def test_review_uses_normalized_ai_text_and_german_visit_type_label(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    _process_complete_report_with_reminder(chat)
    process_report_message_with_ai(chat, "8 7 6 9", _FakeAiService())

    review = build_report_review(
        chat.report_draft,
        _FakeAiService(
            review_text="### Pruefung\n**Alles** passt.",
            final_report_text="### Bericht\n**Besuchsart:** Vor-Ort-Termin",
        ),
    )

    section_values = dict(review["sections"])
    assert section_values["Besuchsart"] == "Vor Ort"
    assert review["review_text"] == "Pruefung\nAlles passt."
    assert review["final_report_text"] == "Bericht\nBesuchsart: Vor-Ort-Termin"


def test_strict_question_answer_flow_reaches_review_without_optional_references(
    app,
) -> None:
    seed_database()
    chat = _start_sales_chat()
    answers = [
        "Nordlicht Maschinenbau GmbH",
        "persoenlich",
        "Mara Stein",
        "2026-07-07",
        "Forecast",
        "Forecast und Lieferfaehigkeit besprochen.",
        "Revidiertes Angebot wird geschickt.",
        "Sales sendet die Unterlagen.",
        "Zufriedenheit 8, technisch 7, kaufmaennisch 6, Prioritaet 9.",
    ]

    for answer in answers:
        process_report_message_with_ai(chat, answer, _FakeAiService())

    final_report = confirm_report(chat)

    assert chat.report_draft.draft_data_json["current_step"] == "review"
    assert final_report.mock_visit_report is not None
    assert final_report.mock_visit_report.target_topic == "Forecast"
    assert chat.status == ReportStatus.CONFIRMED.value


def test_confirm_report_keeps_unmatched_visit_context_as_account_label(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    answers = [
        "SonnenTest GmbH",
        "telefonisch",
        "Frau Becker",
        "2026-07-07",
        "Kooperation",
        "Pilotprojekt und Datenblaetter besprochen.",
        "Unterlagen werden geschickt.",
        "Innendienst soll telefonisch nachfassen.",
        "Zufriedenheit 8, technisch 7, kaufmaennisch 6, Prioritaet 9.",
    ]

    for answer in answers:
        process_report_message_with_ai(chat, answer, _FakeAiService())

    final_report = confirm_report(chat)

    assert final_report.mock_visit_report is not None
    assert final_report.mock_visit_report.account_id is None
    assert final_report.mock_visit_report.account_search_name == "SonnenTest GmbH"


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


def test_german_visit_date_formats_are_accepted() -> None:
    assert parse_visit_date("22.07.2026") == date(2026, 7, 22)
    assert parse_visit_date("22.07.26") == date(2026, 7, 22)
    assert parse_visit_date("22.7.2026") == date(2026, 7, 22)
    assert parse_visit_date("Das Gespräch war heute, am 22.07.2026.") == date(
        2026,
        7,
        22,
    )
    assert parse_visit_date("Das Gespräch war heute.") == date.today()
    assert parse_visit_date("irgendwann letzte Woche") is None


def test_strict_flow_accepts_german_visit_date_and_reaches_review(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    answers = [
        "Nordlicht Maschinenbau GmbH",
        "persoenlich",
        "Mara Stein",
        "22.07.2026",
        "Forecast",
        "Forecast und Lieferfaehigkeit besprochen.",
        "Revidiertes Angebot wird geschickt.",
        "Sales sendet die Unterlagen.",
        "Zufriedenheit 8, technisch 7, kaufmaennisch 6, Prioritaet 9.",
    ]

    for answer in answers:
        process_report_message_with_ai(chat, answer, _FakeAiService())

    assert chat.report_draft.visit_date == date(2026, 7, 22)
    assert chat.report_draft.draft_data_json["current_step"] == "review"


def test_unrelated_conditional_answer_does_not_block_rating_step(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    _process_until_next_appointment_date(chat)

    process_report_message_with_ai(
        chat,
        "Es gibt keinen Auftrag. Staerke: klarer Bedarf.",
        _FakeAiService(),
    )

    draft = chat.report_draft
    assert draft.follow_up_date is not None
    assert draft.draft_data_json["answers"]["next_appointment_date"] == (
        draft.follow_up_date.isoformat()
    )
    assert draft.draft_data_json["answers"]["order_reference"] == "keiner"
    assert draft.draft_data_json["current_step"] == "ratings"


def test_relative_follow_up_date_can_be_stored_without_blocking_flow(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    _process_until_next_appointment_date(chat)

    process_report_message_with_ai(chat, "naechste Woche", _FakeAiService())

    assert chat.report_draft.follow_up_date is not None
    assert chat.report_draft.draft_data_json["answers"]["next_appointment_date"] == (
        chat.report_draft.follow_up_date.isoformat()
    )
    assert chat.report_draft.draft_data_json["current_step"] == "ratings"


def test_conditional_fields_do_not_block_when_no_signal_exists(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    answers = [
        "Nordlicht Maschinenbau GmbH",
        "persoenlich",
        "Mara Stein",
        "2026-07-07",
        "Forecast",
        "Forecast und Lieferfaehigkeit besprochen.",
        "Revidiertes Angebot wird geschickt.",
        "Sales sendet die Unterlagen.",
    ]

    for answer in answers:
        process_report_message_with_ai(chat, answer, _FakeAiService())

    draft_answers = chat.report_draft.draft_data_json["answers"]
    assert "next_appointment_date" not in draft_answers
    assert "offer_reference" not in draft_answers
    assert "order_reference" not in draft_answers
    assert chat.report_draft.draft_data_json["current_step"] == "ratings"


def test_inside_sales_nachfassen_creates_mock_reminder(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    _process_complete_report_with_reminder(chat)

    final_report = confirm_report(chat)

    visit_report = final_report.mock_visit_report
    assert visit_report is not None
    assert len(visit_report.reminders) == 1
    assert "nachfassen" in visit_report.reminders[0].message.lower()


def test_inside_sales_calls_next_week_creates_mock_reminder(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    answers = [
        "Nordlicht Maschinenbau GmbH",
        "persoenlich",
        "Mara Stein",
        "22.07.2026",
        "Forecast",
        "Lieferfaehigkeit und Angebot A-2026-104 besprochen.",
        (
            "Ich sende die Unterlagen, der Innendienst ruft naechste Woche "
            "nach und Mara Stein prueft den Folgeauftrag."
        ),
        "Zufriedenheit 8, technisch 7, kaufmaennisch 6, Prioritaet 9.",
    ]

    for answer in answers:
        process_report_message_with_ai(chat, answer, _FakeAiService())

    final_report = confirm_report(chat)

    visit_report = final_report.mock_visit_report
    assert visit_report is not None
    assert len(visit_report.reminders) == 1
    assert "innendienst ruft naechste woche nach" in (
        visit_report.reminders[0].message.lower()
    )


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


def test_report_loop_can_use_injected_crm_gateway(app) -> None:
    seed_database()
    chat = _start_sales_chat()
    crm_gateway = _FakeCrmGateway()

    _process_complete_report_with_gateway(chat, crm_gateway)
    final_report = confirm_report(chat, crm_gateway=crm_gateway)

    references = chat.report_draft.draft_data_json["crm_references"]
    assert references["account"]["account_number"] == "FAKE-AKL-1"
    assert references["contact"]["full_name"] == "Frau Gateway"
    assert final_report.account_id == 1
    assert crm_gateway.saved_visit_report_payload["account_number"] == "FAKE-AKL-1"
    assert crm_gateway.saved_visit_report_payload["contact_name"] == "Frau Gateway"
    assert crm_gateway.created_reminder_payload["message"]


def _start_sales_chat():
    sales_user = User.query.filter_by(email="laura.schneider@solar-sales.example").one()
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


def _process_until_next_appointment_date(chat) -> None:
    answers = [
        "Nordlicht Maschinenbau GmbH",
        "persoenlich",
        "Mara Stein",
        "2026-07-07",
        "Forecast",
        "Forecast und Lieferfaehigkeit besprochen.",
        "Revidiertes Angebot wird geschickt.",
        "Innendienst soll naechste Woche nachfassen.",
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


def _process_complete_report_with_gateway(chat, crm_gateway) -> None:
    answers = [
        "Gateway Kunde",
        "telefonisch",
        "Frau Gateway",
        "2026-07-07",
        "Gateway Test",
        "Wir haben die Gateway-Grenze besprochen.",
        "BENNO soll den Connector sauber nutzen.",
        "Innendienst soll naechste Woche nachfassen.",
        "2026-07-14",
        "keine",
        "keine",
        "8 7 6 9",
    ]
    for answer in answers:
        process_report_message_with_ai(
            chat,
            answer,
            _FakeAiService(),
            crm_gateway,
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


class _FakeCrmGateway:
    def __init__(self) -> None:
        self.saved_visit_report_payload = None
        self.created_reminder_payload = None

    def search_accounts(
        self,
        query: str,
        account_type: str | None = None,
    ) -> list[AccountReference]:
        if "Gateway Kunde" not in query:
            return []

        return [
            AccountReference(
                id=1,
                account_number="FAKE-AKL-1",
                account_type="K",
                search_name="GATEWAY",
                display_name="Gateway Kunde GmbH",
            )
        ]

    def find_contacts(
        self,
        account_id: int,
        query: str | None = None,
    ) -> list[ContactReference]:
        if query != "Frau Gateway":
            return []

        return [
            ContactReference(
                id=1,
                account_id=account_id,
                full_name="Frau Gateway",
            )
        ]

    def find_offers(self, account_id: int, query: str | None = None) -> list:
        return []

    def find_orders(self, account_id: int, query: str | None = None) -> list:
        return []

    def list_crm_users(self, query: str | None = None) -> list[CrmUserReference]:
        return [
            CrmUserReference(
                id=1,
                username="inside.sales",
                display_name="Inside Sales",
            )
        ]

    def list_field_sales_representatives(
        self,
        query: str | None = None,
    ) -> list[FieldSalesRepresentativeReference]:
        return [
            FieldSalesRepresentativeReference(
                id=1,
                representative_number="REP-FAKE",
                display_name="Gateway Rep",
            )
        ]

    def save_visit_report(
        self,
        final_report_id: int,
        payload: dict,
    ) -> VisitReportReference:
        self.saved_visit_report_payload = payload
        return VisitReportReference(
            id=100,
            visit_report_number="VR-GATEWAY-1",
        )

    def create_reminder(
        self,
        visit_report_number: str,
        payload: dict,
    ) -> ReminderReference:
        self.created_reminder_payload = payload
        return ReminderReference(
            id=200,
            visit_report_number=visit_report_number,
            message=payload["message"],
            due_date=payload.get("due_date"),
        )
