# IngrediYUM

IngrediYUM provides the hungry user with an all-in-one tool to discover recipes, compile shopping lists, and monitor ingredients. Integration of the Spoonacular API allows the user to search for recipes they want to cook. The user can then generate shopping lists with aggregated and categorized ingredients to make grocery shopping more convenient. As the user confirms ingredients purchased and recipes cooked, IngrediYUM will calculate the new ingredient amounts accordingly in the user’s current inventory. Lastly, the user can search for recipes by items in their inventory and generate shopping lists with missing ingredients to make it easy to make use of leftovers.

##Contents
* [Technologies](#technologies)
* [Features](#features)
* [Installation](#install)

## <a name="technologies"></a>Technologies

Backend: Python, Flask, PostgreSQL, SQLAlchemy<br/>
Frontend: JavaScript, jQuery, AJAX, Jinja2, Semantic UI, HTML5, CSS<br/>
API: Spoonacular API<br/>

## <a name="features"></a>Features

![alt tag](http://g.recordit.co/hj1bpmGT3D.gif)

This Flask application has a home page with a form for new users to sign up and a button for returning users to log in.<br>
Passwords are hashed and salted before storing in the PostgreSQL database.

![alt tag](http://g.recordit.co/JgF8w6mcPB.gif)

After the user logs in, a dashboard utilizing 3 SQLAlchemy queries displays the user's current inventory, pending shopping lists, and selected recipes to cook.<br>

A new user is assumed to not have existing inventory.<br>
The user can search for a new recipe by clicking on the "Search for New Recipe" button.

![alt tag](http://g.recordit.co/onauod7rc3.gif)

When the form is submitted, the server makes a call to the Spoonacular API using the user's inputs. The API returns the recipe data, which is then rendered for the user to review.

![alt tag](http://g.recordit.co/GbLEeCtK3Z.gif)

When the user clicks on the "Add Recipe" button, an AJAX call posts that recipe's id to the database and marks it as "needs ingredients". That recipe card is then hidden and a confirmation message is displayed using JQuery.

The user can add one or more recipes and proceed by clicking on the "Generate Shopping List" button. In this example, we'll also add a second recipe (not shown in the image above). The server then calls the Spoonacular API for recipe data for each recipe that needs ingredients.

![alt tag](http://g.recordit.co/BfCcsEwJAr.gif)

The API returns the recipe data and the ingredients are converted to a base unit, aggregated and categorized before rendering on the shopping list page.

![alt tag](http://g.recordit.co/Cy32HhXfnW.gif)

When the user returns to the dashboard, the queries now return the pending shopping list and selected recipe names.

Other features not shown:
- The user can confirm ingredients purchased in their pending shopping list(s).
- The user can view their selected recipes' details and indicate that they've cooked it.
- The user's current inventory will be updated accordingly: ingredients will be added when purchased and subtracted when recipes are cooked.
- The user can search for a new recipe using a leftover ingredient(s) and generate a shopping list with only missing ingredients to buy.

## <a name="install"></a>Installation

To run IngrediYUM:

Install PostgreSQL (Mac OSX)

Clone or fork this repo:

```
https://github.com/katliang/hackbright-project.git
```

Create and activate a virtual environment inside your IngrediYUM directory:

```
virtualenv env
source env/bin/activate
```

Install the dependencies:

```
pip install -r requirements.txt
```

Sign up to use the [Spoonacular API](https://spoonacular.com/food-api).

Save your API key in a file called <kbd>secrets.sh</kbd> using this format:

```
export SPOONACULAR_SECRET_KEY="YOURKEYHERE"
```

In the same file called <kbd>secrets.sh</kbd>, designate any secret key to use the Flask app:

```
export FLASK_SECRET_KEY="YOURKEYHERE"
```

Source your keys from your secrets.sh file into your virtual environment:

```
source secrets.sh
```

Set up the database and create the database tables:

```
createdb food
python seed.py
```

Run the app:

```
python server.py
```

You can now navigate to 'localhost:5000/' to access IngrediYUM.