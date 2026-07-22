"""Tests for BENNO database CLI commands."""

from benno.enums import AiProvider, UserRole
from benno.extensions import db
from benno.models import (
    GlobalSetting,
    MockAccount,
    MockCrmUser,
    MockFieldSalesRepresentative,
    User,
)


def test_init_db_command_runs_successfully(app) -> None:
    runner = app.test_cli_runner()

    result = runner.invoke(args=["init-db"])

    assert result.exit_code == 0
    assert "Initialized the BENNO database." in result.output


def test_seed_db_command_creates_demo_data_without_duplicates(app) -> None:
    runner = app.test_cli_runner()

    first_result = runner.invoke(args=["seed-db"])
    second_result = runner.invoke(args=["seed-db"])

    assert first_result.exit_code == 0
    assert second_result.exit_code == 0
    assert db.session.query(User).filter_by(role=UserRole.ADMIN.value).count() == 1
    assert db.session.query(User).filter_by(role=UserRole.SALES_REP.value).count() == 4
    assert db.session.query(GlobalSetting).one().ai_provider == AiProvider.GEMINI.value
    assert db.session.query(MockAccount).count() == 6
    assert db.session.query(MockCrmUser).count() == 2
    assert db.session.query(MockFieldSalesRepresentative).count() == 4


def test_seed_db_command_initializes_missing_tables(app) -> None:
    runner = app.test_cli_runner()
    db.drop_all()

    result = runner.invoke(args=["seed-db"])

    assert result.exit_code == 0
    assert "Seeded the BENNO database." in result.output
    assert db.session.query(User).count() == 5
    assert db.session.query(MockAccount).count() == 6


def test_reset_db_command_recreates_seeded_database(app) -> None:
    runner = app.test_cli_runner()
    db.session.add(
        MockAccount(
            account_number="TEMP-ACCOUNT",
            account_type="K",
            search_name="TEMP",
            display_name="Temporary Account",
        )
    )
    db.session.commit()

    result = runner.invoke(args=["reset-db", "--yes"])

    assert result.exit_code == 0
    assert "Reset and seeded the BENNO database." in result.output
    assert (
        db.session.query(MockAccount)
        .filter_by(display_name="Temporary Account")
        .count()
        == 0
    )
    assert db.session.query(MockAccount).count() == 6
