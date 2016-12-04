# IngrediYUM

IngrediYUM provides the hungry user with an all-in-one tool to discover recipes, compile shopping lists, and monitor ingredients. Integration of the Spoonacular API allows the user to search for recipes they want to cook. The user can then generate shopping lists with aggregated and categorized ingredients to make grocery shopping more convenient. As the user confirms ingredients purchased and recipes cooked, IngrediYUM will calculate the new ingredient amounts accordingly in the user’s current inventory. Lastly, the user can search for recipes by items in their inventory and generate shopping lists with missing ingredients to make it easy to make use of leftovers.

##Contents
* [Technologies](#technologies)
* [Installation](#install)

## <a name="technologies"></a>Technologies

Backend: Python, Flask, PostgreSQL, SQLAlchemy<br/>
Frontend: JavaScript, jQuery, AJAX, Jinja2, Semantic UI, HTML5, CSS<br/>
API: Spoonacular API<br/>

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