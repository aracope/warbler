"""Message View tests."""

# run these tests like:
#    FLASK_ENV=production python -m unittest test_message_views.py
'''
Command for all test files:
    python -m unittest test_user_model.py
    FLASK_ENV=production python -m unittest test_message_views.py
    python -m unittest test_message_model.py
    python -m unittest test_user_views.py
'''
import os
from unittest import TestCase
from models import db, connect_db, Message, User
from app import app, db, CURR_USER_KEY

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

db.create_all()
app.config['WTF_CSRF_ENABLED'] = False

class BaseTestCase(TestCase):
    """Base setup for all message-related tests.

    This sets up the test client and creates a sample user for all tests."""

    def setUp(self):
        """Set up the test environment by creating a test user."""
        # Clear any existing data in the database
        User.query.delete()
        Message.query.delete()

        # Create a test client and test user
        self.client = app.test_client()

        self.testuser = User.signup(
            username="testuser",
            email="test@test.com",
            # Password should be hashed in the actual app
            password="testuser",
            image_url=None
        )
        db.session.commit()

        # Attach to session
        self.testuser = db.session.merge(self.testuser)  
        
    def tearDown(self):
        """Rollback changes after each test."""
        db.session.rollback()
        # Fully clear the session
        db.session.expunge_all()  

class TestMessageCreate(BaseTestCase):
    """Tests for creating messages."""

    def test_add_message(self):
        """Test for creating messages.
        
        This includes tests for adding new messages and handling unauthorized access.
        """
        with self.client as c:
            with c.session_transaction() as sess:
                # Simulate logged-in user
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Expect redirection after successful message creation
            self.assertEqual(resp.status_code, 302)

    def test_add_message_no_user(self):
        """Test if adding a message fails when no user is logged in."""
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Unauthorized"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            # Check for access denied message
            self.assertIn(b"Access unauthorized.", resp.data)

class TestMessageDelete(BaseTestCase):
    """Set up message for deletion tests.
        
        These tests ensure that users can delete their own messages but not others'.
    """
    def setUp(self):
        super().setUp()

        # Create a message to be deleted in the tests
        self.msg = Message(text="Message to delete", user_id=self.testuser.id)

        db.session.add(self.msg)
        db.session.commit()
        # Store the ID only
        self.msg_id = self.msg.id  

    def test_delete_message(self):
        """Test if a user can delete their own message."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Re-fetching the message to avoid detached instance error
            msg = Message.query.get(self.msg_id)
            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            # Expect success
            self.assertEqual(resp.status_code, 200)
            # Confirm deletion
            self.assertIsNone(Message.query.get(self.msg_id))  
    
    def test_delete_message_not_owner(self):
        """Test if a user cannot delete another user's message."""
        with self.client as c:
            other_user = User.signup(
                username="otheruser", 
                email="otheruser@test.com",
                password="HASHED_PASSWORD", 
                image_url=None
            )
            db.session.commit()

            with c.session_transaction() as sess:
                # Log in as the other user
                sess[CURR_USER_KEY] = other_user.id  

            # Re-fetch
            resp = c.post(f"/messages/{self.msg_id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 403) 

class TestMessageLike(BaseTestCase):
    """Tests for liking messages."""

    def setUp(self):
        """Set up message for like tests.
        
        These tests check if users can like/unlike messages and if unauthorized access is handled properly.
        """
        super().setUp()
        #Set up message for like tests.
        self.msg = Message(text="Like me", user_id=self.testuser.id)

        # Attach to session
        db.session.add(self.msg)
        db.session.commit()
        # Store the ID only
        self.msg_id = self.msg.id  

    def test_like_unlike_message(self):
        """Test if a user can like and unlike a message."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
            # Fresh query each time  
            resp = c.post(f"/messages/{self.msg_id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # Re-fetch user to ensure they are part of the session
            user = User.query.get(self.testuser.id)
            self.assertEqual(len(user.likes), 1)

            # Unlike the message
            resp = c.post(f"/messages/{self.msg_id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # Re-fetch user and verify like removal
            user = User.query.get(self.testuser.id)
            self.assertEqual(len(user.likes), 0)

    def test_like_without_login(self):
        """Test like/unlike when not logged in."""
        with self.client as c:
            resp = c.post(f"/messages/{self.msg_id}/like", follow_redirects=True)
            
            # Ensure unauthorized access message appears
            self.assertIn(b"Access unauthorized.", resp.data)