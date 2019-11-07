import os
import pytest

from cdr import create_app
from cdr.config import TestConfig, TESTDB_PATH
from cdr.extensions import mdb as _mdb, sdb as _sdb


@pytest.fixture
def client(request):
    app = create_app(TestConfig)
    client = app.test_client()

    if os.path.exists(TESTDB_PATH):
        os.unlink(TESTDB_PATH)

    with app.app_context():
        _sdb.app = app
        _sdb.create_all()
        yield client

    def teardown_mdb():
        """Clean mongo db session and drop all tables."""
        db_name = app.config['MONGODB_SETTINGS']['DB']
        assert ('test' in db_name)
        with app.app_context():
            _mdb.connection.drop_database(db_name)

    def teardown_sdb():
        """Clean SQL db session and drop all tables."""
        with app.app_context():
            _sdb.drop_all()
        os.unlink(TESTDB_PATH)

    request.addfinalizer(teardown_mdb)
    request.addfinalizer(teardown_sdb)
