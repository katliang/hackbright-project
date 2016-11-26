from unittest import TestCase
from server import app
from model import connect_to_db, db, example_data, User, UserRecipe, Recipe, ShoppingList, convert_to_base_unit, aggregate_ingredients, search_recipes
import os
import server
import model


class FlaskTestsBasic(TestCase):
    """ Flask Tests"""

    def setUp(self):
        """ Things to do before every test."""

        # Get the Flask test client
        self.client = app.test_client()

        # Show Flask errors that happen during tests
        app.config['TESTING'] = True

    def test_homepage_title(self):
        """Test title on homepage."""

        result = self.client.get("/")
        self.assertIn("ingrediYUM", result.data)

    def test_homepage_signup(self):
        """Test sign up button on homepage."""

        result = self.client.get("/")
        self.assertIn("Sign Up</button>", result.data)

    def test_homepage_username(self):
        """Test username field on homepage."""

        result = self.client.get("/")
        self.assertIn("Username", result.data)

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

        db.session.remove()
        db.drop_all()

    def test_new_registration(self):
        """ Test new user registration."""

        result = self.client.post("/register",
                                  data={"username": "sandy", "password": "123"},
                                  follow_redirects=True)
        self.assertIn("Log In Here", result.data)

    def test_duplicate_registration(self):
        """ Test notification to user when username is taken."""

        result = self.client.post("/register",
                                  data={"username": "tom", "password": "123"},
                                  follow_redirects=True)
        self.assertIn("This username already exists. Please choose another username.", result.data)

    def test_duplicate_registration_redirect(self):
        """ Test redirect to homepage if registration fails."""

        result = self.client.post("/register",
                                  data={"username": "tom", "password": "123"},
                                  follow_redirects=True)
        self.assertIn("Sign Up</button>", result.data)


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
        self.assertIn("Welcome tom!", result.data)

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

    def test_new_search_form_diet(self):
        """ Test diet field on new search form page."""

        result = self.client.get("/new_search")
        self.assertIn('<select name="diet"', result.data)

    def test_new_search_form(self):
        """ Test find recipe button on new search form page."""

        result = self.client.get("/new_search")
        self.assertIn('Find New Recipe(s)</button>', result.data)

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

    def test_convert_to_base_unit_pounds(self):
        """ Test conversion from pounds to ounces."""

        self.assertEqual(convert_to_base_unit(2, 'pounds'), (32.00, 'ounces'))

    def test_convert_to_base_unit_tsp(self):
        """ Test conversion from tablespoons to teaspoons."""

        self.assertEqual(convert_to_base_unit(2, 'tbsp'), (6, 'teaspoons'))

    def test_incorrect_convert_to_base_unit(self):
        """ Test incorrect conversion."""

        self.assertNotEqual(convert_to_base_unit(2, 'pounds'), (2, 'ounces'))

    def test_convert_to_base_other(self):
        """ Test other units."""

        self.assertEqual(convert_to_base_unit(2, 'servings'), (2, 'servings'))


class MockTests(TestCase):
    """Tests with mocking."""

    def setUp(self):
        """ Things to do before every test."""

        # Get the Flask test client
        self.client = app.test_client()
        app.config['TESTING'] = True

        # Connect to test database
        connect_to_db(app, "postgresql:///testfood")

        # Create tables and add sample data
        db.drop_all()
        db.create_all()
        example_data()

        # Create a session
        app.config['SECRET_KEY'] = os.environ["testing_secret_key"]

        with self.client as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

        def _mock_recipe_info_by_id(recipe_id):
            """ Mock data of recipe info."""

            return {"servings": 4,
                    "preparationMinutes": 40,
                    "sourceUrl": "testrecipe.com",
                    "sourceName": "Test Source Recipe",
                    "extendedIngredients": [
                                            {"id": 1,
                                            "aisle": "Fruit",
                                            "image": "apple.png",
                                            "name": "apple",
                                            "amount": 1,
                                            "unit": "pound",
                                            "unitLong": "pound"},
                                            {"id": 2,
                                            "aisle": "Fruit",
                                            "image": "banana.jpg",
                                            "name": "banana",
                                            "amount": 3,
                                            "unit": "ounces",
                                            "unitLong": "ounces"}
                                            ],
                    "id": 1,
                    "title": "Test Recipe",
                    "readyInMinutes": 60,
                    "image": "/recipe.jpg",
                    "instructions": "Recipe instructions here."
                    }

        server.recipe_info_by_id = _mock_recipe_info_by_id
        model.recipe_info_by_id = _mock_recipe_info_by_id

    def tearDown(self):
        """ Things to do after every test."""

        db.session.remove()
        db.session.close()
        db.drop_all()

    def test_show_recipe_title_with_mock(self):
        """ Test title displayed for a recipe."""

        result = self.client.get("/recipe_detail/100")
        self.assertIn("<h2>Test Recipe", result.data)

    def test_show_recipe_image_with_mock(self):
        """ Test image displayed for a recipe."""

        result = self.client.get("/recipe_detail/100")
        self.assertIn('<img src="/recipe.jpg">', result.data)

    def test_show_recipe_ingredient_with_mock(self):
        """ Test an ingredient displayed for a recipe."""

        result = self.client.get("/recipe_detail/100")
        self.assertIn("1.00 pound apple", result.data)

    def test_incorrect_recipe_ingredient_with_mock(self):
        """ Test an incorrect ingredient amount for a recipe."""

        result = self.client.get("/recipe_detail/100")
        self.assertNotIn("3 ounces banana", result.data)

    def test_show_recipe_button_with_mock(self):
        """ Test cook button for a recipe."""

        result = self.client.get("/recipe_detail/100")
        self.assertIn("Cook me!</button>", result.data)

    def test_aggregate_ingredients_one_recipe(self):
        """ Test aggregation function with one recipe."""

        self.assertEqual(aggregate_ingredients([('1',)]), ({1: {'quantity': 16.00,
                                                                'unit': 'ounces',
                                                                'name': 'apple',
                                                                'aisle': 'Fruit'},
                                                            2: {'quantity': 3.00,
                                                                'unit': 'ounces',
                                                                'name': 'banana',
                                                                'aisle': 'Fruit'}
                                                            })
                        )

    def test_aggregate_ingredients_two_recipes(self):
        """ Test aggregation function with two recipes."""

        self.assertEqual(aggregate_ingredients([('1',), ('1',)]), ({1: {'quantity': 32.00,
                                                                      'unit': 'ounces',
                                                                      'name': 'apple',
                                                                      'aisle': 'Fruit'},
                                                                    2: {'quantity': 6.00,
                                                                      'unit': 'ounces',
                                                                      'name': 'banana',
                                                                      'aisle': 'Fruit'}
                                                                    })
                        )


if __name__ == "__main__":
    import unittest

    unittest.main()
