"""User model tests."""

# run these tests like:
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from app import app
from models import db, User, Message, Follows, Likes

# Use test database
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Configure app for testing
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

class UserModelTestCase(TestCase):
    """Test for the User model and related functionality.

    Includes tests for user creation, following, liking messages, and model representation.
    """

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        # Create a test client and a sample user
        self.client = app.test_client()
        self.testuser = User.signup(username="testuser", 
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None,
                                    header_image_url=None)
        db.session.commit()

        # Create a sample message associated with the test user
        message = Message(text="Test message", user_id=self.testuser.id)
        db.session.add(message)

        # Commit the message to the database
        db.session.commit()  

    def tearDown(self):
        """Rollback the session after each test to ensure no changes persist."""
        db.session.remove()

    def test_user_model(self):
        """Test basic user model attributes (messages, followers)."""
        # User should have 1 message and no followers initially
        self.assertEqual(len(self.testuser.messages), 1)
        self.assertEqual(len(self.testuser.followers), 0)

    def test_user_following(self):
        """Test the following relationship between users."""
        # Create a second user and make the first user follow them
        user2 = User.signup("testuser2", "test2@test.com", "password", None)
        db.session.commit()

        self.testuser.following.append(user2)
        db.session.commit()

        # Check if the first user is following the second user
        self.assertTrue(self.testuser.is_following(user2))

        # Second user should not follow the first
        self.assertFalse(user2.is_following(self.testuser))

    def test_liking_message(self):
        """Test if a user can like a message."""
        # Get the first user
        user = User.query.first() 

        # Get the first message 
        message = Message.query.first()

        # Create a Like object that links the user and the message
        like = Likes(user_id=user.id, message_id=message.id)

        db.session.add(like)
        db.session.commit()

    def test_user_repr(self):
        """Test the string representation of the user object."""
        # Verify that the user representation matches the expected format
        self.assertEqual(repr(self.testuser), f"<User #{self.testuser.id}: testuser, test@test.com>")
