""" Flask site for project app."""

from flask import Flask, render_template, request, session, jsonify, flash, redirect
from flask_debugtoolbar import DebugToolbarExtension
from model import search_recipes, recipe_info_by_id, convert_to_base_unit, search_api_by_ingredient, aggregate_ingredients
from model import User
from model import UserRecipe
from model import Recipe
from model import ShoppingList
from model import ListIngredient
from model import Ingredient
from model import Inventory
from model import connect_to_db, db
from jinja2 import StrictUndefined
import json
import os

app = Flask(__name__)

app.secret_key = os.environ["secretkey"]

# Raises an error if an undefined variable is used in Jinja2
app.jinja_env.undefined = StrictUndefined

@app.route("/")
def homepage():
    """ Display homepage."""

    return render_template("homepage.html")


@app.route("/register", methods=["POST"])
def register_process():
    """ Verify registration."""

    username = request.form.get("username")
    password = request.form.get("password")

    check_user = User.query.filter(User.username == username).first()

    if check_user:
        flash('This username already exists. Please choose another username.')
        return redirect("/")
    else:
        new_user = User(username=username, password="")
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return render_template("login.html", just_registered=True)


@app.route("/login", methods=["GET"])
def login_form():
    """ Show login form."""

    return render_template("login.html", just_registered=False)


@app.route("/login", methods=["POST"])
def login_process():
    """ Verify login."""

    username = request.form.get("username")
    password = request.form.get("password")

    check_user = User.query.filter(User.username == username).first()

    if check_user:
        check_password = check_user.check_password(password)
        if check_password:
            session['user_id'] = check_user.user_id
            flash("You are logged in")
            return redirect("/main")
        else:
            flash("Incorrect username and/or password. Please try again.")
            return redirect("/login")
    else:
        flash("Incorrect username and/or password. Please try again.")
        return redirect("/login")


@app.route("/main")
def display_main_page():
    """ Show user's main page."""

    # if user is logged in, session is still active
    if 'user_id' in session:
        current_user = User.query.get(session['user_id'])
        current_ingredients_list = current_user.get_current_inventory()
        pending_shopping_lists = current_user.get_pending_shopping_lists()
        pending_recipes_list = current_user.get_pending_recipes()

        return render_template("main.html", current_ingredients=current_ingredients_list,
                                            pending_shopping_lists=pending_shopping_lists,
                                            pending_recipes_list=pending_recipes_list,
                                            current_user=current_user.username,
                                            )
    else:
        return render_template("homepage.html")

@app.route("/new_search")
def show_new_search_form():

    return render_template("new-search.html")


@app.route("/recipes")
def show_matching_recipes():
    """ Display recipes using the user's diet, intolerances and keywords."""

    diet = request.args.get("diet")
    intolerances = request.args.getlist("intolerances")
    query = request.args.get("query")

    intolerances = "%2C+".join(intolerances)

    recipe_info = search_recipes(diet, intolerances, query)

    return render_template("recipes.html", recipe_info=recipe_info)


@app.route("/user-recipes", methods=["POST"])
def update_user_recipes():
    """ Keeps track of user's selected recipes."""

    recipe_id = request.form.get("recipe_id")

    recipe = Recipe.query.get(int(recipe_id))
    if not recipe:
        new_recipe = Recipe(recipe_id=recipe_id,
                            )
        db.session.add(new_recipe)
        db.session.commit()

    new_user_recipe = UserRecipe(user_id=session['user_id'],
                                 recipe_id=recipe_id,
                                 status='needs_ingredients',
                                 )
    db.session.add(new_user_recipe)
    db.session.commit()

    return jsonify({'recipe_id': recipe_id})


@app.route("/recipe_detail/<recipe_id>")
def show_recipe_details(recipe_id):
    """ Displays recipe details."""

    recipe_details = recipe_info_by_id(recipe_id)

    return render_template("recipe_info.html", recipe_details=recipe_details)


