""" Seeds database."""

from model import User, UserRecipe, Recipe, ShoppingList, ListIngredient, Ingredient, Inventory
from model import connect_to_db, db
from server import app


if __name__ == "__main__":
    connect_to_db(app)

    # Create tables if they haven't been created already
    db.create_all()
