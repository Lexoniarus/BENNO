"""Admin user management helpers."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta
from hashlib import sha256
from secrets import token_urlsafe

from werkzeug.security import generate_password_hash

from benno.enums import AiProvider, SessionLanguage, UserRole, UserSetupTokenPurpose
from benno.extensions import db
from benno.models import GlobalSetting, User, UserSetupToken, utc_now

TOKEN_TTL_HOURS = 24
MIN_PASSWORD_LENGTH = 8


def create_user_from_form(form_data: Mapping[str, str]) -> User:
    """Create a BENNO user from validated admin form input."""
    user_data = _validated_user_data(form_data)
    _ensure_email_available(user_data["email"])

    user = User(
        email=user_data["email"],
        username=user_data["username"],
        password_hash=generate_password_hash(token_urlsafe(32)),
        role=user_data["role"],
        preferred_language=user_data["preferred_language"],
        ai_provider_override=user_data["ai_provider_override"],
        is_active=user_data["is_active"],
    )
    db.session.add(user)
    db.session.flush()
    return user


def update_user_from_form(user: User, form_data: Mapping[str, str]) -> None:
    """Update a BENNO user from validated admin form input."""
    user_data = _validated_user_data(form_data)
    _ensure_email_available(user_data["email"], current_user=user)

    user.email = user_data["email"]
    user.username = user_data["username"]
    user.role = user_data["role"]
    user.preferred_language = user_data["preferred_language"]
    user.ai_provider_override = user_data["ai_provider_override"]
    user.is_active = user_data["is_active"]


def update_global_settings_from_form(form_data: Mapping[str, str]) -> GlobalSetting:
    """Update or create global admin settings."""
    language = _validated_choice(
        form_data.get("default_language", ""),
        {language.value for language in SessionLanguage},
        "Unbekannte Standardsprache.",
    )
    provider = _validated_choice(
        form_data.get("ai_provider", ""),
        {provider.value for provider in AiProvider},
        "Unbekannter KI-Provider.",
    )

    setting = GlobalSetting.query.order_by(GlobalSetting.id).first()
    if setting is None:
        setting = GlobalSetting()
        db.session.add(setting)

    setting.default_language = language
    setting.ai_provider = provider
    return setting


def create_user_setup_token(
    user: User,
    purpose: UserSetupTokenPurpose,
) -> tuple[UserSetupToken, str]:
    """Create a one-time setup or reset token and return its raw value once."""
    _expire_previous_tokens(user, purpose)
    raw_token = token_urlsafe(32)
    setup_token = UserSetupToken(
        user=user,
        token_hash=hash_setup_token(raw_token),
        purpose=purpose.value,
        expires_at=utc_now() + timedelta(hours=TOKEN_TTL_HOURS),
    )
    db.session.add(setup_token)
    db.session.flush()
    return setup_token, raw_token


def hash_setup_token(raw_token: str) -> str:
    """Hash a raw setup token for lookup and storage."""
    return sha256(raw_token.encode("utf-8")).hexdigest()


def find_valid_setup_token(raw_token: str) -> UserSetupToken | None:
    """Return an unused, non-expired setup token for a raw token value."""
    token_hash = hash_setup_token(raw_token)
    setup_token = UserSetupToken.query.filter_by(token_hash=token_hash).one_or_none()
    if setup_token is None or setup_token.used_at is not None:
        return None

    if _is_expired(setup_token):
        return None

    return setup_token


def set_password_from_token(
    raw_token: str,
    password: str,
    password_confirmation: str,
) -> User:
    """Set a user's password through a valid one-time setup token."""
    setup_token = find_valid_setup_token(raw_token)
    if setup_token is None:
        raise ValueError("Dieser Link ist ungültig oder abgelaufen.")

    if password != password_confirmation:
        raise ValueError("Die Passwörter stimmen nicht überein.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError("Das Passwort muss mindestens 8 Zeichen lang sein.")

    setup_token.user.password_hash = generate_password_hash(password)
    setup_token.user.is_active = True
    setup_token.used_at = utc_now()
    return setup_token.user


def choices_for_admin_forms() -> dict[str, list[tuple[str, str]]]:
    """Return validated choice labels for admin templates."""
    return {
        "languages": [
            (SessionLanguage.DE.value, "Deutsch"),
            (SessionLanguage.EN.value, "Englisch"),
        ],
        "providers": [
            (AiProvider.GEMINI.value, "Gemini"),
            (AiProvider.OPENAI.value, "OpenAI"),
            (AiProvider.LOCAL.value, "Lokal"),
        ],
        "roles": [
            (UserRole.SALES_REP.value, "Vertrieb"),
            (UserRole.ADMIN.value, "Admin"),
        ],
    }


def _validated_user_data(form_data: Mapping[str, str]) -> dict[str, str | bool | None]:
    email = str(form_data.get("email", "")).strip().lower()
    username = str(form_data.get("username", "")).strip()
    if not email or "@" not in email:
        raise ValueError("Bitte gib eine gültige E-Mail-Adresse ein.")

    if not username:
        raise ValueError("Bitte gib einen Namen ein.")

    return {
        "email": email,
        "username": username,
        "role": _validated_choice(
            form_data.get("role", ""),
            {role.value for role in UserRole},
            "Unbekannte Rolle.",
        ),
        "preferred_language": _validated_choice(
            form_data.get("preferred_language", ""),
            {language.value for language in SessionLanguage},
            "Unbekannte Sprache.",
        ),
        "ai_provider_override": _validated_optional_choice(
            form_data.get("ai_provider_override", ""),
            {provider.value for provider in AiProvider},
            "Unbekannter KI-Provider.",
        ),
        "is_active": form_data.get("is_active") == "on",
    }


def _validated_choice(
    value: str | None,
    allowed_values: set[str],
    error_message: str,
) -> str:
    normalized_value = str(value or "").strip()
    if normalized_value not in allowed_values:
        raise ValueError(error_message)

    return normalized_value


def _validated_optional_choice(
    value: str | None,
    allowed_values: set[str],
    error_message: str,
) -> str | None:
    normalized_value = str(value or "").strip()
    if not normalized_value:
        return None

    if normalized_value not in allowed_values:
        raise ValueError(error_message)

    return normalized_value


def _ensure_email_available(
    email: str,
    current_user: User | None = None,
) -> None:
    existing_user = User.query.filter_by(email=email).one_or_none()
    if existing_user is not None and existing_user != current_user:
        raise ValueError("Diese E-Mail-Adresse wird bereits verwendet.")


def _expire_previous_tokens(
    user: User,
    purpose: UserSetupTokenPurpose,
) -> None:
    for setup_token in user.setup_tokens:
        if setup_token.purpose == purpose.value and setup_token.used_at is None:
            setup_token.used_at = utc_now()


def _is_expired(setup_token: UserSetupToken) -> bool:
    expires_at = setup_token.expires_at
    current_time = utc_now()
    if expires_at.tzinfo is None:
        current_time = current_time.replace(tzinfo=None)

    return expires_at <= current_time
