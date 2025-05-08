"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

import os
from unittest import TestCase
from models import db, connect_db, Message, User
from app import app, db, CURR_USER_KEY

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"



db.create_all()
app.config['WTF_CSRF_ENABLED'] = False

class BaseTestCase(TestCase):
    """Base setup for all message tests."""

    def setUp(self):
        """Create test client, add sample user."""
        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(
            username="testuser",
            email="test@test.com",
            password="testuser",
            image_url=None
        )
        db.session.commit()
        
    def tearDown(self):
        """Rollback changes after each test."""
        db.session.rollback()

class TestMessageCreate(BaseTestCase):
    """Tests for creating messages."""

    def test_add_message(self):
        """Test if a user can add a new message."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"})
            self.assertEqual(resp.status_code, 302)

    def test_add_message_no_user(self):
        """Test if adding a message fails when not logged in."""
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Unauthorized"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Access unauthorized.", resp.data)

class TestMessageDelete(BaseTestCase):
    """Tests for deleting messages."""

    def setUp(self):
        """Set up message for deletion tests."""
        super().setUp()
        self.msg = Message(text="Message to delete", user_id=self.testuser.id)
        db.session.add(self.msg)
        db.session.commit()

    def test_delete_message(self):
        """Test if a user can delete their own message."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Re-fetching the message to avoid detached instance error
            self.msg = db.session.merge(self.msg)
            resp = c.post(f"/messages/{self.msg.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
    
    def test_delete_message_not_owner(self):
        """Test if a user cannot delete another user's message."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
        # Re-fetching the message to avoid detached instance error
        self.msg = db.session.merge(self.msg)
        other_user = User(username="otheruser", password="HASHED_PASSWORD")
        db.session.add(other_user)
        db.session.commit()

        resp = c.post(f"/messages/{self.msg.id}/delete", follow_redirects=True)
        self.assertEqual(resp.status_code, 403)  # Forbidden

class TestMessageLike(BaseTestCase):
    """Tests for liking messages."""

    def setUp(self):
        """Set up message for like tests."""
        super().setUp()
        self.msg = Message(text="Like me", user_id=self.testuser.id)
        db.session.add(self.msg)
        db.session.commit()
        self.msg = Message.query.get(self.msg.id)  # Attach to session

    def test_like_unlike_message(self):
        """Test if a user can like and unlike a message."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
            # Re-fetch user to ensure they are part of the session
            self.testuser = db.session.merge(self.testuser)
        
            resp = c.post(f"/messages/{self.msg.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(self.testuser.likes), 1)

            # Unlike the message
            resp = c.post(f"/messages/{self.msg.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(self.testuser.likes), 0)

    def test_like_without_login(self):
        """Test like/unlike when not logged in."""
        with self.client as c:
            resp = c.post(f"/messages/{self.msg.id}/like", follow_redirects=True)
            self.assertIn(b"Access unauthorized.", resp.data)