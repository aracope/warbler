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
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        self.client = app.test_client()
        self.testuser = User.signup(username="testuser", 
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    def test_message_model(self):
        """Test if the message model is working correctly."""
        msg = Message(text="Hello", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        self.assertEqual(len(self.testuser.messages), 1)
        self.assertEqual(self.testuser.messages[0].text, "Hello")
