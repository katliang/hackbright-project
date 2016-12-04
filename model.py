""" Models and database functions for application."""

from flask_sqlalchemy import SQLAlchemy
import unirest
import os
from werkzeug.security import generate_password_hash, check_password_hash

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()

class User(db.Model):
    """ User of application."""

    __tablename__ = 'users'

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        """ Provide helpful representation when printed."""

        return '<User user_id=%s username=%s>' % (self.user_id,
                                                  self.username,
                                                  )

    def set_password(self, password):
        """ Sets user password to hashed password."""

        self.password = generate_password_hash(password)

    def check_password(self, password):
        """ Checks user's hashed password."""

        return check_password_hash(self.password, password)

    def get_current_inventory(self):
        """ Returns user's current inventory list."""

        current_inventory = Inventory.query.filter(Inventory.user_id == self.user_id, Inventory.current_quantity > 0).all()

        current_inventory_list = []

        for ingredient in current_inventory:
            current_quantity = ingredient.current_quantity
            base_unit = ingredient.ingredients.base_unit
            ingredient_name = ingredient.ingredients.ingredient_name
            current_inventory_list.append((current_quantity, base_unit, ingredient_name))

        return sorted(current_inventory_list, key=lambda x: x[2])

    def get_pending_recipes(self):
        """ Returns user's pending recipes list."""

        pending_recipes = UserRecipe.query.filter(UserRecipe.status == 'in_progress', UserRecipe.user_id == self.user_id).all()

        pending_recipes_list = []

        for user_recipe in pending_recipes:
            recipe_info = recipe_info_by_id(user_recipe.recipe.recipe_id)
            pending_recipes_list.append(recipe_info)

        return pending_recipes_list

    def get_pending_shopping_lists(self):
        """ Returns user's pending shopping lists."""

        return ShoppingList.query.filter(ShoppingList.has_shopped == False, ShoppingList.user_id == self.user_id).all()

    def get_used_and_missing_ingredients(self, recipe_id_list):
        """ Takes in a list of recipe ids and returns its ingredients with an id, current
        inventory ingredients, missing ingredients and general recipe info."""

        results_recipes = {}

        for recipe_id in recipe_id_list:

            recipe_info = recipe_info_by_id(recipe_id)

            results_recipes[recipe_id] = {}
            results_recipes[recipe_id]['inventory_ing'] = []
            results_recipes[recipe_id]['missing_ing'] = []
            results_recipes[recipe_id]['info'] = recipe_info

            for ingredient in recipe_info['extendedIngredients']:
                (converted_amount, base_unit) = convert_to_base_unit(ingredient['amount'], ingredient['unitLong'])

                check_inventory = Inventory.query.filter(Inventory.ingredient_id == int(ingredient['id']), Inventory.user_id == self.user_id).first()

                if check_inventory:
                    if check_inventory.current_quantity <= 0:
                        results_recipes[recipe_id]['missing_ing'].append((int(ingredient['id']), converted_amount, base_unit, ingredient['name'], ingredient['aisle']))
                    else:
                        results_recipes[recipe_id]['inventory_ing'].append((int(ingredient['id']), converted_amount, base_unit, ingredient['name'], ingredient['aisle']))
                else:
                    results_recipes[recipe_id]['missing_ing'].append((int(ingredient['id']), converted_amount, base_unit, ingredient['name'], ingredient['aisle']))

        return results_recipes

