""" Models and database functions for application."""

from flask_sqlalchemy import SQLAlchemy
import unirest
import os

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()

class User(db.Model):
    """ User of application."""

    __tablename__ = 'users'

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        """ Provide helpful representation when printed."""

        return '<User user_id=%s username=%s password=%s>' % (self.user_id,
                                                              self.username,
                                                              self.password,
                                                             )


class UserRecipe(db.Model):
    """ User recipe data."""

    __tablename__ = 'user_recipes'

    user_recipe_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.recipe_id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)

    # Define relationship to users table
    user = db.relationship("User", backref=db.backref('user_recipes'))

    # Define relationship to recipes table
    recipe = db.relationship("Recipe", backref=db.backref('user_recipes'))

    def __repr__(self):
        """ Provide helpful representation when printed."""

        return '<UserRecipe user_id=%s recipe_id=%s has_cooked=%s>' % (self.user_id,
                                                                       self.recipe_id,
                                                                       self.status,
                                                                       )


class Recipe(db.Model):
    """ Recipe id."""

    __tablename__ = 'recipes'

    recipe_id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        """ Provide helpful representation when printed."""

        return '<Recipe recipe_id=%s>' % (self.recipe_id,
                                          )


class ShoppingList(db.Model):
    """Shopping list data."""

    __tablename__ = 'shopping_lists'

    list_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    has_shopped = db.Column(db.Boolean, nullable=False)

    # Define relationship to users table
    user = db.relationship("User", backref=db.backref('shopping_lists'))

    def __repr__(self):
        """ Provide helpful representation when printed."""

        return '<ShoppingList list_id=%s user_id=%s has_shopped>' % (self.list_id,
                                                                     self.user_id,
                                                                     self.has_shopped,
                                                                     )


class ListIngredient(db.Model):
    """Shopping list ingredient data."""

    __tablename__ = 'shopping_list_ingredients'

    list_ingredient_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    shopping_list_id = db.Column(db.Integer, db.ForeignKey('shopping_lists.list_id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.ingredient_id'), nullable=False)
    aggregate_quantity = db.Column(db.Float, nullable=False)

    # Define relationship to shopping_lists table
    shopping_list = db.relationship("ShoppingList", backref=db.backref('shopping_list_ingredients'))

    # Define relationship to ingredients table
    ingredient = db.relationship("Ingredient", backref=db.backref('shopping_list_ingredients'))

    def __repr__(self):
        """ Provide helpful representation when printed."""

        return '<ListIngredient ingredient_id=%s aggregate_quantity=%s>' % (self.ingredient_id,
                                                                            self.aggregate_quantity,
                                                                            )


class Ingredient(db.Model):
    """ Ingredient data."""

    __tablename__ = 'ingredients'

    ingredient_id = db.Column(db.Integer, primary_key=True)
    ingredient_name = db.Column(db.String(100), nullable=False)
    base_unit = db.Column(db.String(20), nullable=True)


    def __repr__(self):
        """ Provide helpful representation when printed."""

        return '<Ingredient ingredient_name=%s base_unit=%s>' % (self.ingredient_name,
                                                                 self.base_unit,
                                                                 )

class Inventory(db.Model):
    """ Inventory data."""

    __tablename__ = 'inventory'

    inventory_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.ingredient_id'), nullable=False)
    current_quantity = db.Column(db.Float, nullable=False)

    # Define relationship to users table
    user = db.relationship("User", backref=db.backref('inventory'))

    # Define relationship to ingredients table
    ingredients = db.relationship("Ingredient", backref=db.backref('inventory'))


""" Helper functions for applications. """


def connect_to_db(app):
    """ Connect the database to our Flask app."""

    # Configure to use our database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///food'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


def call_api(url):
    """ Takes in a url and requests data from API."""

    # These code snippets use an open-source library. http://unirest.io/python
    response = unirest.get(url,
        headers={
        "X-Mashape-Key": os.environ["secret_key"],
        "Accept": "application/json"
                }
    )

    return response


def search_by_ingredient(search_word):
    """ Takes in a string and returns a list of recipes as dictionaries."""

    url = "https://spoonacular-recipe-food-nutrition-v1.p.mashape.com/recipes/findByIngredients?fillIngredients=true&ingredients=" + str(search_word) + "&limitLicense=false&number=5&ranking=1"

    response = call_api(url)

    # response.body is the parsed response (list)
    return response.body


def search_recipes(diet, intolerances, query):
    """ Searches for recipes and returns a list of recipe information.

    Takes in strings for diet, intolerances and query, and an integer for numresults.
    """

    # ids of recipes that meet user criteria
    result_ids = []
    result_recipe_info = []

    search_url = "https://spoonacular-recipe-food-nutrition-v1.p.mashape.com/recipes/search?diet=" + diet + "&intolerances=" + intolerances + "&number=2&query=" + query

    response = call_api(search_url)

    # response.body is the parsed response (dict)
    for result in response.body['results']:
        result_ids.append(result['id'])

    # second request to get info by recipe id
    for recipe_id in result_ids:
        result_recipe_info.append(recipe_info_by_id(recipe_id))

    return result_recipe_info

def recipe_info_by_id(recipe_id):
    """Takes in a recipe id and returns recipe info for that recipe."""

    get_recipe_url = "https://spoonacular-recipe-food-nutrition-v1.p.mashape.com/recipes/" + str(recipe_id) + "/information?includeNutrition=false"
    recipe_response = call_api(get_recipe_url)

    return recipe_response.body

def convert_to_base_unit(amount, input_unit):
    """Takes in an amount and unit and returns the converted quantity and base unit."""

    if input_unit.lower() in ['lb', 'pounds', 'pound']:
        new_amount = amount * 16.00
        return (new_amount, 'ounces')
    elif input_unit.lower() in ['tbsp', 'tablespoons', 'tbs', 'tbsps']:
        new_amount = amount * 3.00
        return (new_amount, 'teaspoons')
    else:
        return (amount, input_unit)


if __name__ == "__main__":

    from server import app
    connect_to_db(app)
    print 'Connected to DB'
