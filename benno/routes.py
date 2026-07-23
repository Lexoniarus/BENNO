"""Main routes for the BENNO foundation."""

from flask import Blueprint, redirect, url_for
from flask_login import current_user

from benno.enums import UserRole

main_blueprint = Blueprint("main", __name__)


@main_blueprint.get("/")
def index():
    """Route users to the correct BENNO entry point."""
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))

    if current_user.role == UserRole.ADMIN.value:
        return redirect(url_for("admin.dashboard"))

    return redirect(url_for("sales.dashboard"))


@main_blueprint.get("/health")
def health() -> tuple[dict[str, str], int]:
    """Return a small health response for smoke tests."""
    return {"status": "ok", "service": "benno"}, 200


@main_blueprint.get("/favicon.ico")
def favicon():
    """Redirect browsers to BENNO's local PNG favicon asset."""
    return redirect(url_for("static", filename="img/benno-favicon-32.png"))