class UserRecipe(db.Model):
    """ User recipe data."""

    __tablename__ = 'user_recipes'

    user_recipe_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.recipe_id'), nullable=False)
    status = db.Column(db.String(30), nullable=False)

    # Define relationship to users table
    user = db.relationship("User", backref=db.backref('user_recipes'))

    # Define relationship to recipes table
    recipe = db.relationship("Recipe", backref=db.backref('user_recipes'))

    def __repr__(self):
        """ Provide helpful representation when printed."""

        return '<UserRecipe user_id=%s recipe_id=%s status=%s>' % (self.user_id,
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

        return '<ShoppingList list_id=%s user_id=%s has_shopped=%s>' % (self.list_id,
                                                                        self.user_id,
                                                                        self.has_shopped,
                                                                        )

    def get_ingredients(self):
        """ Returns ingredients from a shopping list."""

        list_ingredients = ListIngredient.query.filter(ListIngredient.shopping_list_id == self.list_id).all()

        all_ingredients = {}

        for ingredient in list_ingredients:
            ingredient_id = ingredient.ingredient_id
            ingredient_qty = ingredient.aggregate_quantity
            ingredient_unit = ingredient.ingredient.base_unit
            ingredient_name = ingredient.ingredient.ingredient_name
            ingredient_aisle = ingredient.ingredient.ingredient_aisle

            if ingredient_aisle not in all_ingredients:
                all_ingredients[ingredient_aisle] = [(ingredient_id, ingredient_qty, ingredient_unit, ingredient_name)]
            else:
                all_ingredients[ingredient_aisle].append((ingredient_id, ingredient_qty, ingredient_unit, ingredient_name))

        return all_ingredients


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
    ingredient_aisle = db.Column(db.String(50), nullable=True)


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


def connect_to_db(app, db_uri='postgresql:///food'):
    """ Connect the database to our Flask app."""

    # Configure to use our database
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


def example_data():
    """Create some sample data."""

    # Adds sample users.
    sally = User(username="sally", password="")
    sally.set_password("123")
    tom = User(username="tom", password="")
    tom.set_password("123")

    # Adds sample recipes.
    rec1 = Recipe(recipe_id=1)
    rec2 = Recipe(recipe_id=2)

    # Adds sample ingredients.
    ing1 = Ingredient(ingredient_id=1, ingredient_name='apple', base_unit='ounces')
    ing2 = Ingredient(ingredient_id=2, ingredient_name='banana', base_unit='ounces')
    ing3 = Ingredient(ingredient_id=3, ingredient_name='carrot', base_unit='ounces')

    # Adds sample shopping lists.
    shop1 = ShoppingList(user_id=1, has_shopped=False)
    shop2 = ShoppingList(user_id=2, has_shopped=False)

    db.session.add_all([sally, tom, rec1, rec2, ing1, ing2, ing3, shop1, shop2])
    db.session.commit()

    # Adds sample inventory.
    inv1 = Inventory(user_id=1, ingredient_id=1, current_quantity=5)
    inv2 = Inventory(user_id=1, ingredient_id=2, current_quantity=0)
    inv3 = Inventory(user_id=2, ingredient_id=3, current_quantity=5)

    # Adds sample user recipes.
    u_rec1 = UserRecipe(user_id=1, recipe_id=1, status='needs_ingredients')
    u_rec2 = UserRecipe(user_id=2, recipe_id=2, status='in_progress')

    db.session.add_all([inv1, inv2, inv3, u_rec1, u_rec2])
    db.session.commit()


def call_api(url):
    """ Takes in a url and requests data from API."""

    # These code snippets use an open-source library. http://unirest.io/python
    response = unirest.get(url,
        headers={
        "X-Mashape-Key": os.environ["SPOONACULAR_SECRET_KEY"],
        "Accept": "application/json"
                }
    )

    return response


def search_api_by_ingredient(search_string):
    """ Takes in a search string and returns a list of recipes as dictionaries."""

    url = "https://spoonacular-recipe-food-nutrition-v1.p.mashape.com/recipes/searchComplex?addRecipeInformation=true&fillIngredients=true&includeIngredients=" + str(search_string) + "&intolerances=&limitLicense=false&number=5&ranking=1"

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

    search_url = "https://spoonacular-recipe-food-nutrition-v1.p.mashape.com/recipes/search?diet=" + diet + "&intolerances=" + intolerances + "&number=4&query=" + query

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
    elif input_unit.lower() in ['tbsp', 'tablespoons', 'tbs', 'tbsps', 'tablespoon']:
        new_amount = amount * 3.00
        return (new_amount, 'teaspoons')
    else:
        return (amount, input_unit)

def aggregate_ingredients(all_user_recipes):
    """ Takes a list of recipe ids and aggregates ingredients."""

    aggregated_ingredients = {}

    for recipe_id in all_user_recipes:
        recipe_info = recipe_info_by_id(recipe_id[0])

        for ingredient in recipe_info['extendedIngredients']:
            (converted_amount, base_unit) = convert_to_base_unit(ingredient['amount'], ingredient['unitLong'])

            if ingredient['id'] not in aggregated_ingredients:
                aggregated_ingredients[ingredient['id']] = {'quantity': converted_amount, 'unit': base_unit, 'name': ingredient['name'], 'aisle': ingredient['aisle']}
            else:
                aggregated_ingredients[ingredient['id']]['quantity'] += converted_amount

    return aggregated_ingredients


# if __name__ == "__main__":

#     from server import app
#     connect_to_db(app)
#     print 'Connected to DB'
