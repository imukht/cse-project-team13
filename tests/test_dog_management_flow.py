import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app as app_module


class DogManagementFlowTests(unittest.TestCase):
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
                ("Tester", "dogmanager@example.com", app_module.generate_password_hash("TestPass!1"), 0, "2026-01-01", 1),
            )
            self.user_id = db.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
            db.execute("INSERT INTO notifications (owner_id, email_alerts, in_app_alerts, pedigree_updates, reminders) VALUES (?, ?, ?, ?, ?)", (self.user_id, 1, 1, 1, 1))
            db.execute("INSERT INTO preferences (owner_id, display, privacy, default_view) VALUES (?, ?, ?, ?)", (self.user_id, "Grid", "Shared", "Grid"))
            db.commit()

        with self.client.session_transaction() as session:
            session["user_id"] = self.user_id

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_dog(self, name="Buddy", breed="Labrador", birthdate="2020-01-01", sex="Male"):
        return self.client.post(
            "/homepage",
            data={"name": name, "breed": breed, "birthdate": birthdate, "sex": sex},
            follow_redirects=True,
        )

    # --- Adding dogs ---

    def test_add_dog_creates_dog_and_increments_count(self):
        response = self.add_dog()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dog added successfully", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            dog = db.execute("SELECT * FROM dogs WHERE owner_id = ? AND name = ?", (self.user_id, "Buddy")).fetchone()
            self.assertIsNotNone(dog)
            self.assertEqual(dog["photo"], app_module.DEFAULT_DOG_PHOTO)
            user = db.execute("SELECT dogs_count FROM users WHERE id = ?", (self.user_id,)).fetchone()
            self.assertEqual(user["dogs_count"], 1)

    def test_add_dog_requires_all_fields(self):
        response = self.client.post(
            "/homepage",
            data={"name": "", "breed": "Labrador", "birthdate": "2020-01-01", "sex": "Male"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please complete all required dog fields", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            count = db.execute("SELECT COUNT(*) as c FROM dogs WHERE owner_id = ?", (self.user_id,)).fetchone()["c"]
            self.assertEqual(count, 0)

    def test_add_dog_rejects_future_birthdate(self):
        future_date = (date.today() + timedelta(days=30)).isoformat()
        response = self.add_dog(birthdate=future_date)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Birthdate cannot be in the future", response.data)

    def test_add_dog_rejects_malformed_birthdate(self):
        response = self.add_dog(birthdate="01/01/2020")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please enter a valid birthdate", response.data)

    # --- Editing dogs ---

    def test_edit_dog_updates_fields(self):
        self.add_dog(name="Original Name", breed="Poodle")
        with app_module.app.app_context():
            db = app_module.get_db()
            dog_id = db.execute("SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (self.user_id, "Original Name")).fetchone()["id"]

        response = self.client.post(
            f"/dogs/{dog_id}/edit",
            data={"name": "Updated Name", "breed": "Beagle", "birthdate": "2019-06-15", "sex": "Female"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dog information updated", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            dog = db.execute("SELECT * FROM dogs WHERE id = ?", (dog_id,)).fetchone()
            self.assertEqual(dog["name"], "Updated Name")
            self.assertEqual(dog["breed"], "Beagle")
            self.assertEqual(dog["birthdate"], "2019-06-15")

    def test_edit_dog_rejects_future_birthdate(self):
        self.add_dog(name="Original Name")
        with app_module.app.app_context():
            db = app_module.get_db()
            dog_id = db.execute("SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (self.user_id, "Original Name")).fetchone()["id"]

        future_date = (date.today() + timedelta(days=10)).isoformat()
        response = self.client.post(
            f"/dogs/{dog_id}/edit",
            data={"name": "Original Name", "breed": "Labrador", "birthdate": future_date, "sex": "Male"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Birthdate cannot be in the future", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            dog = db.execute("SELECT birthdate FROM dogs WHERE id = ?", (dog_id,)).fetchone()
            self.assertEqual(dog["birthdate"], "2020-01-01")

    def test_edit_dog_returns_not_found_for_missing_dog(self):
        response = self.client.post(
            "/dogs/999999/edit",
            data={"name": "Ghost", "breed": "Labrador", "birthdate": "2020-01-01", "sex": "Male"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dog profile not found", response.data)

    def test_cannot_edit_another_users_dog(self):
        self.add_dog(name="Protected Dog")
        with app_module.app.app_context():
            db = app_module.get_db()
            dog_id = db.execute("SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (self.user_id, "Protected Dog")).fetchone()["id"]
            db.execute(
                "INSERT INTO users (full_name, email, password_hash, dogs_count, created_at, email_verified) VALUES (?, ?, ?, ?, ?, ?)",
                ("Other Owner", "otherowner2@example.com", app_module.generate_password_hash("TestPass!1"), 0, "2026-01-01", 1),
            )
            other_user_id = db.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
            db.commit()

        other_client = app_module.app.test_client()
        with other_client.session_transaction() as session:
            session["user_id"] = other_user_id

        response = other_client.post(
            f"/dogs/{dog_id}/edit",
            data={"name": "Hijacked Name", "breed": "Beagle", "birthdate": "2020-01-01", "sex": "Male"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dog profile not found", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            dog = db.execute("SELECT name FROM dogs WHERE id = ?", (dog_id,)).fetchone()
            self.assertEqual(dog["name"], "Protected Dog")

    # --- Deleting dogs ---

    def test_delete_dog_removes_dog_and_decrements_count(self):
        self.add_dog(name="Temporary Dog")
        with app_module.app.app_context():
            db = app_module.get_db()
            dog_id = db.execute("SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (self.user_id, "Temporary Dog")).fetchone()["id"]

        response = self.client.post(f"/dogs/{dog_id}/delete", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dog profile removed", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            dog = db.execute("SELECT id FROM dogs WHERE id = ?", (dog_id,)).fetchone()
            self.assertIsNone(dog)
            user = db.execute("SELECT dogs_count FROM users WHERE id = ?", (self.user_id,)).fetchone()
            self.assertEqual(user["dogs_count"], 0)

    def test_delete_dog_count_never_goes_negative(self):
        with app_module.app.app_context():
            db = app_module.get_db()
            db.execute("UPDATE users SET dogs_count = 0 WHERE id = ?", (self.user_id,))
            db.execute(
                "INSERT INTO dogs (owner_id, name, breed, birthdate, sex, photo, is_saved, father, mother, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (self.user_id, "Underflow Dog", "Labrador", "2020-01-01", "Male", app_module.DEFAULT_DOG_PHOTO, 0, "", "", ""),
            )
            db.commit()
            dog_id = db.execute("SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (self.user_id, "Underflow Dog")).fetchone()["id"]

        self.client.post(f"/dogs/{dog_id}/delete", follow_redirects=True)

        with app_module.app.app_context():
            db = app_module.get_db()
            user = db.execute("SELECT dogs_count FROM users WHERE id = ?", (self.user_id,)).fetchone()
            self.assertEqual(user["dogs_count"], 0)

    def test_cannot_delete_another_users_dog(self):
        self.add_dog(name="Safe Dog")
        with app_module.app.app_context():
            db = app_module.get_db()
            dog_id = db.execute("SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (self.user_id, "Safe Dog")).fetchone()["id"]
            db.execute(
                "INSERT INTO users (full_name, email, password_hash, dogs_count, created_at, email_verified) VALUES (?, ?, ?, ?, ?, ?)",
                ("Other Owner", "otherowner3@example.com", app_module.generate_password_hash("TestPass!1"), 0, "2026-01-01", 1),
            )
            other_user_id = db.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
            db.commit()

        other_client = app_module.app.test_client()
        with other_client.session_transaction() as session:
            session["user_id"] = other_user_id

        response = other_client.post(f"/dogs/{dog_id}/delete", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dog profile not found", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            dog = db.execute("SELECT id FROM dogs WHERE id = ?", (dog_id,)).fetchone()
            self.assertIsNotNone(dog)


if __name__ == "__main__":
    unittest.main()
