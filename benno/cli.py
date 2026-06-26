"""Command line helpers for BENNO."""

import click
from flask import Flask, current_app

from benno.extensions import db


def register_cli_commands(app: Flask) -> None:
    """Register BENNO database commands."""

    @app.cli.command("init-db")
    def init_db_command() -> None:
        """Create all configured database tables."""
        db.create_all()
        click.echo("Initialized the BENNO database.")

    @app.cli.command("seed-db")
    def seed_db_command() -> None:
        """Create or update local demo data."""
        from benno.seed import seed_database

        db.create_all()
        seed_database()
        click.echo("Seeded the BENNO database.")

    @app.cli.command("reset-db")
    @click.option(
        "--yes",
        is_flag=True,
        help="Confirm that the local database may be dropped and recreated.",
    )
    def reset_db_command(yes: bool) -> None:
        """Drop, recreate, and seed the local development database."""
        if not yes and not current_app.testing:
            raise click.ClickException("Use --yes to confirm local database reset.")

        from benno.seed import seed_database

        db.drop_all()
        db.create_all()
        seed_database()
        click.echo("Reset and seeded the BENNO database.")
