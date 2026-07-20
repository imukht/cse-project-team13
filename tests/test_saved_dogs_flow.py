import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app as app_module


class SavedDogsFlowTests(unittest.TestCase):
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
                ("Tester", "saveddogs@example.com", app_module.generate_password_hash("TestPass!1"), 2, "2026-01-01", 1),
            )
            self.user_id = db.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
            db.execute("INSERT INTO notifications (owner_id, email_alerts, in_app_alerts, pedigree_updates, reminders) VALUES (?, ?, ?, ?, ?)", (self.user_id, 1, 1, 1, 1))
            db.execute("INSERT INTO preferences (owner_id, display, privacy, default_view) VALUES (?, ?, ?, ?)", (self.user_id, "Grid", "Shared", "Grid"))
            db.execute(
                "INSERT INTO dogs (owner_id, name, breed, birthdate, sex, photo, is_saved, father, mother, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (self.user_id, "Saved Dog", "Labrador", "2020-01-01", "Male", app_module.DEFAULT_DOG_PHOTO, 1, "", "", ""),
            )
            db.execute(
                "INSERT INTO dogs (owner_id, name, breed, birthdate, sex, photo, is_saved, father, mother, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (self.user_id, "Unsaved Dog", "Poodle", "2021-01-01", "Female", app_module.DEFAULT_DOG_PHOTO, 0, "", "", ""),
            )
            db.commit()
            self.saved_dog_id = db.execute(
                "SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (self.user_id, "Saved Dog")
            ).fetchone()["id"]
            self.unsaved_dog_id = db.execute(
                "SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (self.user_id, "Unsaved Dog")
            ).fetchone()["id"]

        with self.client.session_transaction() as session:
            session["user_id"] = self.user_id

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_saved_dogs_page_requires_login(self):
        anonymous_client = app_module.app.test_client()
        response = anonymous_client.get("/saved-dogs", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please sign in to continue", response.data)

    def test_saved_dogs_page_lists_owners_dogs(self):
        response = self.client.get("/saved-dogs")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Saved Dog", response.data)
        self.assertIn(b"Unsaved Dog", response.data)

    def test_toggle_save_flips_state_on(self):
        response = self.client.post(
            f"/dogs/{self.unsaved_dog_id}/save",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"is_saved": True})

        with app_module.app.app_context():
            db = app_module.get_db()
            dog = db.execute("SELECT is_saved FROM dogs WHERE id = ?", (self.unsaved_dog_id,)).fetchone()
            self.assertEqual(dog["is_saved"], 1)

    def test_toggle_save_flips_state_off(self):
        response = self.client.post(
            f"/dogs/{self.saved_dog_id}/save",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"is_saved": False})

        with app_module.app.app_context():
            db = app_module.get_db()
            dog = db.execute("SELECT is_saved FROM dogs WHERE id = ?", (self.saved_dog_id,)).fetchone()
            self.assertEqual(dog["is_saved"], 0)

    def test_toggle_save_returns_404_for_missing_or_other_users_dog(self):
        response = self.client.post(
            "/dogs/999999/save",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "Dog profile not found."})

    def test_cannot_toggle_save_on_another_users_dog(self):
        with app_module.app.app_context():
            db = app_module.get_db()
            db.execute(
                "INSERT INTO users (full_name, email, password_hash, dogs_count, created_at, email_verified) VALUES (?, ?, ?, ?, ?, ?)",
                ("Other Owner", "otherowner@example.com", app_module.generate_password_hash("TestPass!1"), 1, "2026-01-01", 1),
            )
            other_user_id = db.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
            db.execute("INSERT INTO notifications (owner_id, email_alerts, in_app_alerts, pedigree_updates, reminders) VALUES (?, ?, ?, ?, ?)", (other_user_id, 1, 1, 1, 1))
            db.execute("INSERT INTO preferences (owner_id, display, privacy, default_view) VALUES (?, ?, ?, ?)", (other_user_id, "Grid", "Shared", "Grid"))
            db.commit()

        other_client = app_module.app.test_client()
        with other_client.session_transaction() as session:
            session["user_id"] = other_user_id

        response = other_client.post(
            f"/dogs/{self.saved_dog_id}/save",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
