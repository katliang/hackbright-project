""" Seeds database."""

from model import User
from model import UserRecipe
from model import Recipe
from model import ShoppingList
from model import ListIngredient
from model import Ingredient
from model import Inventory
from model import connect_to_db, db
from server import app








if __name__ == "__main__":
    connect_to_db(app)

    # Create tables if they haven't been created already
    db.create_all()

    # Loads test user data
    load_test_users()

