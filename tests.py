from unittest import TestCase
from server import app
from model import connect_to_db, db, example_data, User, UserRecipe, Recipe, ShoppingList
import os


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

    def test_not_logged_in_main(self):
        """ Test redirect from main to index page when not logged in."""

        result = self.client.get("/main")
        self.assertIn("Sign Up", result.data)


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

        result = self.client.post("/register",
                                  data={"username": "sandy", "password": "123"},
                                  follow_redirects=True)
        self.assertIn("Log In Here", result.data)

    def test_duplicate_registration(self):
        """ Test duplicate user registration."""

        result = self.client.post("/register",
                                  data={"username": "tom", "password": "123"},
                                  follow_redirects=True)
        self.assertIn("Register Here", result.data)


class FlaskTestsLoggedIn(TestCase):
    """Flask tests that use the database and session."""

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

        # Create a session
        app.config['SECRET_KEY'] = os.environ["testing_secret_key"]

        with self.client as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

    def tearDown(self):
        """ Things to do after every test."""

        db.session.remove()
        db.drop_all()

    def test_successful_login(self):
        """ Test successful user login."""

        result = self.client.post("/login",
                                  data={"username": "tom", "password": "123"},
                                  follow_redirects=True)
        self.assertIn("Main Page", result.data)

    def test_wrong_password_login(self):
        """ Test unsuccessful user login with wrong password."""

        result = self.client.post("/login",
                                  data={"username": "tom", "password": "456"},
                                  follow_redirects=True)
        self.assertIn("Log In Here", result.data)

    def test_unregistered_login(self):
        """ Test unsuccessful user login with unregistered user."""

        result = self.client.post("/login",
                                  data={"username": "sam", "password": "123"},
                                  follow_redirects=True)
        self.assertIn("Log In Here", result.data)

    def test_new_search_form(self):
        """ Test new search form page."""

        result = self.client.get("/new_search")
        self.assertIn('<select name="diet">', result.data)
        self.assertIn('value="Find New Recipe(s)', result.data)

    def test_user_repr(self):
        """ Test representation of a user."""

        sally = User.query.filter(User.username == "sally").one()
        assert sally.__repr__() == '<User user_id=1 username=sally>'

    def test_get_current_inventory(self):
        """ Test user's current inventory."""

        current_user = User.query.get(1)
        self.assertEqual(current_user.get_current_inventory(), [(5.0, 'ounces', 'apple')])

    def test_user_recipe_repr(self):
        """ Test representation of a user recipe."""

        user_recipe = UserRecipe.query.filter(UserRecipe.user_id == 1).first()
        assert user_recipe.__repr__() == '<UserRecipe user_id=1 recipe_id=1 status=needs_ingredients>'

    def test_recipe_repr(self):
        """ Test representation of a recipe."""

        recipe = Recipe.query.get(1)
        assert recipe.__repr__() == '<Recipe recipe_id=1>'

    def test_shopping_list_repr(self):
        """ Test representation of a shopping list."""

        shopping_list = ShoppingList.query.filter(ShoppingList.user_id == 1).first()
        assert shopping_list.__repr__() == '<ShoppingList list_id=1 user_id=1 has_shopped=False>'

    def test_log_out(self):
        """ Test user log out."""

        result = self.client.get("/logout")
        self.assertIn("You Have Logged Out", result.data)

if __name__ == "__main__":
    import unittest

    unittest.main()
