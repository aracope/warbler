"""User model tests."""

# run these tests like:
#
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
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.client = app.test_client()
        self.testuser = User.signup(username="testuser", 
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None,
                                    header_image_url=None)
        db.session.commit()

        # Create a sample message
        message = Message(text="Test message", user_id=self.testuser.id)
        db.session.add(message)
        db.session.commit()  # Commit the message to the database

    def tearDown(self):
        db.session.remove()

    def test_user_model(self):
        # User should have no messages & no followers
        self.assertEqual(len(self.testuser.messages), 1)
        self.assertEqual(len(self.testuser.followers), 0)

    def test_user_following(self):
        user2 = User.signup("testuser2", "test2@test.com", "password", None)
        db.session.commit()

        self.testuser.following.append(user2)
        db.session.commit()

        self.assertTrue(self.testuser.is_following(user2))
        self.assertFalse(user2.is_following(self.testuser))

    def test_liking_message(self):
        user = User.query.first()  
        message = Message.query.first()

        # Create a Like object that links the user and the message
        like = Likes(user_id=user.id, message_id=message.id)

        db.session.add(like)
        db.session.commit()

    def test_user_repr(self):
        self.assertEqual(repr(self.testuser), f"<User #{self.testuser.id}: testuser, test@test.com>")
