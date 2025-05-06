import os
from unittest import TestCase

from models import db, connect_db, User, Message
from app import app, CURR_USER_KEY

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
app.config['WTF_CSRF_ENABLED'] = False

db.create_all()

class UserViewsTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        self.client = app.test_client()
        self.testuser = User.signup(
            username="testuser", 
            email="test@test.com",
            password="testuser",
            image_url=None)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()


    def test_profile_edit_form_display(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/users/profile")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Edit Your Profile', resp.data)


    def test_profile_edit_success(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/profile", data={
                "username": "newname",
                "email": "new@test.com",
                "image_url": "",
                "header_image_url": "",
                "bio": "New bio",
                "password": "testuser"
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Profile updated!", resp.data)
            self.assertIn(b"newname", resp.data)

    def test_profile_edit_wrong_password(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/profile", data={
                "username": "failname",
                "email": "fail@test.com",
                "image_url": "",
                "header_image_url": "",
                "bio": "Wrong",
                "password": "wrongpassword"
            }, follow_redirects=True)

            # Check if the error message is in the response
            self.assertIn(b"Incorrect password. Profile not updated.", resp.data)
            # Re-fetch the user from the database
            user = User.query.get(self.testuser.id)
            self.assertEqual(user.username, "testuser")  # Make sure the username didn't change
 
class HomepageTestCase(TestCase):
    def setUp(self):
        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()
        self.testuser = User.signup(
            username="testuser", 
            email="test@test.com",
            password="testuser",
            image_url=None)
        db.session.commit()

        self.testuser2 = User.signup(
            username="testuser2", 
            email="test2@test.com",
            password="testuser2",
            image_url=None)
        db.session.commit()

        # Create messages for users
        self.msg1 = Message(text="This is a message", user_id=self.testuser.id)
        self.msg2 = Message(text="This is another message", user_id=self.testuser2.id)
        db.session.add(self.msg1)
        db.session.add(self.msg2)
        db.session.commit()

        # Follow testuser2
        self.testuser.following.append(self.testuser2)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()

    def test_homepage_logged_in(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/')
            self.assertEqual(resp.status_code, 200)
            # Check that the messages displayed are from testuser and testuser2 (since testuser follows testuser2)
            self.assertIn(b"This is a message", resp.data)
            self.assertIn(b"This is another message", resp.data)

    def test_homepage_logged_out(self):
        with self.client as c:
            resp = c.get('/')
            self.assertEqual(resp.status_code, 200)
            # Check that the response contains the anonymous homepage message
            self.assertIn(b"New to Warbler?", resp.data)
            self.assertIn(b"Sign up now to get your own personalized timeline!", resp.data)