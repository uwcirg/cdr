from flask.ext.testing import TestCase as Base

from cdr import create_app
from cdr.config import TestConfig
from cdr.extensions import db


class TestCase(Base):
    """Base TestClass for your application."""

    def create_app(self):
        """Create and return a testing flask app."""
        app = create_app(TestConfig)
        return app

    def init_data(self):
        pass

    def setUp(self):
        """Reset all tables before testing."""
        self.init_data()

    def tearDown(self):
        """Clean db session and drop all tables."""
        #db.drop_all()

    def _test_get_request(self, endpoint, template=None):
        response = self.client.get(endpoint)
        self.assert_200(response)
        if template:
            self.assertTemplateUsed(name=template)
        return response
