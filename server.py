""" Flask site for project app."""

from flask import Flask, render_template, request
from flask_debugtoolbar import DebugToolbarExtension
from model import search_recipes
from model import User
from model import Recipe
from model import Ingredient
from model import RecipeIngredient
from model import connect_to_db, db
from jinja2 import StrictUndefined

import os

app = Flask(__name__)

app.secret_key = os.environ["secretkey"]

# Raises an error if an undefined variable is used in Jinja2
app.jinja_env.undefined = StrictUndefined

@app.route("/")
def homepage():
    """Display homepage."""

    return render_template("homepage.html")


@app.route("/inventory", methods=["POST"])
def show_inventory():
    """ Display user's current ingredients."""

    username = request.form.get("username")
    password = request.form.get("password")

    check_user = User.query.filter(User.username == username, User.password == password).first()

    if check_user:
        # user begins with no inventory
        current_ingredients = []
        return render_template("inventory.html", current_ingredients=current_ingredients)
    else:
        return render_template("/homepage.html")


@app.route("/recipes")
def show_matching_recipes():
    """ Display recipes using the ingredient selected."""

    diet = request.args.get("diet")
    intolerances = request.args.getlist("intolerances")
    numresults = request.args.get("numresults")
    query = request.args.get("query")

    intolerances = "%2C+".join(intolerances)

    recipe_info = search_recipes(diet, intolerances, numresults, query)

    return render_template("recipes.html", recipe_info=recipe_info)


@app.route("/shopping_list", methods=["POST"])
def show_shopping_list():
    """Display shopping list of missing ingredients."""

    recipes_ingredients = request.form.getlist("recipe")

    print "recipes_ingredients is ", recipes_ingredients
    print "recipes_ingredients[0] is ", recipes_ingredients[0]
    print "recipes_ingredients type is ", type(recipes_ingredients)
    print "recipes_ingredients[0] type is ", type(recipes_ingredients[0])

    return render_template("shopping.html")



if __name__ == "__main__":
    # the toolbar is only enabled in debug mode:
    app.debug = True
    connect_to_db(app)
    DebugToolbarExtension(app)
    app.run(host="0.0.0.0")