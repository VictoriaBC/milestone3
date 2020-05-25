import os, math, datetime
from flask import Flask, render_template, redirect, request, url_for, session, flash
from flask_pymongo import PyMongo, pymongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["MONGO_DBNAME"] = 'task_manager'
app.config["MONGO_URI"] = 'mongodb+srv://vpb:Cuqa2956@myfirstcluster-zzbzp.mongodb.net/task_manager?retryWrites=true&w=majority'
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY')

mongo = PyMongo(app)

# Collections
users = mongo.db.users
recipes = mongo.db.recipes
deleted = mongo.db.deleted


@app.route('/base')
def intro():
    """
    Intro Page for the Website. Invites users to Start Browsing, 
    Sign-In or Register a new account
    """
    return render_template("intro.html")


@app.route('/get_recipes')    
def get_recipes():
    """
    Main Page for the Website. Displays all the recipes with pagination. 
    Also features a Most Popular section.
    """
    
    # Pagination 
    
    # # Recipes per page
    p_limit = 9
    current_page = int(request.args.get('current_page', 1))
    collection = mongo.db.recipes.count()
    pages = range(1, int(math.ceil(collection / p_limit)) + 1)
    total_page_no = int(math.ceil(collection/p_limit))
    all_recipes = mongo.db.recipes.find().skip((current_page -1)*p_limit).limit(p_limit).sort('_id', pymongo.DESCENDING)

    # Most Popular recipes - finds the recipes with the most favourite count and shows only the top 3
    recommended = mongo.db.recipes.find().sort("favourite_count", pymongo.DESCENDING).limit(3)
       
    return render_template("showall.html", all_recipes=all_recipes, current_page=current_page, pages=pages, total_page_no=total_page_no, recommended=recommended)


@app.route('/search')
def search():
    """
    Search Results Page. Uses MongoDB's wildcard text search to search for any words that appear in the recipes that are searched.
    The results are then paginated. If there are no results for the user's query, the Most Popular section appears as a suggestion.
    """
    # Wildcard text search index
    mongo.db.recipes.create_index([("$**", pymongo.TEXT)])
    #  Results per page
    p_limit = 9
    current_page = int(request.args.get('current_page', 1))
    #  Input term for search query
    word_search = request.args.get('word_search')
    #  Results for search sorted by ID
    results = mongo.db.recipes.find({'$text': {'$search': str(word_search)}}, {"score": {"$meta": 'textScore'}}).sort('_id', pymongo.ASCENDING).skip((current_page -1)*p_limit).limit(p_limit)
    # Pagination
    results_count = mongo.db.recipes.find({'$text': {'$search': str(word_search)}}).count()
    results_pages = range(1, int(math.ceil(results_count / p_limit)) + 1)
    total_page_no = int(math.ceil(results_count/p_limit))
    
    # Most Popular recipes - appear when there are no results to the user's query
    recommended = mongo.db.recipes.find().sort("favourite_count", pymongo.DESCENDING).limit(3)
    
    return render_template("search.html", 
                        p_limit = p_limit,
                        current_page=current_page, 
                        results_count=results_count,
                        word_search=word_search,
                        results=results,
                        results_pages=results_pages,
                        total_page_no=total_page_no,
                        recommended=recommended)    


####### CRUD FUNCTIONS #######


@app.route('/recipe_display/<recipe_id>')
def recipe_display(recipe_id):

    """
    Displays the recipe on a page of its own.
    """

    recipe = mongo.db.recipes.find_one({'_id': ObjectId(recipe_id)})

    return render_template('recipe_display.html', recipe=recipe)


@app.route('/edit_recipe/<recipe_id>')
def edit_recipe(recipe_id):
    """
    Path to edit the recipe currently being viewed. 
    User is brought to a form page based on the recipe's current fields.
    """
    
    # Checks if user is in session
    if 'user' in session:
    
        recipe = mongo.db.recipes.find_one({'_id': ObjectId(recipe_id)})
        
    else:
        flash("You must be logged in to Edit, Save or Delete a recipe!")
        return redirect(url_for('get_recipes')) 
    
    return render_template('editrecipe.html', recipe=recipe)


@app.route('/update_recipe/<recipe_id>', methods=["POST"])
def update_recipe(recipe_id):
    """
    Updates the recipe when the user submits the form displayed on the edit page.
    """
    
    # Captures the form data and updates the recipe.
    recipes.update_one({'_id': ObjectId(recipe_id), 
    }, {
        '$set': {
    'recipe_name':request.form.get('recipe_name'),
    'photo_url':request.form.get('photo_url'),
    'preptime': request.form.get('preptime'),
    'servings': request.form.get('servings'),
    'ingredients':request.form.getlist('ingredients'),
    'instructions':request.form.get('instructions'),
    'tags':request.form.getlist('tags')
    }
    })
                   
                                                        
    # Returns back to the recipe after update.
    flash('Recipe updated.')
    return redirect(url_for('recipe_display', recipe_id=recipe_id))


