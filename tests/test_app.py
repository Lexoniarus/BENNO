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


def test_index_page_is_available() -> None:
    app = create_app("testing")

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    assert b"BENNO" in response.data


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


def test_relative_sqlite_url_uses_instance_folder(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///benno.sqlite3")

    app = create_app("development")

    with app.app_context():
        database_path = Path(db.engine.url.database)

    assert database_path == Path(app.instance_path) / "benno.sqlite3"
