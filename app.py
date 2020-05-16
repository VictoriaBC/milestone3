import os
from flask import Flask, render_template, request, flash, session, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import bcrypt

# Create an instance of flask and assign it to 'app'.
app = Flask(__name__)

# Initilize connection to MongoDB.
app.config["MONGO_DBNAME"] = 'Beer-Time'
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.secret_key = os.environ.get('SECRET_KEY')
mongo = PyMongo(app)


# Home page
@app.route('/')
def index():
    """
    Renders the home page for the website.
    """
    try:
        users = mongo.db.users
        return render_template("pages/index.html", body_id="home-page",
                               page_title="Home", current_user=users.find_one(
                                   {'name': session['username']}))
    except:
        return render_template("pages/index.html", body_id="home-page", page_title="Home")


# All beers page
@app.route('/beers')
def beers():
    """
    Renders beers page where all beers in DB are displayed for the user, code checks
    for current user favourites and makes data available for front-end.
    """
    try:
        users = mongo.db.users
        current_user_obj = users.find_one(
            {'name': session['username'].lower()})
        if len(current_user_obj['favourites']) != 0:
            current_user_favourites = current_user_obj['favourites']
        favourite_beers_id = []

        if len(current_user_obj['favourites']) != 0:
            for fav in current_user_favourites:
                current_beer = mongo.db.beers.find_one({'_id': fav})
                current_beer_id = current_beer['_id']
                favourite_beers_id.append(current_beer_id)

        return render_template("pages/beers/all-beers.html", favourite_beers_id=favourite_beers_id,
                               beers=mongo.db.beers.find(), body_id="all-beers",
                               current_user=users.find_one({'name': session['username'].lower()}))
    except:
        return redirect(url_for('create_account'))

# My list page
@app.route('/my-list', methods=["GET", "POST"])
def my_list():
    """
    Renders the my-list page showing the user which beers they have
    in their favourites array.
    """
    users = mongo.db.users
    current_user_obj = users.find_one({'name': session['username'].lower()})
    current_user_favourites = current_user_obj['favourites']
    favourite_beers = []
    favourite_beers_id = []

    if len(current_user_obj['favourites']) != 0:
        for fav in current_user_favourites:
            current_beer = mongo.db.beers.find_one({'_id': fav})
            current_beer_id = current_beer['_id']
            favourite_beers_id.append(current_beer_id)

    for fav in current_user_favourites:
        current_beer = mongo.db.beers.find_one({'_id': fav})
        favourite_beers.append(current_beer)

    return render_template("pages/my-list.html", body_id="my-list",
                           page_title="My List", favourite_beers_id=favourite_beers_id,
                           favourite_beers=favourite_beers, current_user=users.find_one(
                               {'name': session['username'].lower()}))

# Add to favourites route
@app.route('/add-to-favourites/<beer_id>', methods=["POST"])
def add_to_favourites(beer_id):
    """
    Add the beer_id into the current users favourites array.
    """
    users = mongo.db.users
    current_user_obj = users.find_one({'name': session['username'].lower()})
    mongo.db.users.update(
        current_user_obj, {"$push": {"favourites": ObjectId(beer_id)}})
    return redirect(url_for('my_list'))

# Remove from favourites route
@app.route('/remove-from-favourites/<beer_id>', methods=["POST"])
def remove_from_favourites(beer_id):
    """
    Remove the beer_id from the current users favourites array.
    """
    users = mongo.db.users
    current_user_obj = users.find_one({'name': session['username'].lower()})
    mongo.db.users.update(
        current_user_obj, {"$pull": {"favourites": ObjectId(beer_id)}})
    return redirect(url_for('my_list'))

# Beer page
@app.route('/beer/<beer_id>')
def beer_page(beer_id):
    """
    Constructs page for individual beer,
    makes reviews and favourite functionality available for front end.
    """
    users = mongo.db.users
    the_beer = mongo.db.beers.find_one({"_id": ObjectId(beer_id)})
    you_might_like = mongo.db.beers.find().limit(3)
    test = mongo.db.reviews.find({'beer_id': ObjectId(beer_id)})
    reviews = []
    current_user_obj = users.find_one({'name': session['username'].lower()})
    current_user_favourites = current_user_obj['favourites']
    favourite_beers = []
    favourite_beers_id = []
    if len(current_user_obj['favourites']) != 0:
        for fav in current_user_favourites:
            current_beer = mongo.db.beers.find_one({'_id': fav})
            current_beer_id = current_beer['_id']
            favourite_beers_id.append(current_beer_id)
    for fav in current_user_favourites:
        current_beer = mongo.db.beers.find_one({'_id': fav})
        favourite_beers.append(current_beer)
    cur = test
    for i in cur:
        reviews.append(i)
    return render_template('pages/beers/beer.html',
                           favourite_beers_id=favourite_beers_id, beer=the_beer,
                           beer_reviews=reviews, you_might_like=you_might_like,
                           body_id="beer-product", current_user=users.find_one(
                               {'name': session['username']}))

# Add Review route
@app.route('/review/add/<beer_id>', methods=["GET", "POST"])
def add_review(beer_id):
    """
    Adds user review into the database.
    """
    mongo.db.reviews.insert({
        'name': request.form.get('name'),
        'review': request.form.get('review'),
        'beer_id': ObjectId(beer_id),
    })
    return redirect(url_for('beer_page', beer_id=beer_id))

