from unittest import TestCase
from server import app
from model import connect_to_db, db, example_data


class FlaskTestsBasic(TestCase):
    """ Flask Tests"""

    def setUp(self):
        """ Things to do before every test."""

        # Get the Flask test client
        self.client = app.test_client()

        # Show Flask errors that happen during tests
        app.config['TESTING'] = True

    def test_homepage(self):
        """Test homepage page."""

        result = self.client.get("/")
        self.assertIn("Welcome", result.data)

    def test_registration_form(self):
        """Test registration form page."""

        result = self.client.get("/register")
        self.assertIn("Register Here", result.data)

    def test_login_form(self):
        """ Test log in form page."""

        result = self.client.get("/login")
        self.assertIn("Log In Here", result.data)


class FlaskTestsDatabase(TestCase):
    """Flask tests that use the database."""

    def setUp(self):
        """ Things to do before every test."""

        # Get the Flask test client
        self.client = app.test_client()
        app.config['TESTING'] = True

        # Connect to test database
        connect_to_db(app, "postgresql:///testfood")

        # Create tables and add sample data
        db.create_all()
        example_data()

    def tearDown(self):
        """ Things to do after every test."""

        db.session.close()
        db.drop_all()

    def test_new_registration(self):
        """ Test new user registration."""

        new_user = self.client.post("/register",
                                  data={"username": "sandy", "password": "123"},
                                  follow_redirects=True)
        self.assertIn("Log In Here", new_user.data)

    def test_duplicate_registration(self):
        """ Test duplicate user registration."""

        duplicate_user = self.client.post("/register",
                                  data={"username": "tom", "password": "123"},
                                  follow_redirects=True)
        self.assertIn("Register Here", duplicate_user.data)


if __name__ == "__main__":
    import unittest

    unittest.main()
