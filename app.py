import os
from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from forms import UserAddForm, LoginForm, MessageForm, UserEditForm
from models import db, connect_db, User, Message, Likes, bcrypt

# Constant to store the key used for the current user ID in the session
CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)
bcrypt.init_app(app)
db.create_all()
##############################################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """Before each request, check if the user is logged in.
    If logged in, add the current user to Flask's global 'g' object for easy access.
    This allows the user to be accessed easily in other parts of the app, such as templates.
    """
    if CURR_USER_KEY in session:
        # Retrieve user from DB using their ID in session
        user = User.query.get(session[CURR_USER_KEY])

         # Set the user to 'g.user', or None if not found
        g.user = user if user else None
    else:
        # If no user in session, set g.user to None
        g.user = None


def do_login(user):
    """Log in user by storing their user ID in the session."""
    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user by deleting their user ID from the session."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    If form is valid:
    - Create a new user and add to the database.
    - Commit the new user record to the database.
    - Log in the user.
    - Redirect to the homepage.
    
    If the form is invalid:
    - Show the signup form again with any validation errors.
    
    If the username already exists:
    - Flash a message to the user indicating the error and show the form again.
    """

    form = UserAddForm()

    # Check if the form has been submitted and is valid
    if form.validate_on_submit():
        try:
            # Create a new user instance with the data from the form
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                # Set a default image if not provided
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            # Commit the new user to the database
            db.session.commit()

        # Handle the case where the username already exists in the database
        except IntegrityError:
            flash("Username already taken", 'danger')

            # Return the signup form with error messages
            return render_template('users/signup.html', form=form)

        # Log the user in after successful signup
        do_login(user)

        return redirect("/")

    else:
        # If the form is not valid, render the signup form again
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login.
    If form is valid:
    - Check if the username and password match a user in the database.
    - Log the user in by storing their ID in the session.
    - Redirect to the homepage.
    
    If the form is invalid:
    - Show the login form again with error messages.
    
    If the username/password is incorrect:
    - Flash a message to the user indicating the login failure.
    """

    form = LoginForm()

    # Check if the form has been submitted and is valid
    if form.validate_on_submit():
        # Find user by username
        user = User.authenticate(form.username.data,
                                 form.password.data)

        # Check if user exists and password is correct
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            # Log the user in by storing their ID in the session
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect(f"/users/{user.id}")

        flash("Invalid credentials.", 'danger')

    # Render the login form if not valid
    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""
    # Call the do_logout function to clear the session
    do_logout()

    # Flash a success message
    flash("You have been logged out successfully.", "success")

    # Redirect to the login page
    return redirect('/login')


##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    # Retrieve the 'q' parameter from the query string for searching users
    search = request.args.get('q')

    # If 'q' is not provided, fetch all users from the database
    if not search:
        users = User.query.all()
    else:
        # Otherwise, filter users based on the username that contains the search query
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile page for a specific user identified by user_id."""
    # Retrieve user by their ID or return 404 if not found
    user = User.query.get_or_404(user_id)

    # Get the messages that the user has liked
    liked_messages = user.likes
    return render_template('users/show.html', user=user, liked_messages=liked_messages)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        # If not logged in, show an error message
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    # Render following page for the user
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    # If not logged in, show an error message
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""
    # If not logged in, show an error message
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)

    # Add the followed user to the logged-in user's following lis
    g.user.following.append(followed_user)
    # Commit the change to the database
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Allow the currently logged-in user to stop following another user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # Retrieve the user to stop following
    followed_user = User.query.get(follow_id)

    # Remove the followed user from the logged-in user's following list
    g.user.following.remove(followed_user)

    # Commit the change to the database
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")

@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # Create a form pre-filled with the current user's data
    form = UserEditForm(obj=g.user)

    # Check if the form has been submitted and is valid
    if form.validate_on_submit():
        # Verify current password
        if bcrypt.check_password_hash(g.user.password, form.password.data):
            # Update user details with new data from the form
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.image_url = form.image_url.data
            g.user.header_image_url = form.header_image_url.data
            g.user.bio = form.bio.data

            # Commit changes to the database
            db.session.commit()

            flash("Profile updated!", "success")
            return redirect(f"/users/{g.user.id}") 
        else:
            flash("Incorrect password. Profile not updated.", "danger")
            return render_template("users/edit.html", form=form, user_id=g.user.id)
        
    return render_template("users/edit.html", form=form, user_id=g.user.id)

@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete the currently logged-in user's account."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # Log the user out after account deletion
    do_logout()

    # Delete the user's record from the database
    db.session.delete(g.user)
    # Commit the change to the database
    db.session.commit()

    # Redirect to the signup page after account deletion
    return redirect("/signup")


##############################################################################
# Messages routes:
@app.route('/users/<int:user_id>/liked')
def liked_messages(user_id):
    """Show all the messages that the specified user has liked."""
    # Retrieve user by their ID or return 404 if not found
    user = User.query.get_or_404(user_id)

    # Get the user's liked messages
    liked_messages = user.likes
    return render_template('users/liked_messages.html', user=user, liked_messages=liked_messages)

@app.route('/messages/<int:message_id>/like', methods=["POST"])
def like_message(message_id):
    """Allow the logged-in user to like or unlike a message."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    # Check if the user has already liked the message
    like = Likes.query.filter_by(user_id=g.user.id, message_id=message_id).first()

    if like:
        # If already liked, remove the like from the database
        db.session.delete(like)
        flash("You unliked this message.", "success")
    else:
        new_like = Likes(user_id=g.user.id, message_id=message_id)

        # Add the new like to the session
        db.session.add(new_like)
        flash("You liked this message!", "success")
    
    # Commit changes to the database
    db.session.commit()
    return redirect("/")

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message: Show form if GET. If valid, post the message and redirect to user page."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    # Check if the form is valid
    if form.validate_on_submit():
        # Create a new message instance
        msg = Message(text=form.text.data)

        # Associate the new message with the logged-in user
        g.user.messages.append(msg)

        # Commit the new message to the database
        db.session.commit()
        flash("Message posted!", "success")
        return redirect(f"/users/{g.user.id}")  # <-- Redirect (302)

    return render_template('messages/new.html', form=form)

@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a specific message by its ID."""
    # Retrieve the message by its ID
    msg = Message.query.get(message_id)

    # Render the message details page
    return render_template('messages/show.html', message=msg)

@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a specific message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/"), 403

    # Retrieve the message by its ID
    msg = Message.query.get_or_404(message_id)

    if msg.user_id != g.user.id:
        flash("Access unauthorized.", "danger")
        return redirect("/"), 403

    # Delete the message from the database
    db.session.delete(msg)

    # Commit the deletion to the database
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """
    if g.user:
        # Get list of followed user IDs, including self
        following_ids = [u.id for u in g.user.following] + [g.user.id]

        # Fetch the 100 most recent messages from users the logged-in user follows
        messages = (Message
                    .query
                    .filter(Message.user_id.in_(following_ids))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        # Get the list of message likes by the user
        likes = [like.id for like in g.user.likes]

        # Render the homepage with messages and likes
        return render_template('home.html', messages=messages, likes=likes)

    else:
        # Render homepage for anonymous users
        return render_template('home-anon.html')


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
