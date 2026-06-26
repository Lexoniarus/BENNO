"""Tests for BENNO database CLI commands."""

from benno.enums import UserRole
from benno.extensions import db
from benno.models import MockCustomer, User


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
    assert db.session.query(User).filter_by(role=UserRole.SALES_REP.value).count() == 1
    assert db.session.query(MockCustomer).count() == 4


def test_reset_db_command_recreates_seeded_database(app) -> None:
    runner = app.test_cli_runner()
    db.session.add(
        MockCustomer(
            external_customer_id="TEMP-CUSTOMER",
            name="Temporary Customer",
        )
    )
    db.session.commit()

    result = runner.invoke(args=["reset-db", "--yes"])

    assert result.exit_code == 0
    assert "Reset and seeded the BENNO database." in result.output
    assert (
        db.session.query(MockCustomer).filter_by(name="Temporary Customer").count() == 0
    )
    assert db.session.query(MockCustomer).count() == 4