# Delete Review route
@app.route('/review/delete/<review_id>', methods=["GET", "POST"])
def delete_review(review_id):
    """
    Removes user review from the database.
    """
    mongo.db.reviews.remove({'_id': ObjectId(review_id)})
    return redirect(url_for('beers'))

# Edit Review page
@app.route('/review/edit/<review_id>', methods=["GET", "POST"])
def edit_review(review_id):
    """
    Renders edit page and handles editing user reviews in the database.
    """
    if request.method == 'POST':
        mongo.db.reviews.update({'_id': ObjectId(review_id)}, {
            '$set': {'review': request.form.get('review')}})
        return redirect(url_for('edit_review', review_id=review_id))
    users = mongo.db.users
    review = mongo.db.reviews.find({"_id": ObjectId(review_id)})
    return render_template("pages/edit-review.html",
                           body_id="edit-review-page", review=review, review_id=review_id,
                           current_user=users.find_one({'name': session['username']}))

# Add beer page
@app.route('/beer/add', methods=["GET", "POST"])
def add_beer():
    """
    Add a beer into the database
    """
    if request.method == 'POST':
        mongo.db.beers.insert_one(request.form.to_dict())
        return redirect(url_for('beers'))
    users = mongo.db.users
    return render_template('pages/beers/add-beer.html',
                           body_id="add-beer", types=mongo.db.types.find(),
                           current_user=users.find_one(
                               {'name': session['username'].lower()}))

# Edit beer page
@app.route('/beer/edit/<beer_id>', methods=["GET", "POST"])
def edit_beer(beer_id):
    """
    Edit a beer in the database
    """
    if request.method == 'POST':
        beer = mongo.db.beers
        beer.update({'_id': ObjectId(beer_id)},
                    {'name': request.form.get('name'),
                     'brewery': request.form.get('brewery'),
                     'type': request.form.get('type'),
                     'excerpt': request.form.get('excerpt'),
                     'notes': request.form.get('notes'),
                     'abv': request.form.get('abv'),
                     'image': request.form.get('image')})
        return redirect(url_for('beers'))
    users = mongo.db.users
    the_beer = mongo.db.beers.find_one({"_id": ObjectId(beer_id)})
    all_types = mongo.db.types.find()
    return render_template('pages/beers/edit-beer.html',
                           body_id='edit-page', beer=the_beer,
                           types=all_types, current_user=users.find_one(
                               {'name': session['username']}))

# Delete beer route
@app.route('/beer/delete/<beer_id>')
def delete_beer(beer_id):
    """
    Delete a beer from the database
    """
    mongo.db.beers.remove({'_id': ObjectId(beer_id)})
    return redirect(url_for('beers'))

# Register Account page
@app.route('/register', methods=["GET", "POST"])
def create_account():
    """
    Renders account register page and handles account registration,
    inserting new user into the database upon creation.
    """
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})
        favourites_array = []
        password = request.form['password']
        repeat_password = request.form['repeat_password']

        if password == repeat_password:
            if existing_user is None:
                hashpass = bcrypt.hashpw(
                    request.form['password'].encode('utf-8'), bcrypt.gensalt())
                users.insert({
                    'name': request.form['username'].lower(),
                    'password': hashpass,
                    'favourites': favourites_array
                })
                session['username'] = request.form['username']
                return redirect(url_for('index'))
            flash('That username already exists, try something else.')
        flash('The passwords dont match.')
    return render_template("pages/account-nav.html",
                           body_id="register-page", page_title="Create an Account")

# Sign-in page
@app.route('/sign-in', methods=["GET", "POST"])
def sign_in():
    """
    Renders sign-in page and handles user sign in attempts.
    """
    if request.method == 'POST':
        users = mongo.db.users
        login_user = users.find_one({'name': request.form['username'].lower()})

        if login_user:
            if bcrypt.hashpw(request.form['password'].encode('utf-8'),
                             login_user['password']) == login_user['password']:
                session['username'] = request.form['username']
                return redirect(url_for('index'))
            flash('That username/password combination was incorrect')
            return redirect(url_for('sign_in'))
    return render_template("pages/account-nav.html", body_id="sign-in", page_title="Sign In")

# sign-out route
@app.route('/sign-out')
def sign_out():
    """
    This function clears the session when the route is accessed.
    """
    session.clear()
    return redirect('/')

# Contact Page
@app.route('/contact', methods=["GET", "POST"])
def contact():
    """
    Renders the contact page and flashes responses based on inputs.
    """
    try:
        users = mongo.db.users
        if request.method == "POST":
            flash("Thanks {} we have received your message! A member of our team will be in touch shortly".format(
                request.form["name"]))
        return render_template("pages/contact-us.html",
                               body_id="contact-page", page_title="Contact Us",
                               current_user=users.find_one({'name': session['username']}))
    except:
        if request.method == "POST":
            flash("Thanks {} we have received your message! A member of our team will be in touch shortly".format(
                request.form["name"]))
        return render_template("pages/contact-us.html",
                               body_id="contact-page", page_title="Contact Us")

# 404 page
@app.errorhandler(404)
def page_not_found(error):
    """
    Renders an error page with 404 message.
    """
    error_message = str(error)
    return render_template('pages/error-page.html', error_message=error_message), 404

# 500 page
@app.errorhandler(500)
def server_error(error):
    """
    Renders an error page with 500 message.
    """
    error_message = str(error)
    return render_template('pages/error-page.html', error_message=error_message), 500


if __name__ == '__main__':
    app.run(host=os.getenv('IP'), port=os.getenv('PORT'), debug=os.getenv('FLASK_DEBUG'))