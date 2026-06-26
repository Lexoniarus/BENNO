"""Application factory for BENNO."""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from benno.config import CONFIG_BY_NAME, DevelopmentConfig
from benno.extensions import db
from benno.routes import main_blueprint


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the BENNO Flask application."""
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    _configure_app(app, config_name)
    _ensure_instance_folder(app)
    _initialize_extensions(app)
    _register_blueprints(app)

    return app


def _configure_app(app: Flask, config_name: str | None) -> None:
    selected_name = config_name or os.environ.get("BENNO_ENV", "development")
    config_class = CONFIG_BY_NAME.get(str(selected_name), DevelopmentConfig)
    app.config.from_object(config_class)
    _configure_secret_key(app)
    _configure_database(app)


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

    database_path = Path(app.instance_path) / "benno.sqlite3"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path.as_posix()}"


def _ensure_instance_folder(app: Flask) -> None:
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)


def _initialize_extensions(app: Flask) -> None:
    db.init_app(app)


def _register_blueprints(app: Flask) -> None:
    app.register_blueprint(main_blueprint)
