"""Shared pytest fixtures for BENNO tests."""

import pytest

from benno import create_app
from benno.extensions import db


@pytest.fixture()
def app():
    """Create a fresh testing application with an empty database."""
    test_app = create_app("testing")

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()
