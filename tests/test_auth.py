"""Tests for BENNO authentication and role routing."""

from werkzeug.security import check_password_hash, generate_password_hash

from benno.enums import SessionLanguage, UserRole
from benno.extensions import db
from benno.models import User
from benno.seed import seed_database


def test_login_page_loads(app) -> None:
    with app.test_client() as client:
        response = client.get("/login")

    assert response.status_code == 200
    assert b"BENNO" in response.data
    assert b"img/benno-favicon.svg" in response.data
    assert b"img/benno-favicon-32.png" in response.data
    assert b"img/benno-apple-touch-icon.png" in response.data
    assert b"img/benno-logo.svg" in response.data


def test_logo_asset_is_available(app) -> None:
    with app.test_client() as client:
        response = client.get("/static/img/benno-logo.svg")

    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"


def test_favicon_asset_is_available(app) -> None:
    with app.test_client() as client:
        response = client.get("/static/img/benno-favicon-32.png")

    assert response.status_code == 200
    assert response.mimetype == "image/png"


def test_apple_touch_icon_asset_is_available(app) -> None:
    with app.test_client() as client:
        response = client.get("/static/img/benno-apple-touch-icon.png")

    assert response.status_code == 200
    assert response.mimetype == "image/png"


def test_valid_admin_login_redirects_to_admin_dashboard(app) -> None:
    seed_database()

    with app.test_client() as client:
        response = _login(client, "admin@solar-sales.local", "Admin123")

    assert response.status_code == 302
    assert response.location == "/admin"


def test_seed_database_updates_admin_password_and_creates_sales_reps(app) -> None:
    old_admin = User(
        email="admin@solar-sales.local",
        username="Old Admin",
        password_hash=generate_password_hash("admin-demo-password"),
        role=UserRole.ADMIN.value,
        preferred_language=SessionLanguage.DE.value,
        is_active=True,
    )
    db.session.add(old_admin)
    db.session.commit()

    seed_database()

    admin = User.query.filter_by(email="admin@solar-sales.local").one()
    sales_users = User.query.filter_by(role=UserRole.SALES_REP.value).all()

    assert admin.username == "Nina Hartmann"
    assert check_password_hash(admin.password_hash, "Admin123")
    assert {user.email: user.external_sales_rep_id for user in sales_users} == {
        "laura.schneider@solar-sales.example": "REP-001",
        "markus.weber@solar-sales.example": "REP-002",
        "sophie.klein@solar-sales.example": "REP-003",
        "tobias.fischer@solar-sales.example": "REP-004",
    }


def test_valid_sales_login_redirects_to_sales_dashboard(app) -> None:
    seed_database()

    with app.test_client() as client:
        response = _login(client, "laura.schneider@solar-sales.example", "Sales123")

    assert response.status_code == 302
    assert response.location == "/sales"


def test_root_redirects_logged_in_admin_to_admin_dashboard(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client, "admin@solar-sales.local", "Admin123")
        response = client.get("/")

    assert response.status_code == 302
    assert response.location == "/admin"


def test_root_redirects_logged_in_sales_user_to_sales_dashboard(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client, "laura.schneider@solar-sales.example", "Sales123")
        response = client.get("/")

    assert response.status_code == 302
    assert response.location == "/sales"


def test_wrong_password_stays_on_login_with_controlled_error(app) -> None:
    seed_database()

    with app.test_client() as client:
        response = _login(
            client,
            "laura.schneider@solar-sales.example",
            "wrong-password",
        )

    assert response.status_code == 200
    assert "E-Mail oder Passwort ist ungültig.".encode() in response.data


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
    assert "E-Mail oder Passwort ist ungültig.".encode() in response.data


def test_logout_clears_access(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client, "laura.schneider@solar-sales.example", "Sales123")
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
        _login(client, "laura.schneider@solar-sales.example", "Sales123")
        response = client.get("/admin")

    assert response.status_code == 403


def test_admin_user_cannot_access_sales_pages(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client, "admin@solar-sales.local", "Admin123")
        response = client.get("/sales")

    response_text = response.get_data(as_text=True)

    assert response.status_code == 403
    assert "Zugriff nicht erlaubt" in response_text
    assert "Zurück zum Start" in response_text


def _login(client, email: str, password: str):
    return client.post(
        "/login",
        data={"email": email, "password": password},
    )
