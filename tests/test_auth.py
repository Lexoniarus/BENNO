"""Tests for BENNO authentication and role routing."""

from werkzeug.security import generate_password_hash

from benno.enums import SessionLanguage, UserRole
from benno.extensions import db
from benno.models import User
from benno.seed import seed_database


def test_login_page_loads(app) -> None:
    with app.test_client() as client:
        response = client.get("/login")

    assert response.status_code == 200
    assert b"BENNO" in response.data


def test_valid_admin_login_redirects_to_admin_dashboard(app) -> None:
    seed_database()

    with app.test_client() as client:
        response = _login(client, "admin@benno.local", "admin-demo-password")

    assert response.status_code == 302
    assert response.location == "/admin"


def test_valid_sales_login_redirects_to_sales_dashboard(app) -> None:
    seed_database()

    with app.test_client() as client:
        response = _login(client, "sales@benno.local", "sales-demo-password")

    assert response.status_code == 302
    assert response.location == "/sales"


def test_root_redirects_logged_in_admin_to_admin_dashboard(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client, "admin@benno.local", "admin-demo-password")
        response = client.get("/")

    assert response.status_code == 302
    assert response.location == "/admin"


def test_root_redirects_logged_in_sales_user_to_sales_dashboard(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client, "sales@benno.local", "sales-demo-password")
        response = client.get("/")

    assert response.status_code == 302
    assert response.location == "/sales"


def test_wrong_password_stays_on_login_with_controlled_error(app) -> None:
    seed_database()

    with app.test_client() as client:
        response = _login(client, "sales@benno.local", "wrong-password")

    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


def test_inactive_user_cannot_log_in(app) -> None:
    inactive_user = User(
        email="inactive@example.invalid",
        username="Inactive User",
        password_hash=generate_password_hash("secret"),
        role=UserRole.SALES_REP.value,
        preferred_language=SessionLanguage.DE.value,
        is_active=False,
    )
    db.session.add(inactive_user)
    db.session.commit()

    with app.test_client() as client:
        response = _login(client, "inactive@example.invalid", "secret")

    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


def test_logout_clears_access(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client, "sales@benno.local", "sales-demo-password")
        logout_response = client.get("/logout")
        protected_response = client.get("/sales")

    assert logout_response.status_code == 302
    assert logout_response.location == "/login"
    assert protected_response.status_code == 302
    assert protected_response.location.startswith("/login")


def test_anonymous_access_to_protected_pages_redirects_to_login(app) -> None:
    with app.test_client() as client:
        admin_response = client.get("/admin")
        sales_response = client.get("/sales")

    assert admin_response.status_code == 302
    assert admin_response.location.startswith("/login")
    assert sales_response.status_code == 302
    assert sales_response.location.startswith("/login")


def test_sales_user_cannot_access_admin_pages(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client, "sales@benno.local", "sales-demo-password")
        response = client.get("/admin")

    assert response.status_code == 403


def test_admin_user_cannot_access_sales_pages(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client, "admin@benno.local", "admin-demo-password")
        response = client.get("/sales")

    assert response.status_code == 403


def _login(client, email: str, password: str):
    return client.post(
        "/login",
        data={"email": email, "password": password},
    )
