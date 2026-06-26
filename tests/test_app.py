"""Tests for the BENNO Flask foundation."""

from flask import Flask

from benno import create_app


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