@app.route('/add_recipe')
def add_recipe():
    """
    Path to add a new recipe. User is brought to an empty form page.
    """
    
    recipes=mongo.db.recipes.find()
    
    return render_template('addrecipe.html', recipes=recipes)


@app.route('/insert_recipe', methods=["POST"])
def insert_recipe():  
    """
    Inserts new recipe to the Recipes collection when user submits
    the form from the add_recipe page.
    """
    
    # Identifies the current user in order to capture the author of the new recipe.
    user = users.find_one({"username": session['user']})
    new_recipe = recipes.insert_one({
        'recipe_name':request.form.get('recipe_name'),
        'photo_url':request.form.get('photo_url'),
        'preptime': request.form.get('preptime'),
        'servings': request.form.get('servings'),
        'calories':request.form.get('calories'),
        'fat':request.form.get('fat'),
        'satfat':request.form.get('satfat'),
        'carbs':request.form.get('carbs'),
        'fiber':request.form.get('fiber'),
        'sugar':request.form.get('sugar'),
        'protein':request.form.get('protein'),
        'ingredients':request.form.getlist('ingredients'),
        'instructions':request.form.get('instructions'),
        'tags':request.form.getlist('tags'),
        'added_on' : datetime.datetime.utcnow(), 
        'author' : {
            '_id': user['_id'],
            'username': user['username']},
        'favourite_count': int(0)
    })
    
    # Returns the new recipe after insertion.
    flash('Recipe Added.')
    return redirect(url_for('recipe_display', recipe_id = new_recipe.inserted_id))


@app.route('/delete_recipe/<recipe_id>')
def delete_recipe(recipe_id):
    """
    Deletes the recipe currently being viewed but first 
    adds the recipe to a collection called Deleted. 
    This allows the site Admin to reinstate the recipe if they see fit. 
    """
    
    # Checks if the user is in session
    if 'user' in session:
        # # Identifies the current user in order to identify who has deleted the recipe.
        user = users.find_one({"username": session['user']})
            
        deleted_recipe = recipes.find_one({'_id': ObjectId(recipe_id)})
        # # Inserts recipe to be deleted into Deleted collection
        deleted.insert_one(deleted_recipe)
        # # Updates the deleted recipe by identifying who has deleted it and when
        deleted.update_one({'_id': ObjectId(recipe_id)}, 
                                                {"$set" :
                                                    {"deleted_on" : datetime.datetime.utcnow(), 
                                                    "favourite_count": int(0),
                                                    "deleted_by" : {
                                                                '_id': user['_id'],
                                                                'username': user['username']}}
                                                })
        # Removes the recipe from the Recipes collection
        recipes.remove({'_id': ObjectId(recipe_id)})
        
        
        # Removes the deleted recipe from Users Favourites.
        users.update({}, 
                    {"$pull": {"favourite_recipes": ObjectId(recipe_id)}},
                    multi=True)
        
    else:
        flash("You must be logged in to Edit, Save or Delete a recipe!")
        return redirect(url_for('get_recipes'))
    
    
    flash('Recipe Deleted.')
    return redirect(url_for('get_recipes')) 


####### DELETED RECIPE FUNCTIONS #######    
    
@app.route('/deleted_recipe_display/<recipe_id>')
def deleted_recipe_display(recipe_id):
    
    """
    Displays the recipe on a page of its own.
    """
    
    deleted_recipe = mongo.db.deleted.find_one({'_id': ObjectId(recipe_id)})
    return render_template('deleted_recipe_display.html', deleted_recipe=deleted_recipe)    
    
    
@app.route('/restore_recipe/<recipe_id>')
def restore_recipe(recipe_id):
    """
    Restores the deleted recipe to the Recipe database and removes it from deleted. 
    Sets new fields in the recipe document stating who restored the recipe and when. 
    """
    
    # Checks if the user is in session
    if 'user' in session:
        
        # Checks if user is the Admin
        if session['user'] == "admin":
            # # Identifies the current user in order to identify who has deleted the recipe.
            user = users.find_one({"username": session['user']})
                
            restored_recipe = deleted.find_one({'_id': ObjectId(recipe_id)})
            # # Inserts recipe to be deleted into Deleted collection
            recipes.insert_one(restored_recipe)
            # # Updates the deleted recipe by identifying who has deleted it and when
            recipes.update_one({'_id': ObjectId(recipe_id)}, 
                                                    {"$set" :
                                                        {"restored_on" : datetime.datetime.utcnow(), 
                                                        "restored_by" : {
                                                                    '_id': user['_id'],
                                                                    'username': user['username']}}
                                                    })
            # Removes the recipe from the Deleted collection after restoration into Recipe collection
            deleted.remove({'_id': ObjectId(recipe_id)})
        else:
            flash("Only the Admin can restore recipes!")
            return redirect(url_for('get_recipes'))                
        
    else:
        flash("You must be logged in to Edit, Save or Delete a recipe!")
        return redirect(url_for('get_recipes'))
    flash('Recipe Restored.')
    return redirect(url_for('recipe_display', recipe_id=recipe_id))     