@app.route("/verify_recipe.json", methods=["POST"])
def verify_recipe():
    """ Verify if inventory has enough of the recipe's ingredients to cook."""

    recipe_id = request.form.get("data")

    recipe_details = recipe_info_by_id(int(recipe_id))

    # First check if ALL ingredients are sufficient to make recipe
    for ingredient in recipe_details['extendedIngredients']:
        # Look up ingredient in inventory table
        check_ingredient = Inventory.query.filter(Inventory.ingredient_id == int(ingredient['id']), Inventory.user_id == session['user_id']).first()

        if not check_ingredient:
            return jsonify({'result': False})
        # If unit is not the same as the base unit in inventory table, convert the unit to base unit
        if ingredient['unitLong'] != check_ingredient.ingredients.base_unit:
            (converted_amount, converted_unit) = convert_to_base_unit(float(ingredient['amount']), ingredient['unitLong'])

            # Check if current inventory has enough for the recipe
            if check_ingredient.current_quantity < converted_amount:
                return jsonify({'result': False})
        else:
            if check_ingredient.current_quantity < round(float(ingredient['amount']),2):
                return jsonify({'result': False})

    # If ALL ingredients are sufficient, subtract quantities
    for ingredient in recipe_details['extendedIngredients']:
        update_ingredient = Inventory.query.filter(Inventory.ingredient_id == int(ingredient['id']), Inventory.user_id == session['user_id']).one()

        if ingredient['unitLong'] != update_ingredient.ingredients.base_unit:
            (converted_amount, converted_unit) = convert_to_base_unit(float(ingredient['amount']), ingredient['unitLong'])
            # Subtract recipe amount from inventory amount
            update_ingredient.current_quantity -= converted_amount
        else:
            update_ingredient.current_quantity -= round(float(ingredient['amount']),2)

    # Update user_recipe status to 'cooked'
    cooked_recipe = UserRecipe.query.filter(UserRecipe.recipe_id == int(recipe_id), UserRecipe.user_id == session['user_id'], UserRecipe.status == 'in_progress').first()
    cooked_recipe.status = 'cooked'

    db.session.commit()

    return jsonify({'result': True})


@app.route("/shopping_list", methods=["POST"])
def show_shopping_list():
    """ Creates shopping list of missing ingredients with aggregated quantities and base units."""

    all_user_recipes = db.session.query(UserRecipe.recipe_id).filter(UserRecipe.user_id == session['user_id'], UserRecipe.status == 'needs_ingredients').all()
    new_shopping_list = ShoppingList(user_id=session['user_id'],
                                     has_shopped=False,
                                    )
    db.session.add(new_shopping_list)

    aggregated_ingredients = aggregate_ingredients(all_user_recipes)

    for ingredient_id in aggregated_ingredients:
        ingredient = db.session.query(Ingredient).filter(Ingredient.ingredient_id == ingredient_id).first()

        if not ingredient:
            new_ingredient = Ingredient(ingredient_id=ingredient_id,
                                        ingredient_name=aggregated_ingredients[ingredient_id]['name'],
                                        base_unit=aggregated_ingredients[ingredient_id]['unit'],
                                        ingredient_aisle=aggregated_ingredients[ingredient_id]['aisle'],
                                        )
            db.session.add(new_ingredient)

        new_list_ingredient = ListIngredient(shopping_list_id=new_shopping_list.list_id,
                                             ingredient_id=ingredient_id,
                                             aggregate_quantity=aggregated_ingredients[ingredient_id]['quantity'],
                                             )
        db.session.add(new_list_ingredient)

    # Update status of recipes added to shopping list to 'in progress'
    update_recipes = UserRecipe.query.filter(UserRecipe.user_id == session['user_id'], UserRecipe.status == 'needs_ingredients').all()
    for recipe in update_recipes:
        recipe.status = 'in_progress'

    db.session.commit()

    user_ingredients = new_shopping_list.get_ingredients()
    
    return render_template("shopping.html", ingredients=user_ingredients)


@app.route("/confirm_list/<shopping_list_id>")
def confirm_purchases(shopping_list_id):
    """ Displays the selected shopping list for user to confirm purchases."""

    shopping_list = ShoppingList.query.filter(ShoppingList.list_id == shopping_list_id).first()

    all_ingredients = shopping_list.get_ingredients()

    return render_template("list_confirmation.html", ingredients=all_ingredients, shopping_list_id=shopping_list_id)


@app.route("/inventory.json", methods=["POST"])
def add_inventory():
    """ Adds purchased ingredients to inventory."""

    inventory = request.form.get("data")
    inventory_dict = json.loads(inventory)
    shopping_list_id = int(request.form.get("listId"))

    # Add each ingredient to inventory list
    for ingredient_id in inventory_dict:
        check_inventory = Inventory.query.filter(Inventory.user_id == session['user_id'], Inventory.ingredient_id == ingredient_id).first()
        if not check_inventory:
            new_inventory = Inventory(user_id=session['user_id'],
                                      ingredient_id=int(ingredient_id),
                                      current_quantity=round(float(inventory_dict[ingredient_id]['ingredientQty']),2),
                                      )
            db.session.add(new_inventory)
        else:
            check_inventory.current_quantity += round(float(inventory_dict[ingredient_id]['ingredientQty']),2)

    # Change status of shopping list since list has been used by user
    shopping_list = ShoppingList.query.filter(ShoppingList.list_id == shopping_list_id).one()
    shopping_list.has_shopped = True

    db.session.commit()

    return jsonify({'success': True})


@app.route("/display_inventory")
def display_current_inventory():
    """ Displays user's current inventory."""

    current_user = User.query.get(session['user_id'])

    current_inventory_list = current_user.get_current_inventory()

    return render_template("/display-inventory.html", current_inventory=current_inventory_list)


