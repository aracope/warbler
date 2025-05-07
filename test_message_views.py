"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        """Rollback changes after each test."""
        db.session.rollback()

    def test_add_message(self):
        """Test if a user can add a new message."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"})
            self.assertEqual(resp.status_code, 302)  # Redirect after posting

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")  # Check the message in DB

    def test_add_message_no_user(self):
        """Test if adding a message fails when not logged in."""
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Unauthorized"})
            self.assertEqual(resp.status_code, 302)  # Should redirect to login
            self.assertIn(b"login", resp.data)  # Check that redirect is to login page

    def test_delete_message(self):
        """Test if a user can delete their own message."""
        msg = Message(text="Message to delete", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(b"Message to delete", resp.data)  # Check message is deleted

    def test_delete_message_not_owner(self):
        """Test if a user cannot delete another user's message."""
        msg = Message(text="Another user's message", user_id=self.testuser.id)
        user2 = User.signup("testuser2", "test2@test.com", "testuser2", None)
        db.session.commit()
        
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user2.id  # Log in as a different user

            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 403)  # Forbidden to delete someone else's message

    def test_message_likes(self):
        """Test if a user can like and unlike a message."""
        msg = Message(text="Like me", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Like the message
            resp = c.post(f"/messages/{msg.id}/like", follow_redirects=True)
            self.assertIn(b"liked", resp.data)

            # Unlike the message
            resp = c.post(f"/messages/{msg.id}/like", follow_redirects=True)
            self.assertIn(b"unliked", resp.data)