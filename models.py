"""SQLAlchemy models for Warbler."""
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

# Initialize the database and bcrypt for password hashing
db = SQLAlchemy()
bcrypt = Bcrypt()

class Follows(db.Model):
    """Represents a follow relationship between users."""
    __tablename__ = 'follows'

    # ID of the user being followed
    user_being_followed_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    # ID of the user who is following
    user_following_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )


class Likes(db.Model):
    """Mapping users liking specific warbles/messages."""
    __tablename__ = 'likes' 

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ID of the user who liked the messag
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade')
    )

    # ID of the liked message
    message_id = db.Column(
        db.Integer,
        db.ForeignKey('messages.id', ondelete='cascade')
    )

class User(db.Model):
    """Represents a user in the system."""
    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # Email of the user, must be unique
    email = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
    )

    # Username of the user, must be unique
    username = db.Column(
        db.String(50),
        nullable=False,
        unique=True
    )

    # Profile image URL, defaults to a default profile image
    image_url = db.Column(
        db.String(50),
        nullable=True,
        default="/static/images/default-pic.png"
    )

    # Header image URL, defaults to a default header image
    header_image_url = db.Column(
        db.Text,
         nullable=True,
        default="/static/images/warbler-hero.jpg"
    )

    # Bio of the user
    bio = db.Column(
        db.Text,
    )

    # Location of the user
    location = db.Column(
        db.Text,
    )

    # Password of the user (hashed)
    password = db.Column(
        db.Text,
        nullable=False,
    )

    # Establishing the many-to-many relationship with Messages through Likes
    likes = db.relationship('Message',
                            secondary='likes',
                            backref='liked_by')

    # Relationship for the messages created by this user
    messages = db.relationship('Message')

    # Relationship for the users that this user is following (many-to-many)
    followers = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follows.user_being_followed_id == id),
        secondaryjoin=(Follows.user_following_id == id)
    )

    # Relationship for the users that are following this user (many-to-many)
    following = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follows.user_following_id == id),
        secondaryjoin=(Follows.user_being_followed_id == id)
    )

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    def is_following(self, user):
        """Checks if the current user is following the given user."""
        return user in self.following

    def is_followed_by(self, user):
        """Checks if the current user is followed by the given user."""
        return user in self.followers

    @classmethod
    def signup(cls, username, email, password, image_url=None, header_image_url=None):
        """Signs up a new user by hashing the password and saving to the database.
        """
        # Hash the user's password
        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        # Create a new user object
        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url or "/static/images/default-pic.png",
        )

        # If provided, set the header image UR
        if header_image_url is not None:
            user.header_image_url = header_image_url

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Authenticate a user by checking the username and password hash.
        """
        # Find user by username
        user = cls.query.filter_by(username=username).first()

        # Check if password is correct
        if user and bcrypt.check_password_hash(user.password, password):
            # Return the authenticated user
            return user
        # Return False if authentication fails
        return False


class Message(db.Model):
    """An individual message ("warble")."""
    __tablename__ = 'messages'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # Text of the message (maximum 140 characters)
    text = db.Column(
        db.String(140),
        nullable=False,
    )

    # Timestamp of when the message was created
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow(),
    )

    # ID of the user who posted the message
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    # Relationship to the user who posted this message
    user = db.relationship('User')


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
