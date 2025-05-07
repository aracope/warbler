import os
from unittest import TestCase

from models import db, connect_db, User, Message
from app import app, CURR_USER_KEY

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"
app.config['WTF_CSRF_ENABLED'] = False

db.create_all()

class UserViewsTestCase(TestCase):
    def setUp(self):
        db.drop_all()
        db.create_all()

        self.client = app.test_client()
        self.testuser = User.signup(
            username="testuser", 
            email="test@test.com",
            password="testuser",
            image_url=None)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()

    def test_login(self):
        with self.client as c:
            resp = c.post("/login", data={"username": "testuser", "password": "testuser"})
            self.assertEqual(resp.status_code, 302)

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

            # Directly check the database
            user = User.query.get(self.testuser.id)
            self.assertEqual(user.username, "newname")
            self.assertEqual(user.bio, "New bio")
            self.assertEqual(user.email, "new@test.com")

  