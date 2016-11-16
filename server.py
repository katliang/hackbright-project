""" Flask site for project app."""

from flask import Flask, render_template, request, session, jsonify, flash, redirect
from flask_debugtoolbar import DebugToolbarExtension
from model import search_recipes, recipe_info_by_id, convert_to_base_unit, search_api_by_ingredient
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
    """Display homepage."""

    return render_template("homepage.html")


@app.route("/register", methods=["GET"])
def registration_form():
    """ Show registration form."""

    return render_template("registration.html")


@app.route("/register", methods=["POST"])
def register_process():
    """ Verify registration."""

    username = request.form.get("username")
    password = request.form.get("password")

    check_user = User.query.filter(User.username == username).first()

    if check_user:
        flash('This username already exists. Please choose another username.')
        return redirect("/register")
    else:
        new_user = User(username=username, password="")
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")


@app.route("/login", methods=["GET"])
def login_form():
    """ Show login form."""

    return render_template("login.html")


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
        current_ingredients = Inventory.query.filter(Inventory.user_id == session['user_id'], Inventory.current_quantity > 0).all()

        current_ingredients_list = []

        for ingredient in current_ingredients:
            current_quantity = ingredient.current_quantity
            base_unit = ingredient.ingredients.base_unit
            ingredient_name = ingredient.ingredients.ingredient_name
            current_ingredients_list.append((current_quantity, base_unit, ingredient_name))

        pending_shopping_lists = ShoppingList.query.filter(ShoppingList.has_shopped == False, ShoppingList.user_id == session['user_id']).all()

        pending_recipes = UserRecipe.query.filter(UserRecipe.status == 'in_progress', UserRecipe.user_id == session['user_id']).all()

        pending_recipes_list = []

        for user_recipe in pending_recipes:
            recipe_info = recipe_info_by_id(user_recipe.recipe.recipe_id)
            pending_recipes_list.append(recipe_info)

        return render_template("main.html", current_ingredients=current_ingredients_list,
                                            pending_shopping_lists=pending_shopping_lists,
                                            pending_recipes_list=pending_recipes_list,
                                            )
    else:
        return render_template("homepage.html")


@app.route("/recipes")
def show_matching_recipes():
    """ Display recipes using the ingredient selected."""

    diet = request.args.get("diet")
    intolerances = request.args.getlist("intolerances")
    query = request.args.get("query")

    intolerances = "%2C+".join(intolerances)

    recipe_info = search_recipes(diet, intolerances, query)

    return render_template("recipes.html", recipe_info=recipe_info)


@app.route("/user-recipes.json", methods=["POST"])
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
                                     status='needs_ingredients',
                                     )
        db.session.add(new_user_recipe)

    db.session.commit()

    return jsonify({})


@app.route("/recipe_detail/<recipe_id>")
def show_recipe_details(recipe_id):

    recipe_details = recipe_info_by_id(recipe_id)

    return render_template("recipe_info.html", recipe_details=recipe_details)


@app.route("/verify_recipe", methods=["POST"])
def verify_recipe():

    recipe_id = request.form.get("data")

    recipe_details = recipe_info_by_id(int(recipe_id))

    # First check if ALL ingredients are sufficient to make recipe
    for ingredient in recipe_details['extendedIngredients']:
        # Look up ingredient in inventory table
        check_ingredient = Inventory.query.filter(Inventory.ingredient_id == int(ingredient['id']), Inventory.user_id == session['user_id']).one()

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
    cooked_recipe = UserRecipe.query.filter(UserRecipe.recipe_id == int(recipe_id), UserRecipe.user_id == session['user_id']).first()
    cooked_recipe.status = 'cooked'

    db.session.commit()

    return jsonify({'result': True})


@app.route("/shopping_list", methods=["POST"])
def show_shopping_list():
    """Display shopping list of missing ingredients."""

    all_user_recipes = db.session.query(UserRecipe.recipe_id).filter(UserRecipe.user_id == session['user_id'], UserRecipe.status == 'needs_ingredients').all()
    new_shopping_list = ShoppingList(user_id=session['user_id'],
                                     has_shopped=False,
                                    )
    db.session.add(new_shopping_list)

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

    # Update status of recipes added to shopping list to 'in progress'
    update_recipes = UserRecipe.query.filter(UserRecipe.user_id == session['user_id'], UserRecipe.status == 'needs_ingredients').all()
    for recipe in update_recipes:
        recipe.status = 'in_progress'

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


@app.route("/confirm_list/<shopping_list_id>")
def confirm_purchases(shopping_list_id):

    list_ingredients = ListIngredient.query.filter(ListIngredient.shopping_list_id == shopping_list_id).all()

    all_ingredients = []

    for ingredient in list_ingredients:
        ingredient_id = ingredient.ingredient_id
        ingredient_qty = ingredient.aggregate_quantity
        ingredient_unit = ingredient.ingredient.base_unit
        ingredient_name = ingredient.ingredient.ingredient_name
        all_ingredients.append((ingredient_id, ingredient_qty, ingredient_unit, ingredient_name))

    return render_template("list_confirmation.html", ingredients=all_ingredients, shopping_list_id=shopping_list_id)


@app.route("/inventory", methods=["POST"])
def add_inventory():
    """ Adds purchased ingredients to inventory."""

    inventory = request.form.get("data")
    inventory_dict = json.loads(inventory)
    shopping_list_id = int(request.form.get("listId"))

    # Add each ingredient to inventory list
    for ingredient_id in inventory_dict:
        new_inventory = Inventory(user_id=session['user_id'],
                                  ingredient_id=int(ingredient_id),
                                  current_quantity=round(float(inventory_dict[ingredient_id]['ingredientQty']),2),
                                  )
        db.session.add(new_inventory)

    # Change status of shopping list since list has been used by user
    shopping_list = ShoppingList.query.filter(ShoppingList.list_id == shopping_list_id).one()
    shopping_list.has_shopped = True

    db.session.commit()

    return jsonify({'success': True})


@app.route("/display_inventory")
def display_current_inventory():
    """Displays user's current ingredients."""

    current_inventory = Inventory.query.filter(Inventory.user_id == session['user_id'], Inventory.current_quantity > 0).all()

    current_inventory_list = []

    for ingredient in current_inventory:
        current_quantity = ingredient.current_quantity
        base_unit = ingredient.ingredients.base_unit
        ingredient_name = ingredient.ingredients.ingredient_name
        current_inventory_list.append((current_quantity, base_unit, ingredient_name))

    return render_template("/display-inventory.html", current_inventory=current_inventory_list)


@app.route("/search_by_ingredient")
def show_search_by_results():

    # Retrieve list of selected ingredients by name and transform to search string
    search_ingredients = request.args.getlist("ingredients[]")
    ingredients = "%2C+".join(search_ingredients)

    search_results = search_api_by_ingredient(ingredients)

    # After getting search results, check if inventory quantity >= recipe quantity
    # since API only searches by ingredient name and doesn't include quantities.
    # Only display results that pass this criteria.

    # Filtered list of recipes to display to user
    show_recipes = []

    for recipe in search_results['results']:
        enough_ingredients = True

        for ingredient in recipe['usedIngredients']:
            check_ingredient = Inventory.query.filter(Inventory.ingredient_id == int(ingredient['id']), Inventory.user_id == session['user_id']).one()

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
            show_recipes.append(recipe)

    return render_template("recipes-by-ingredient.html", show_recipes=show_recipes)


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