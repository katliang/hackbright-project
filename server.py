""" Flask site for project app."""

from flask import Flask, render_template, request, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from model import search_recipes, recipe_info_by_id, convert_to_base_unit
from model import User
from model import UserRecipe
from model import Recipe
from model import ShoppingList
from model import ListIngredient
from model import Ingredient
from model import Inventory
from model import connect_to_db, db
from jinja2 import StrictUndefined
from sqlalchemy.sql import func

import os

app = Flask(__name__)

app.secret_key = os.environ["secretkey"]

# Raises an error if an undefined variable is used in Jinja2
app.jinja_env.undefined = StrictUndefined

@app.route("/")
def homepage():
    """Display homepage."""

    return render_template("homepage.html")


@app.route("/search", methods=["POST"])
def show_search_form():
    """ Display user's current ingredients."""

    username = request.form.get("username")
    password = request.form.get("password")

    check_user = User.query.filter(User.username == username, User.password == password).first()

    if check_user:
        # user begins with no inventory
        session['user_id'] = check_user.user_id
        current_ingredients = []
        return render_template("search.html", current_ingredients=current_ingredients)
    else:
        return render_template("/homepage.html")


@app.route("/search", methods=["GET"])
def redisplay_search_form():
    """ Display user's current ingredients."""

    # if user is searching again for recipes, session is still active
    if 'user_id' in session:
        current_ingredients = []
        return render_template("search.html", current_ingredients=current_ingredients)
    else:
        return render_template("/homepage.html")


@app.route("/recipes")
def show_matching_recipes():
    """ Display recipes using the ingredient selected."""

    diet = request.args.get("diet")
    intolerances = request.args.getlist("intolerances")
    query = request.args.get("query")

    intolerances = "%2C+".join(intolerances)

    recipe_info = search_recipes(diet, intolerances, query)

    return render_template("recipes.html", recipe_info=recipe_info)


@app.route("/user-recipes", methods=["POST"])
def show_user_recipes():
    """Keeps track of selected recipes."""

    recipe_ids = request.form.getlist("recipe_ids[]")

    for recipe_id in recipe_ids:
        recipe = db.session.query(UserRecipe).filter(UserRecipe.user_id == session['user_id'], UserRecipe.recipe_id == recipe_id).first()
        if not recipe:
            new_recipe = Recipe(recipe_id=recipe_id,
                                )
            db.session.add(new_recipe)

        new_user_recipe = UserRecipe(user_id=session['user_id'],
                                     recipe_id=recipe_id,
                                     status='need_ingredients',
                                     )
        db.session.add(new_user_recipe)

    db.session.commit()

    all_user_recipes = db.session.query(UserRecipe.recipe_id).filter(UserRecipe.user_id == session['user_id']).filter(UserRecipe.status == 'need_ingredients').all()
    
    recipe_dict = {}
    recipe_dict['id'] = []

    for recipe in all_user_recipes:
        recipe_dict['id'].append(recipe[0])

    return jsonify(recipe_dict)


@app.route("/shopping_list", methods=["POST"])
def show_shopping_list():
    """Display shopping list of missing ingredients."""

    all_user_recipes = db.session.query(UserRecipe.recipe_id).filter(UserRecipe.user_id == session['user_id']).all()
    new_shopping_list = ShoppingList(user_id=session['user_id'],
                                     has_shopped=False,
                                    )
    db.session.add(new_shopping_list)
    db.session.commit()

    aggregated_ingredients = {}

    for recipe_id in all_user_recipes:
        recipe_info = recipe_info_by_id(recipe_id[0])
        
        for ingredient in recipe_info['extendedIngredients']:
            (converted_amount, base_unit) = convert_to_base_unit(ingredient['amount'], ingredient['unitLong'])

            if ingredient['id'] not in aggregated_ingredients:
                aggregated_ingredients[ingredient['id']] = {'quantity': converted_amount, 'unit': base_unit, 'name': ingredient['name']}
            else:
                aggregated_ingredients[ingredient['id']]['quantity'] += converted_amount

    for ingredient_id in aggregated_ingredients:
        ingredient = db.session.query(Ingredient).filter(Ingredient.ingredient_id == ingredient_id).first()

        if not ingredient:
            new_ingredient = Ingredient(ingredient_id=ingredient_id,
                                        ingredient_name=aggregated_ingredients[ingredient_id]['name'],
                                        base_unit=aggregated_ingredients[ingredient_id]['unit'],
                                        )
            db.session.add(new_ingredient)

        new_list_ingredient = ListIngredient(shopping_list_id=new_shopping_list.list_id,
                                             ingredient_id=ingredient_id,
                                             aggregate_quantity=aggregated_ingredients[ingredient_id]['quantity'],
                                             )
        db.session.add(new_list_ingredient)

    db.session.commit()

    user_ingredients = (db.session.query(ListIngredient.aggregate_quantity,
                                         Ingredient.base_unit,
                                         Ingredient.ingredient_name)
                                  .join(Ingredient)
                                  .join(ShoppingList)
                                  .join(User)
                                  .filter(ListIngredient.shopping_list_id == new_shopping_list.list_id)
                                  .filter(User.user_id == session['user_id'])
                                  .order_by(Ingredient.ingredient_name)).all()
    
    return render_template("shopping.html", ingredients=user_ingredients)


@app.route("/logout")
def logs_user_out():
    """ Logs out user."""

    session.pop('user_id', None)

    return render_template("/logout.html")


if __name__ == "__main__":
    # the toolbar is only enabled in debug mode:
    app.debug = True
    connect_to_db(app)
    DebugToolbarExtension(app)
    app.run(host="0.0.0.0")