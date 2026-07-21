"""Tests for the BENNO Flask foundation."""

from pathlib import Path

from flask import Flask

from benno import create_app
from benno.extensions import db


def test_create_app_uses_testing_configuration() -> None:
    app = create_app("testing")

    assert isinstance(app, Flask)
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"


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


def test_relative_sqlite_url_uses_instance_folder(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///benno.sqlite3")

    app = create_app("development")

    with app.app_context():
        database_path = Path(db.engine.url.database)

    assert database_path == Path(app.instance_path) / "benno.sqlite3"
