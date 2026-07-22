"""Tests for the BENNO Flask foundation."""

from pathlib import Path

from flask import Flask

from benno import create_app
from benno.extensions import db


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_report_form_script_adds_pending_typing_state() -> None:
    script_text = (_project_root() / "benno" / "static" / "js" / "app.js").read_text(
        encoding="utf-8"
    )
    user_pending_call = (
        'addChatMessage("user", messageText.toString(), "chat-message--pending")'
    )
    assistant_typing_call = (
        'addChatMessage("assistant", "BENNO analysiert", "chat-message--typing")'
    )

    assert user_pending_call in script_text
    assert assistant_typing_call in script_text
    assert 'reportForm.setAttribute("aria-busy", "true")' in script_text


def test_voice_script_marks_dynamic_assistant_replies_for_speech() -> None:
    script_text = (_project_root() / "benno" / "static" / "js" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "article.dataset.assistantMessage" in script_text
    assert "article.dataset.speechUrl = options.speechUrl" in script_text
    assert "payload.assistant_speech_url" in script_text
    assert "payload.tts_error || !payload.audio" in script_text
    assert "stopVoiceMode();" in script_text
    assert "maxPlaybackWaitMs" in script_text
    assert "Ich höre zu. Sprich deine Antwort." in script_text


def test_voice_script_supports_report_chat_autostart() -> None:
    script_text = (_project_root() / "benno" / "static" / "js" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "dataset.voiceAutoStart" in script_text
    assert "startVoiceMode({ auto: true })" in script_text
    assert 'sessionStorage.setItem(storageKey, "true")' in script_text
    assert "sessionStorage.removeItem(storageKey)" in script_text
    assert "Automatischer Sprachstart wurde blockiert." in script_text


def test_report_chat_css_reserves_space_for_sticky_composer() -> None:
    css_text = (_project_root() / "benno" / "static" / "css" / "app.css").read_text(
        encoding="utf-8"
    )

    assert "padding: 20px 20px 180px;" in css_text
    assert "scroll-padding-bottom: 180px;" in css_text
    assert "padding: 14px 14px 260px;" in css_text
    assert "scroll-padding-bottom: 260px;" in css_text


def test_create_app_uses_testing_configuration() -> None:
    app = create_app("testing")

    assert isinstance(app, Flask)
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
    assert app.config["VOICE_MAX_UPLOAD_BYTES"] == 10_485_760
    assert app.config["VOICE_TTS_CACHE_DIR"] == "instance/voice_cache"
    assert app.config["VOICE_TTS_CACHE_ENABLED"] is True
    assert app.config["VOICE_TTS_MAX_SNIPPET_CHARS"] == 180
    assert app.config["VOICE_TTS_PREWARM_ENABLED"] is True


def test_index_redirects_anonymous_users_to_login() -> None:
    app = create_app("testing")

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 302
    assert response.location == "/login"


def test_health_endpoint_returns_ok_status() -> None:
    app = create_app("testing")

    with app.test_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"service": "benno", "status": "ok"}


def test_favicon_route_redirects_to_local_logo() -> None:
    app = create_app("testing")

    with app.test_client() as client:
        response = client.get("/favicon.ico")

    assert response.status_code == 302
    assert response.location == "/static/img/benno-logo.svg"


def test_development_configuration_reads_environment_at_app_creation(
    monkeypatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///custom.sqlite3")
    monkeypatch.setenv("SECRET_KEY", "custom-secret-key")

    app = create_app("development")

    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///custom.sqlite3"
    assert app.config["SECRET_KEY"] == "custom-secret-key"


def test_development_configuration_reads_langfuse_environment(monkeypatch) -> None:
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://langfuse.test")
    monkeypatch.setenv("LANGFUSE_CAPTURE_FULL_CONTEXT", "true")
    monkeypatch.setenv("LANGFUSE_FLUSH_ON_TURN", "true")

    app = create_app("development")

    assert app.config["LANGFUSE_ENABLED"] is True
    assert app.config["LANGFUSE_PUBLIC_KEY"] == "pk-test"
    assert app.config["LANGFUSE_SECRET_KEY"] == "sk-test"
    assert app.config["LANGFUSE_BASE_URL"] == "https://langfuse.test"
    assert app.config["LANGFUSE_HOST"] == "https://langfuse.test"
    assert app.config["LANGFUSE_CAPTURE_FULL_CONTEXT"] is True
    assert app.config["LANGFUSE_FLUSH_ON_TURN"] is True


def test_development_configuration_reads_voice_upload_limit(monkeypatch) -> None:
    monkeypatch.setenv("VOICE_MAX_UPLOAD_BYTES", "2048")

    app = create_app("development")

    assert app.config["VOICE_MAX_UPLOAD_BYTES"] == 2048


def test_development_configuration_reads_voice_tts_cache_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv("VOICE_TTS_CACHE_ENABLED", "false")
    monkeypatch.setenv("VOICE_TTS_PREWARM_ENABLED", "false")
    monkeypatch.setenv("VOICE_TTS_CACHE_DIR", "instance/test-voice-cache")
    monkeypatch.setenv("VOICE_TTS_MAX_SNIPPET_CHARS", "96")

    app = create_app("development")

    assert app.config["VOICE_TTS_CACHE_ENABLED"] is False
    assert app.config["VOICE_TTS_PREWARM_ENABLED"] is False
    assert app.config["VOICE_TTS_CACHE_DIR"] == "instance/test-voice-cache"
    assert app.config["VOICE_TTS_MAX_SNIPPET_CHARS"] == 96


def test_default_development_database_uses_project_root(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "")

    app = create_app("development")

    with app.app_context():
        database_path = Path(db.engine.url.database)

    assert database_path == _project_root() / "benno-dev.sqlite3"


def test_default_development_database_ignores_current_working_directory(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.chdir(tmp_path)

    app = create_app("development")

    with app.app_context():
        database_path = Path(db.engine.url.database)

    assert database_path == _project_root() / "benno-dev.sqlite3"
