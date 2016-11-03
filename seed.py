""" Seeds database."""

from model import User
from model import Recipe
from model import Ingredient
from model import RecipeIngredient
from model import connect_to_db, db
from server import app


def load_test_users():
    """ Loads some sample usernames and passwords for testing."""

    print 'Users'

    # Deletes all rows in the table to avoid duplicate data if
    # this function has to be run again
    User.query.delete()

    bob = User(username="bob", password="123")
    sally = User(username="sally", password="123")
    tom = User(username="tom", password="123")

    # Adds above users to the session
    db.session.add(bob)
    db.session.add(sally)
    db.session.add(tom)

    # Commit changes to the database
    db.session.commit()





if __name__ == "__main__":
    connect_to_db(app)

    # Create tables if they haven't been created already
    db.create_all()

    # Loads test user data
    load_test_users()

