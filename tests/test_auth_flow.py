import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app as app_module


class AuthFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        app_module.DB_PATH = os.path.join(self.temp_dir.name, "embark_test.db")
        app_module.app.config["TESTING"] = True
        app_module.app.config["WTF_CSRF_ENABLED"] = False
        self.client = app_module.app.test_client()
        with app_module.app.app_context():
            app_module.init_db()

    def tearDown(self):
        self.temp_dir.cleanup()

    def register(self, full_name="New User", email="newuser@example.com",
                  password="StrongPass!1", confirm=None):
        return self.client.post(
            "/register",
            data={
                "fullName": full_name,
                "email": email,
                "password": password,
                "confirmPassword": confirm if confirm is not None else password,
            },
            follow_redirects=True,
        )

    def test_register_creates_unverified_user_and_shows_confirmation(self):
        response = self.register()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"newuser@example.com", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            user = db.execute(
                "SELECT * FROM users WHERE email = ?", ("newuser@example.com",)
            ).fetchone()
            self.assertIsNotNone(user)
            self.assertEqual(user["email_verified"], 0)
            self.assertIsNotNone(user["verification_token"])

    def test_register_rejects_mismatched_passwords(self):
        response = self.register(confirm="Different1!")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Passwords do not match", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            user = db.execute(
                "SELECT id FROM users WHERE email = ?", ("newuser@example.com",)
            ).fetchone()
            self.assertIsNone(user)

    def test_register_rejects_weak_password(self):
        response = self.register(password="weakpass", confirm="weakpass")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Password must be at least 8 characters", response.data)

    def test_register_rejects_duplicate_email(self):
        self.register(email="dupe@example.com")
        response = self.register(full_name="Someone Else", email="dupe@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"account with that email already exists", response.data)

    def test_login_blocked_until_email_verified(self):
        self.register(email="unverified@example.com")
        response = self.client.post(
            "/login",
            data={"email": "unverified@example.com", "password": "StrongPass!1"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please verify your email", response.data)

    def test_login_fails_with_wrong_password(self):
        self.register(email="hasaccount@example.com")
        with app_module.app.app_context():
            db = app_module.get_db()
            db.execute(
                "UPDATE users SET email_verified = 1 WHERE email = ?",
                ("hasaccount@example.com",),
            )
            db.commit()

        response = self.client.post(
            "/login",
            data={"email": "hasaccount@example.com", "password": "WrongPass!1"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid email or password", response.data)

    def test_verify_then_login_succeeds(self):
        self.register(email="verifyme@example.com")
        with app_module.app.app_context():
            db = app_module.get_db()
            token = db.execute(
                "SELECT verification_token FROM users WHERE email = ?",
                ("verifyme@example.com",),
            ).fetchone()["verification_token"]

        verify_response = self.client.get(f"/verify/{token}", follow_redirects=True)
        self.assertEqual(verify_response.status_code, 200)
        self.assertIn(b"successfully verified", verify_response.data)

        login_response = self.client.post(
            "/login",
            data={"email": "verifyme@example.com", "password": "StrongPass!1"},
            follow_redirects=True,
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertIn(b"Welcome back", login_response.data)

    def test_logout_clears_session(self):
        self.register(email="logmeout@example.com")
        with app_module.app.app_context():
            db = app_module.get_db()
            user_id = db.execute(
                "SELECT id FROM users WHERE email = ?", ("logmeout@example.com",)
            ).fetchone()["id"]

        with self.client.session_transaction() as session:
            session["user_id"] = user_id

        response = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"signed out", response.data)

        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)


if __name__ == "__main__":
    unittest.main()