@app.route("/search_by_ingredient")
def show_search_by_results():
    """ Takes user's selected ingredients to search for recipes and displays results."""

    # Retrieve list of selected ingredients by name and transform to search string
    search_ingredients = request.args.getlist("ingredient")
    ingredients = "%2C+".join(search_ingredients)

    search_results = search_api_by_ingredient(ingredients)

    # After getting search results, check if inventory quantity >= recipe quantity
    # since API only searches by ingredient name and doesn't include quantities.
    # Only display results that pass this criteria.

    # Filtered list of recipes to display to user
    filter_recipes = []

    for recipe in search_results['results']:
        enough_ingredients = True

        for ingredient in recipe['usedIngredients']:
            check_ingredient = Inventory.query.filter(Inventory.ingredient_id == int(ingredient['id']), Inventory.user_id == session['user_id']).first()

            # If the recipe ingredient's unit != inventory unit, convert it
            if ingredient['unitLong'] != check_ingredient.ingredients.base_unit:
                (converted_amount, converted_unit) = convert_to_base_unit(round(float(ingredient['amount']),2), ingredient['unitLong'])
                # If recipe amount > inventory amount, don't add recipe to list
                if converted_amount > check_ingredient.current_quantity:
                    enough_ingredients = False
            else:
                # If recipe amount > inventory amount, don't add recipe to list
                if round(float(ingredient['amount']),2) > check_ingredient.current_quantity:
                    enough_ingredients = False

        # If inventory quantities >= respective recipe quantities, add to list
        if enough_ingredients == True:
            filter_recipes.append(recipe['id'])

    current_user = User.query.get(session['user_id'])

    results_recipes = current_user.get_used_and_missing_ingredients(filter_recipes)

    return render_template("recipes-by-ingredient.html", results_recipes=results_recipes)


@app.route("/add-recipe-id.json", methods=['POST'])
def add_recipe_id():
    """ Adds selected recipe in which there are missing ingredients for shopping list."""

    # Get recipe ids for recipes selected by user
    selected_recipes = request.form.getlist('recipe-ids[]')

    for recipe_id in selected_recipes:
        # Convert from unicode
        recipe_id = int(recipe_id)

        # Check if recipe id already exists
        recipe = Recipe.query.get(recipe_id)

        # If recipe does not already exist, add it
        if not recipe:
            new_recipe = Recipe(recipe_id=recipe_id,
                                )
            db.session.add(new_recipe)
            db.session.commit()

        # Add recipe with status 'needs_missing_ingredients'
        new_user_recipe = UserRecipe(user_id=session['user_id'],
                                     recipe_id=recipe_id,
                                     status='needs_missing_ingredients',
                                     )
        db.session.add(new_user_recipe)

    db.session.commit()

    return jsonify({'result': True})


@app.route("/partial_shopping_list", methods=['POST'])
def add_missing_ingredients():
    """ Displays shopping list with missing ingredients."""

    new_recipes_to_add = db.session.query(UserRecipe.recipe_id).filter(UserRecipe.user_id == session['user_id'], UserRecipe.status == 'needs_missing_ingredients').all()

    new_recipe_list = []
    for recipe in new_recipes_to_add:
        new_recipe_list.append(recipe[0])

    new_shopping_list = ShoppingList(user_id=session['user_id'],
                                     has_shopped=False,
                                    )
    db.session.add(new_shopping_list)

    current_user = User.query.get(session['user_id'])

    results_recipes = current_user.get_used_and_missing_ingredients(new_recipe_list)

    for recipe in results_recipes:
        for missing_ingredient in results_recipes[recipe]['missing_ing']:
            ingredient = Ingredient.query.filter(Ingredient.ingredient_id == missing_ingredient[0]).first()
            if not ingredient:
                new_missing_ingredient = Ingredient(ingredient_id=missing_ingredient[0],
                                                    ingredient_name=missing_ingredient[3],
                                                    base_unit=missing_ingredient[2],
                                                    ingredient_aisle=missing_ingredient[4],
                                                    )
                db.session.add(new_missing_ingredient)

            new_list_ingredient = ListIngredient(shopping_list_id=new_shopping_list.list_id,
                                                 ingredient_id=missing_ingredient[0],
                                                 aggregate_quantity=missing_ingredient[1],
                                                 )

            db.session.add(new_list_ingredient)

    # Update status of recipes added to shopping list to 'in progress'
    update_recipes = UserRecipe.query.filter(UserRecipe.user_id == session['user_id'], UserRecipe.status == 'needs_missing_ingredients').all()
    for recipe in update_recipes:
        recipe.status = 'in_progress'
        db.session.commit()

    user_ingredients = new_shopping_list.get_ingredients()

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