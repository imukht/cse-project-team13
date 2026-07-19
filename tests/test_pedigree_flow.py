import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app as app_module


class PedigreeFlowTests(unittest.TestCase):
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

    def test_pedigree_can_link_existing_dogs(self):
        with app_module.app.app_context():
            db = app_module.get_db()
            db.execute(
                "INSERT INTO users (full_name, email, password_hash, dogs_count, created_at, email_verified) VALUES (?, ?, ?, ?, ?, ?)",
                ("Tester", "tester@example.com", app_module.generate_password_hash("TestPass!"), 2, "2026-01-01", 1),
            )
            user_id = db.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
            db.execute("INSERT INTO notifications (owner_id, email_alerts, in_app_alerts, pedigree_updates, reminders) VALUES (?, ?, ?, ?, ?)", (user_id, 1, 1, 1, 1))
            db.execute("INSERT INTO preferences (owner_id, display, privacy, default_view) VALUES (?, ?, ?, ?)", (user_id, "Grid", "Shared", "Grid"))
            db.execute("INSERT INTO dogs (owner_id, name, breed, birthdate, sex, photo, is_saved, father, mother, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_id, "Alpha", "Labrador", "2020-01-01", "Male", app_module.DEFAULT_DOG_PHOTO, 1, "", "", ""))
            db.execute("INSERT INTO dogs (owner_id, name, breed, birthdate, sex, photo, is_saved, father, mother, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_id, "Beta", "Golden Retriever", "2020-02-01", "Female", app_module.DEFAULT_DOG_PHOTO, 1, "", "", ""))
            db.commit()
            first_dog_id = db.execute("SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (user_id, "Alpha")).fetchone()["id"]
            second_dog_id = db.execute("SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (user_id, "Beta")).fetchone()["id"]

        with self.client.session_transaction() as session:
            session["user_id"] = user_id

        response = self.client.post(
            f"/pedigrees/{first_dog_id}/relationships",
            data={"father_id": str(second_dog_id), "mother_id": ""},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Pedigree updated", response.data)

        with app_module.app.app_context():
            db = app_module.get_db()
            dog = db.execute("SELECT father, mother FROM dogs WHERE id = ?", (first_dog_id,)).fetchone()
            self.assertEqual(dog["father"], "Beta")
            self.assertEqual(dog["mother"], "")

    def test_cannot_use_same_dog_for_both_parents_or_self(self):
        with app_module.app.app_context():
            db = app_module.get_db()
            db.execute(
                "INSERT INTO users (full_name, email, password_hash, dogs_count, created_at, email_verified) VALUES (?, ?, ?, ?, ?, ?)",
                ("Tester", "tester2@example.com", app_module.generate_password_hash("TestPass!"), 1, "2026-01-01", 1),
            )
            user_id = db.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
            db.execute("INSERT INTO notifications (owner_id, email_alerts, in_app_alerts, pedigree_updates, reminders) VALUES (?, ?, ?, ?, ?)", (user_id, 1, 1, 1, 1))
            db.execute("INSERT INTO preferences (owner_id, display, privacy, default_view) VALUES (?, ?, ?, ?)", (user_id, "Grid", "Shared", "Grid"))
            db.execute("INSERT INTO dogs (owner_id, name, breed, birthdate, sex, photo, is_saved, father, mother, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_id, "Solo", "Labrador", "2020-01-01", "Male", app_module.DEFAULT_DOG_PHOTO, 1, "", "", ""))
            db.commit()
            dog_id = db.execute("SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (user_id, "Solo")).fetchone()["id"]

        with self.client.session_transaction() as session:
            session["user_id"] = user_id

        response = self.client.post(
            f"/pedigrees/{dog_id}/relationships",
            data={"father_id": str(dog_id), "mother_id": str(dog_id)},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please choose different dogs for father and mother", response.data)

        response = self.client.post(
            f"/pedigrees/{dog_id}/relationships",
            data={"father_id": str(dog_id), "mother_id": ""},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"A dog cannot be linked as its own parent", response.data)

    def test_selected_dog_tree_can_show_grandparents(self):
        with app_module.app.app_context():
            db = app_module.get_db()
            db.execute(
                "INSERT INTO users (full_name, email, password_hash, dogs_count, created_at, email_verified) VALUES (?, ?, ?, ?, ?, ?)",
                ("Tester", "tester3@example.com", app_module.generate_password_hash("TestPass!"), 3, "2026-01-01", 1),
            )
            user_id = db.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
            db.execute("INSERT INTO notifications (owner_id, email_alerts, in_app_alerts, pedigree_updates, reminders) VALUES (?, ?, ?, ?, ?)", (user_id, 1, 1, 1, 1))
            db.execute("INSERT INTO preferences (owner_id, display, privacy, default_view) VALUES (?, ?, ?, ?)", (user_id, "Grid", "Shared", "Grid"))
            db.execute("INSERT INTO dogs (owner_id, name, breed, birthdate, sex, photo, is_saved, father, mother, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_id, "Pup", "Labrador", "2020-01-01", "Male", app_module.DEFAULT_DOG_PHOTO, 1, "", "", ""))
            db.execute("INSERT INTO dogs (owner_id, name, breed, birthdate, sex, photo, is_saved, father, mother, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_id, "Dad", "Golden Retriever", "2018-01-01", "Male", app_module.DEFAULT_DOG_PHOTO, 1, "", "", ""))
            db.execute("INSERT INTO dogs (owner_id, name, breed, birthdate, sex, photo, is_saved, father, mother, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_id, "Granddad", "German Shepherd", "2016-01-01", "Male", app_module.DEFAULT_DOG_PHOTO, 1, "", "", ""))
            db.commit()
            pup_id = db.execute("SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (user_id, "Pup")).fetchone()["id"]
            dad_id = db.execute("SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (user_id, "Dad")).fetchone()["id"]
            granddad_id = db.execute("SELECT id FROM dogs WHERE owner_id = ? AND name = ?", (user_id, "Granddad")).fetchone()["id"]
            db.execute("UPDATE dogs SET father = ? WHERE id = ?", ("Dad", pup_id))
            db.execute("UPDATE dogs SET father = ? WHERE id = ?", ("Granddad", dad_id))
            db.commit()

        with self.client.session_transaction() as session:
            session["user_id"] = user_id

        response = self.client.get(f"/pedigrees?selected_dog={pup_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Granddad", response.data)


if __name__ == "__main__":
    unittest.main()