####### FAVOURITE RECIPES FUNCTIONS #######    

@app.route('/my_favourites/<user>')
def my_favourites(user):
    """
    My Favourites Page displays all the recipes the user has added as their favourites. 
    """
    # Check if user is logged in
    if 'user' in session:
        user_in_db = users.find_one({"username": user})
        favourites = mongo.db.users.find(user_in_db)
        
        # Defines favourite_recipes array from current User document
        favourites_recipes = user_in_db["favourite_recipes"]
        
        # Finds favourite recipes in Recipe collection in order to display full recipes
        favs = recipes.find({"_id" : {
                                    "$in" : favourites_recipes }
                            })
        
        # Most Popular recipes - appear when there are no results to the user's query
        recommended = mongo.db.recipes.find().sort("favourite_count", pymongo.DESCENDING).limit(3)
        
    else:
        flash("You must be logged in!")
        return redirect(url_for('get_recipes'))
        
    return render_template('my_favourites.html', user=user_in_db, favourites=favourites, favourites_recipes=favourites_recipes, favs=favs, recommended=recommended)

  
@app.route('/add_to_favourites/<recipe_id>', methods=["GET", "POST"])
def add_to_favourites(recipe_id):
    """
    Adds the current recipe to the current users "Favourites" array in the Users collection. 
    """
    # Checks if user is in session
    if 'user' in session:
        # Identifies the current user 
        user = users.find_one({"username": session['user']})
        
        favourites = user['favourite_recipes']
        
        # Makes sure the recipe is not already in the user's favourites and then adds to favourites
        if ObjectId(recipe_id) not in favourites:
            users.update_one({"username": session['user']}, 
                                                    {"$push" :
                                                        {"favourite_recipes" : ObjectId(recipe_id)}})
            
            recipes.update({'_id':ObjectId(recipe_id)},
                                                {'$inc': {'favourite_count': 1}})
            
        else:
            # If the recipe is already in the User's favourites, the below message is displayed
            flash("You have already added this recipe to your Favourites")
            return redirect(url_for('recipe_display', user=user['username'], recipe_id=recipe_id))
    else:
        flash("You must be logged in to Edit, Save or Delete a recipe!")
        return redirect(url_for('get_recipes'))
    
    
    flash('Added to My Favourites.')
    return redirect(url_for('recipe_display', user=user['username'], recipe_id=recipe_id))


@app.route('/remove_from_favourites/<recipe_id>', methods=["GET", "POST"])
def remove_from_favourites(recipe_id):
    """
    Removes the current recipe from the current users "Favourites" array in the Users collection. 
    """
    # Identifies the current user 
    user = users.find_one({"username": session['user']})
    
    favourites = user['favourite_recipes']
        
            
    # Identifies the recipe to be removed from the user's favourite
    # remove_recipe = recipes.find_one({'_id': ObjectId(recipe_id)})
        
    # Removes recipe from user's favourites
    if ObjectId(recipe_id) in favourites:
        users.update({"username": session['user']}, 
                                                {"$pull" :
                                                    {"favourite_recipes" : ObjectId(recipe_id)}})
                                                    
        recipes.update({'_id':ObjectId(recipe_id)},
                                                {'$inc': {'favourite_count': -1}})                                            
        flash('Removed from My Favourites.')
        return redirect(url_for('my_favourites', user=user['username'], recipe_id=recipe_id))
            
                                                        
    else:
        flash("You must be logged in to Edit, Save or Delete a recipe!")
        return redirect(url_for('get_recipes'))


####### USER FUNCTIONS #######    
    
# Login - taken and modified from Miroslav Svec's (username Miro) sessions from Slack DCD channel
@app.route('/login', methods=['GET'])
def login():
    """
    Logs the user into the website. 
    """

    # Check if user is not logged in already
    if 'user' in session:
        user_in_db = users.find_one({"username": session['user']})
        if user_in_db:
            # If so redirect user to their "My Favourites" page
            flash("You are logged in already!")
            return redirect(url_for('my_favourites', user=user_in_db['username']))
    else:
        # Render the page for user to be able to log in
        return render_template("login.html")


