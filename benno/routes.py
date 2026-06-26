"""Main routes for the BENNO foundation."""

from flask import Blueprint, render_template

main_blueprint = Blueprint("main", __name__)


@main_blueprint.get("/")
def index() -> str:
    """Render the BENNO start screen."""
    return render_template("index.html")


@main_blueprint.get("/health")
def health() -> tuple[dict[str, str], int]:
    """Return a small health response for smoke tests."""
    return {"status": "ok", "service": "benno"}, 200
