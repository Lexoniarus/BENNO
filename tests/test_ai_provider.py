"""Tests for BENNO AI provider configuration."""

from benno import create_app
from benno.enums import UserIntent
from benno.services.ai_provider import (
    AiProviderError,
    NullAiService,
    get_ai_service,
    get_ai_status,
)
from benno.services.gemini_provider import (
    ANALYSIS_SYSTEM_INSTRUCTION,
    NEXT_QUESTION_SYSTEM_INSTRUCTION,
    GeminiMessageAnalysis,
    GeminiSectionUpdate,
    _build_analysis_content,
    _build_next_question_prompt,
    _convert_gemini_analysis,
)


def test_default_gemini_model_is_configured() -> None:
    app = create_app("testing")

    assert app.config["AI_PROVIDER"] == "gemini"
    assert app.config["GEMINI_MODEL"] == "gemini-3.1-flash-lite"


def test_development_configuration_reads_gemini_environment(monkeypatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")

    app = create_app("development")

    assert app.config["AI_PROVIDER"] == "gemini"
    assert app.config["GEMINI_API_KEY"] == "test-gemini-key"
    assert app.config["GEMINI_MODEL"] == "gemini-test-model"


def test_testing_configuration_does_not_create_real_ai_service(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    app = create_app("testing")

    with app.app_context():
        ai_service = get_ai_service()

    assert isinstance(ai_service, NullAiService)


def test_provider_initialization_error_returns_null_service(app, monkeypatch) -> None:
    def raise_provider_error(self, api_key: str, model: str) -> None:
        raise AiProviderError("fake initialization failure")

    monkeypatch.setattr(
        "benno.services.gemini_provider.GeminiService.__init__",
        raise_provider_error,
    )
    app.config["GEMINI_API_KEY"] = "test-gemini-key"

    with app.app_context():
        ai_service = get_ai_service()

    assert isinstance(ai_service, NullAiService)
    assert app.config["AI_PROVIDER_LAST_ERROR"] == "Initialisierung fehlgeschlagen"


def test_ai_status_shows_missing_gemini_sdk(app, monkeypatch) -> None:
    app.config["GEMINI_API_KEY"] = "test-gemini-key"

    monkeypatch.setattr(
        "benno.services.ai_provider.importlib.util.find_spec",
        lambda module_name: None if module_name == "google.genai" else object(),
    )

    with app.app_context():
        status = get_ai_status()

    assert status == {
        "label": "KI: Gemini / gemini-3.1-flash-lite SDK fehlt",
        "state": "inactive",
    }


def test_ai_status_shows_provider_initialization_error(app, monkeypatch) -> None:
    def raise_provider_error(self, api_key: str, model: str) -> None:
        raise AiProviderError("fake initialization failure")

    monkeypatch.setattr(
        "benno.services.gemini_provider.GeminiService.__init__",
        raise_provider_error,
    )
    app.config["GEMINI_API_KEY"] = "test-gemini-key"

    with app.app_context():
        get_ai_service()
        status = get_ai_status()

    assert status == {
        "label": (
            "KI: Gemini / gemini-3.1-flash-lite nicht verfügbar "
            "(Initialisierung fehlgeschlagen)"
        ),
        "state": "inactive",
    }


def test_gemini_section_update_list_converts_to_internal_dict() -> None:
    gemini_analysis = GeminiMessageAnalysis(
        intent=UserIntent.ADDITIONAL_INFO,
        intent_confidence=0.93,
        target_sections=["visit_context", "participants", "target_topic"],
        section_updates=[
            GeminiSectionUpdate(section="visit_context", value="PerfSolar"),
            GeminiSectionUpdate(section="participants", value="Frau Müller"),
            GeminiSectionUpdate(section="target_topic", value="Forecast"),
        ],
        suggested_next_section="info_text",
        suggested_next_question="Was wurde besprochen?",
    )

    analysis = _convert_gemini_analysis(gemini_analysis)

    assert analysis.intent == UserIntent.ADDITIONAL_INFO
    assert analysis.intent_confidence == 0.93
    assert analysis.section_updates == {
        "visit_context": "PerfSolar",
        "participants": "Frau Müller",
        "target_topic": "Forecast",
    }
    assert analysis.suggested_next_section == "info_text"
    assert analysis.suggested_next_question == "Was wurde besprochen?"


def test_gemini_section_update_conversion_ignores_malformed_empty_values() -> None:
    gemini_analysis = GeminiMessageAnalysis(
        section_updates=[
            GeminiSectionUpdate(section="participants", value="Frau Schmidt"),
            GeminiSectionUpdate(section="participants", value=""),
            GeminiSectionUpdate(section="participants", value="Herr Walther"),
            GeminiSectionUpdate(section=None, value="No section"),
            GeminiSectionUpdate(section="info_text", value=None),
        ],
    )

    analysis = _convert_gemini_analysis(gemini_analysis)

    assert analysis.section_updates == {"participants": "Herr Walther"}


def test_gemini_analysis_uses_system_instruction_separate_from_content() -> None:
    content = _build_analysis_content(
        {"current_step": "visit_context"},
        "Ich war bei PerfSolar.",
    )

    assert "You support BENNO" in ANALYSIS_SYSTEM_INSTRUCTION
    assert "extractor and observer role" in ANALYSIS_SYSTEM_INSTRUCTION
    assert "Context:" in content
    assert "Ich war bei PerfSolar." in content
    assert "You support BENNO" not in content


def test_gemini_next_question_prompt_uses_conversation_system_instruction() -> None:
    prompt = _build_next_question_prompt(
        {
            "next_step": "participants",
            "known_answers": {"visit_context": "PerfSolar"},
        }
    )

    assert "conversation role" in NEXT_QUESTION_SYSTEM_INSTRUCTION
    assert "Use next_step as the target" in NEXT_QUESTION_SYSTEM_INSTRUCTION
    assert "Validated conversation state:" in prompt
    assert "PerfSolar" in prompt
