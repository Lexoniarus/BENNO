"""Tests for BENNO AI provider configuration."""

from benno import create_app
from benno.services.ai_provider import NullAiService, get_ai_service


def test_default_gemini_model_is_configured() -> None:
    app = create_app("testing")

    assert app.config["AI_PROVIDER"] == "gemini"
    assert app.config["GEMINI_MODEL"] == "gemini-2.5-flash-lite"


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