# # Taken and modified from Miroslav Svec's (username Miro) sessions from Slack DCD channel
@app.route('/user_auth', methods=['POST'])
def user_auth():
    """
    Checks user login details from login form
    """
    
    form = request.form.to_dict()
    user_in_db = users.find_one({"username": form['username']})
    # Check for user in database
    if user_in_db:
        # If passwords match (hashed / real password)
        if check_password_hash(user_in_db['password'], form['user_password']):
            # Log user in (add to session)
            session['user'] = form['username']
            # If the user is admin redirect him to admin area
            if session['user'] == "admin":
                return redirect(url_for('admin'))
            else:
                flash("You were logged in!")
                return redirect(url_for('my_favourites', user=user_in_db['username']))

        else:
            flash("Wrong password or user name!")
            return redirect(url_for('login'))
    else:
        flash("You must be registered!")
        return redirect(url_for('register'))
# Insert/get tasks
@app.route('/')
@app.route('/get_tasks')
def get_tasks():
    return render_template("tasks.html", tasks=mongo.db.tasks.find())

@app.route('/insert_task', methods=['POST'])
def insert_task():
    tasks = mongo.db.tasks
    tasks.insert_one(request.form.to_dict())
    return redirect(url_for('get_tasks'))

# Sign up - taken and modified from Miroslav Svec's (username Miro) sessions from Slack DCD channel
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registers new users to the website.
    """
    tasks = mongo.db.users
    
    # Check if user is not logged in already
    if 'user' in session:
        flash('You are already signed in!')
        return redirect(url_for('get_recipes'))
    if request.method == 'POST':
        form = request.form.to_dict()
        # Check if the password and password1 actually match
        if form['user_password'] == form['user_password1']:
            # If so try to find the user in db
            user = users.find_one({"username": form['username']})
            if user:
                flash("That username already exists!")
                return redirect(url_for('register'))
            # If user does not exist register new user
            else:
                # Hash password
                hash_pass = generate_password_hash(form['user_password'])
                # Create new user with hashed password
                users.insert_one(
                    {
                        'username': form['username'],
                        'email': form['email'],
                        'password': hash_pass,
                        'favourite_recipes': []
                    }
                )
                # Check if user is actually saved
                user_in_db = users.find_one(
                    {"username": form['username']})
                if user_in_db:
                    # Log user in (add to session)
                    session['user'] = user_in_db['username']
                    return redirect(url_for('my_favourites', user=user_in_db['username']))
                else:
                    flash("There was a problem saving your profile")
                    return redirect(url_for('register'))

        else:
            flash("Passwords dont match!")
            return redirect(url_for('register'))

    return render_template("register.html", register=mongo.db.users.find())


# Log out- taken and modified from Miroslav Svec's (username Miro) sessions from Slack DCD channel
@app.route('/logout')
def logout():
    """
    Logs the users out of the session
    """
    
    
    # Clear the session
    session.clear()
    flash('You have been logged out!')
    return redirect(url_for('get_recipes'))


####### PROFILE/ADMIN VIEWS #######     
    
    
@app.route('/profile/<user>')
def profile(user):
    """
    Users Profile page displays the recipes the user has created.
    """
    
    users_profile = users.find({'username': user})
    
    # Pagination if Users recipes exceed 9 recipes per page
    
    # Results per page
    p_limit = 9
    current_page = int(request.args.get('current_page', 1))
    users_recipes_count = recipes.find({'author.username': user}).count()
    pages = range(1, int(math.ceil(users_recipes_count / p_limit)) + 1)
    total_page_no = int(math.ceil(users_recipes_count/p_limit))
    users_recipes = recipes.find({'author.username': user}).skip((current_page -1)*p_limit).limit(p_limit)

    
    return render_template('profile.html', user=user, 
                                           users_profile=users_profile, 
                                           users_recipes=users_recipes,
                                           users_recipes_count=users_recipes_count,
                                           current_page=current_page, pages=pages, total_page_no=total_page_no)


@app.route('/admin')
def admin():
    """
    Admin area. Allows the Admin to check on statistics about the Users, Recipes and Deleted recipes collections.
    """
    # Checks if user is the Admin
    if session['user'] == "admin":
        # Queries for Admin reports
        users = mongo.db.users.find()
        recipes = mongo.db.recipes.find()
        deleted = mongo.db.deleted.find()
        
        return render_template('admin.html', users=users, recipes=recipes, deleted=deleted)
    else:
        flash('Only Admins can access this page!')
        return redirect(url_for('get_recipes'))



if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=False)