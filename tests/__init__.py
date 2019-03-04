import pytest

from cdr import create_app
from cdr.config import TestConfig
from cdr.extensions import db


@pytest.fixture
def client():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        yield client

    """Clean db session and drop all tables."""
    db_name = app.config['MONGODB_SETTINGS']['DB']
    assert ('test' in db_name)
    with app.app_context():
        db.connection.drop_database(db_name)
