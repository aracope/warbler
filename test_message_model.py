"""Message model tests."""

import os
from unittest import TestCase
from app import app
from models import db, Message, User

# Use test database
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Configure app for testing
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True

class MessageModelTestCase(TestCase):
    """Test the Message model's functionality, such as creating messages and associating them with users."""

    def setUp(self):
        """Set up the test environment by creating a test user and initializing the test client."""
        # Drop all existing tables and create them fresh for the tests
        db.drop_all()
        db.create_all()

        # Create a test client and a sample user
        self.client = app.test_client()
        self.testuser = User.signup(username="testuser", 
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        db.session.commit()

    def tearDown(self):
        """Rollback the session after each test to avoid persistence of changes."""
        db.session.remove()

    def test_message_model(self):
        """Test the functionality of the Message model, including creating and associating messages."""
        # Create a new message for the test user
        msg = Message(text="Hello", user_id=self.testuser.id)

        # Add and commit the message to the database
        db.session.add(msg)
        db.session.commit()

        # Check that the user has one message and its text is correct
        self.assertEqual(len(self.testuser.messages), 1)
        self.assertEqual(self.testuser.messages[0].text, "Hello")
