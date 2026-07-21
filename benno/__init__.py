"""Application factory for BENNO."""

import importlib
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from benno.cli import register_cli_commands
from benno.config import CONFIG_BY_NAME, DevelopmentConfig
from benno.extensions import db, login_manager
from benno.routes import main_blueprint

LOCAL_DATABASE_FILENAME = "benno-dev.sqlite3"


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the BENNO Flask application."""
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    _configure_app(app, config_name)
    _ensure_instance_folder(app)
    _load_models()
    _initialize_extensions(app)
    _register_blueprints(app)
    _register_cli(app)

    return app


def _configure_app(app: Flask, config_name: str | None) -> None:
    selected_name = config_name or os.environ.get("BENNO_ENV", "development")
    config_class = CONFIG_BY_NAME.get(str(selected_name), DevelopmentConfig)
    app.config.from_object(config_class)
    _configure_ai(app)
    _configure_langfuse(app)
    _configure_secret_key(app)
    _configure_database(app)


def _configure_ai(app: Flask) -> None:
    if app.config.get("TESTING"):
        return

    configured_provider = os.environ.get("AI_PROVIDER")
    if configured_provider:
        app.config["AI_PROVIDER"] = configured_provider

    configured_gemini_key = os.environ.get("GEMINI_API_KEY")
    if configured_gemini_key:
        app.config["GEMINI_API_KEY"] = configured_gemini_key

    configured_gemini_model = os.environ.get("GEMINI_MODEL")
    if configured_gemini_model:
        app.config["GEMINI_MODEL"] = configured_gemini_model


def _configure_langfuse(app: Flask) -> None:
    if app.config.get("TESTING"):
        return

    _configure_boolean_from_env(app, "LANGFUSE_ENABLED")
    _configure_boolean_from_env(app, "LANGFUSE_CAPTURE_FULL_CONTEXT")
    _configure_boolean_from_env(app, "LANGFUSE_FLUSH_ON_TURN")
    for key in (
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_BASE_URL",
        "LANGFUSE_HOST",
    ):
        configured_value = os.environ.get(key)
        if configured_value:
            app.config[key] = configured_value

    if app.config.get("LANGFUSE_HOST"):
        return
    if not app.config.get("LANGFUSE_BASE_URL"):
        return

    app.config["LANGFUSE_HOST"] = app.config["LANGFUSE_BASE_URL"]
    os.environ["LANGFUSE_HOST"] = app.config["LANGFUSE_BASE_URL"]


def _configure_boolean_from_env(app: Flask, key: str) -> None:
    configured_value = os.environ.get(key)
    if configured_value is None:
        return

    app.config[key] = configured_value.strip().lower() in {"1", "true", "yes", "on"}


def _configure_secret_key(app: Flask) -> None:
    configured_secret_key = os.environ.get("SECRET_KEY")
    if configured_secret_key:
        app.config["SECRET_KEY"] = configured_secret_key


def _configure_database(app: Flask) -> None:
    configured_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if configured_uri:
        return

    configured_uri = os.environ.get("DATABASE_URL")
    if configured_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = configured_uri
        return

    database_path = _project_root() / LOCAL_DATABASE_FILENAME
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path.as_posix()}"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ensure_instance_folder(app: Flask) -> None:
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)


def _load_models() -> None:
    importlib.import_module("benno.models")


def _initialize_extensions(app: Flask) -> None:
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    _register_user_loader()


def _register_blueprints(app: Flask) -> None:
    from benno.admin import admin_blueprint
    from benno.auth import auth_blueprint
    from benno.sales import sales_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(sales_blueprint)


def _register_user_loader() -> None:
    from benno.models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        if not user_id.isdigit():
            return None

        return db.session.get(User, int(user_id))


def _register_cli(app: Flask) -> None:
    register_cli_commands(app)
