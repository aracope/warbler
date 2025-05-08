import os
from unittest import TestCase

from models import db, connect_db, User, Message
from app import app, CURR_USER_KEY

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
app.config['WTF_CSRF_ENABLED'] = False

db.create_all()

class UserViewsTestCase(TestCase):
    """Test the views related to user actions like login and profile editing."""

    def setUp(self):
        """Set up the test environment by creating a test user."""
        # Drop all existing tables and create them fresh for the tests
        db.drop_all()
        db.create_all()

        # Create a test client and a sample user
        self.client = app.test_client()
        self.testuser = User.signup(
            username="testuser", 
            email="test@test.com",
            password="testuser",
            image_url=None)
        db.session.commit()

    def tearDown(self):
        """Rollback the session after each test to avoid persistence of changes."""
        db.session.rollback()

    def test_login(self):
        """Test user login functionality for a valid user."""
    
        with self.client as c:
            # Send a POST request to log the user in
            resp = c.post("/login", data={
                "username": self.testuser.username,
                "password": "testuser"
        }, follow_redirects=True)

            # Check if login was successful
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello, testuser!", resp.get_data(as_text=True))

    def test_profile_edit_form_display(self):
        """Test if the profile edit form displays correctly when the user is logged in."""
        with self.client as c:
            # Set the current user session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Request the profile edit page
            resp = c.get("/users/profile")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Edit Your Profile', resp.data)

    def test_profile_edit_success(self):
        """Test successful profile update with new information."""
        with self.client as c:
            # Set the current user session
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Send a POST request to update the profile information
            resp = c.post("/users/profile", data={
                "username": "newname",
                "email": "new@test.com",
                "image_url": "",
                "header_image_url": "",
                "bio": "New bio",
                "password": "testuser"
            }, follow_redirects=True)

            # Check that the profile update was successful
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Profile updated!", resp.data)
            self.assertIn(b"newname", resp.data)

            # Check if the database reflects the profile changes
            user = User.query.get(self.testuser.id)
            self.assertEqual(user.username, "newname")
            self.assertEqual(user.bio, "New bio")
            self.assertEqual(user.email, "new@test.com")

  