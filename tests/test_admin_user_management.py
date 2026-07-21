"""Tests for Phase 8 admin user management."""

from datetime import timedelta

from werkzeug.security import check_password_hash

from benno.enums import AiProvider, SessionLanguage, UserRole, UserSetupTokenPurpose
from benno.extensions import db
from benno.models import GlobalSetting, User, UserSetupToken, utc_now
from benno.seed import seed_database
from benno.services.admin_users import create_user_setup_token


def test_admin_can_create_user_and_receive_setup_link(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client)
        response = client.post(
            "/admin/users/new",
            data={
                "email": "new.sales@example.invalid",
                "username": "New Sales",
                "role": UserRole.SALES_REP.value,
                "preferred_language": SessionLanguage.DE.value,
                "ai_provider_override": "",
                "is_active": "on",
            },
        )

    created_user = User.query.filter_by(email="new.sales@example.invalid").one()
    setup_token = UserSetupToken.query.filter_by(user_id=created_user.id).one()
    assert response.status_code == 200
    assert b"/setup/" in response.data
    assert b"Setup-Link" in response.data
    assert setup_token.purpose == UserSetupTokenPurpose.SETUP.value
    assert setup_token.used_at is None


def test_admin_can_edit_user_role_language_status_and_provider(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()

    with app.test_client() as client:
        _login(client)
        response = client.post(
            f"/admin/users/{sales_user.id}/edit",
            data={
                "email": "sales.changed@example.invalid",
                "username": "Changed Sales",
                "role": UserRole.ADMIN.value,
                "preferred_language": SessionLanguage.EN.value,
                "ai_provider_override": AiProvider.LOCAL.value,
            },
        )

    assert response.status_code == 302
    assert sales_user.email == "sales.changed@example.invalid"
    assert sales_user.username == "Changed Sales"
    assert sales_user.role == UserRole.ADMIN.value
    assert sales_user.preferred_language == SessionLanguage.EN.value
    assert sales_user.ai_provider_override == AiProvider.LOCAL.value
    assert sales_user.is_active is False


def test_setup_link_sets_password_and_marks_token_used(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    _, raw_token = create_user_setup_token(
        sales_user,
        UserSetupTokenPurpose.RESET,
    )
    db.session.commit()

    with app.test_client() as client:
        response = client.post(
            f"/setup/{raw_token}",
            data={
                "password": "fresh-password",
                "password_confirmation": "fresh-password",
            },
        )

    setup_token = UserSetupToken.query.filter_by(user_id=sales_user.id).one()
    assert response.status_code == 302
    assert response.location == "/login"
    assert setup_token.used_at is not None
    assert check_password_hash(sales_user.password_hash, "fresh-password")


def test_expired_setup_link_is_rejected(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    setup_token, raw_token = create_user_setup_token(
        sales_user,
        UserSetupTokenPurpose.RESET,
    )
    setup_token.expires_at = utc_now() - timedelta(hours=1)
    db.session.commit()

    with app.test_client() as client:
        response = client.post(
            f"/setup/{raw_token}",
            data={
                "password": "fresh-password",
                "password_confirmation": "fresh-password",
            },
        )

    assert response.status_code == 200
    assert "ungültig oder abgelaufen".encode() in response.data
    assert not check_password_hash(sales_user.password_hash, "fresh-password")


def test_used_setup_link_is_rejected(app) -> None:
    seed_database()
    sales_user = User.query.filter_by(email="sales@benno.local").one()
    setup_token, raw_token = create_user_setup_token(
        sales_user,
        UserSetupTokenPurpose.RESET,
    )
    setup_token.used_at = utc_now()
    db.session.commit()

    with app.test_client() as client:
        response = client.get(f"/setup/{raw_token}")

    assert response.status_code == 200
    assert "ungültig oder abgelaufen".encode() in response.data


def test_admin_can_update_global_language_and_provider(app) -> None:
    seed_database()

    with app.test_client() as client:
        _login(client)
        response = client.post(
            "/admin/settings",
            data={
                "default_language": SessionLanguage.EN.value,
                "ai_provider": AiProvider.LOCAL.value,
            },
        )

    global_setting = GlobalSetting.query.one()
    assert response.status_code == 302
    assert global_setting.default_language == SessionLanguage.EN.value
    assert global_setting.ai_provider == AiProvider.LOCAL.value


def _login(client) -> None:
    client.post(
        "/login",
        data={
            "email": "admin@benno.local",
            "password": "admin-demo-password",
        },
    )
