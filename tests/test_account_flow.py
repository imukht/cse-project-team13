import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app as app_module


class AccountFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        app_module.DB_PATH = os.path.join(self.temp_dir.name, "embark_test.db")
        app_module.app.config["TESTING"] = True
        app_module.app.config["WTF_CSRF_ENABLED"] = False
        self.client = app_module.app.test_client()
        with app_module.app.app_context():
            app_module.init_db()
            db = app_module.get_db()
            db.execute(
                "INSERT INTO users (full_name, email, password_hash, dogs_count, created_at, email_verified) VALUES (?, ?, ?, ?, ?, ?)",
                ("Tester", "profileowner@example.com", app_module.generate_password_hash("OldPass!1"), 0, "2026-01-01", 1),
            )
            self.user_id = db.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
            db.execute("INSERT INTO notifications (owner_id, email_alerts, in_app_alerts, pedigree_updates, reminders) VALUES (?, ?, ?, ?, ?)", (self.user_id, 1, 1, 1, 1))
            db.execute("INSERT INTO preferences (owner_id, display, privacy, default_view) VALUES (?, ?, ?, ?)", (self.user_id, "Grid", "Shared", "Grid"))
            db.execute(
                "INSERT INTO users (full_name, email, password_hash, dogs_count, created_at, email_verified) VALUES (?, ?, ?, ?, ?, ?)",
                ("Existing Owner", "taken@example.com", app_module.generate_password_hash("SomePass!1"), 0, "2026-01-01", 1),
            )
            db.commit()

        with self.client.session_transaction() as session:
            session["user_id"] = self.user_id

    def tearDown(self):
        self.temp_dir.cleanup()

    def change_account(self, current_password="OldPass!1", new_email="", new_password="", confirm_password=""):
        return self.client.post(
            "/profile",
            data={
                "action": "confirm-account-change",
                "current_password": current_password,
                "new_email": new_email,
                "new_password": new_password,
                "confirm_password": confirm_password,
            },
            follow_redirects=True,
        )

    def test_show_change_form_action_renders_form(self):
        response = self.client.post("/profile", data={"action": "show-change-form"})
        self.assertEqual(response.status_code, 200)

    def test_change_email_requires_correct_current_password(self):
        response = self.change_account(current_password="WrongPass!1", new_email="newemail@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Current password is incorrect", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            user = db.execute("SELECT email FROM users WHERE id = ?", (self.user_id,)).fetchone()
            self.assertEqual(user["email"], "profileowner@example.com")

    def test_change_email_succeeds_with_correct_password(self):
        response = self.change_account(new_email="newemail@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Account details updated successfully", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            user = db.execute("SELECT email FROM users WHERE id = ?", (self.user_id,)).fetchone()
            self.assertEqual(user["email"], "newemail@example.com")

    def test_change_email_rejects_email_already_in_use(self):
        response = self.change_account(new_email="taken@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"already in use", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            user = db.execute("SELECT email FROM users WHERE id = ?", (self.user_id,)).fetchone()
            self.assertEqual(user["email"], "profileowner@example.com")

    def test_change_password_requires_matching_confirmation(self):
        response = self.change_account(new_password="NewPass!1", confirm_password="Different!2")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"New passwords do not match", response.data)

    def test_change_password_rejects_weak_new_password(self):
        response = self.change_account(new_password="weak", confirm_password="weak")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"New password must be at least 8 characters", response.data)

    def test_change_password_succeeds_and_old_password_stops_working(self):
        response = self.change_account(new_password="NewPass!1", confirm_password="NewPass!1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Account details updated successfully", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            user = db.execute("SELECT password_hash FROM users WHERE id = ?", (self.user_id,)).fetchone()
            self.assertTrue(app_module.check_password_hash(user["password_hash"], "NewPass!1"))
            self.assertFalse(app_module.check_password_hash(user["password_hash"], "OldPass!1"))

    def test_change_account_requires_email_or_password(self):
        response = self.change_account()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please enter an email address or a new password", response.data)


if __name__ == "__main__":
    unittest.main()
