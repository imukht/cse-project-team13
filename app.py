import os
import secrets
import smtplib
import sqlite3
from email.message import EmailMessage
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "embark-secret-key")
DB_PATH = os.path.join(os.path.dirname(__file__), "embark.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
DEFAULT_DOG_PHOTO = "/static/default-dog.svg"
BREED_OPTIONS = [
    "Affenpinscher",
    "Akita",
    "Alaskan Malamute",
    "American Bulldog",
    "American Eskimo Dog",
    "American Staffordshire Terrier",
    "Australian Shepherd",
    "Basset Hound",
    "Beagle",
    "Bernese Mountain Dog",
    "Bichon Frise",
    "Border Collie",
    "Boston Terrier",
    "Boxer",
    "Bulldog",
    "Cane Corso",
    "Cavalier King Charles Spaniel",
    "Chihuahua",
    "Chow Chow",
    "Cocker Spaniel",
    "Collie",
    "Dachshund",
    "Dalmatian",
    "Doberman Pinscher",
    "English Bulldog",
    "English Springer Spaniel",
    "French Bulldog",
    "German Shepherd",
    "Golden Retriever",
    "Great Dane",
    "Greyhound",
    "Havanese",
    "Husky",
    "Labrador Retriever",
    "Maltese",
    "Miniature Schnauzer",
    "Poodle",
    "Pug",
    "Rottweiler",
    "Siberian Husky",
    "Shih Tzu",
    "Weimaraner",
    "Yorkshire Terrier",
]


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def has_column(table_name, column_name):
    rows = get_db().execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            dogs_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            email_verified INTEGER DEFAULT 0,
            verification_token TEXT,
            verification_sent_at TEXT
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS dogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            breed TEXT NOT NULL,
            birthdate TEXT NOT NULL,
            sex TEXT NOT NULL,
            photo TEXT NOT NULL,
            is_saved INTEGER DEFAULT 0,
            father TEXT DEFAULT '',
            mother TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            owner_id INTEGER PRIMARY KEY,
            email_alerts INTEGER DEFAULT 1,
            in_app_alerts INTEGER DEFAULT 1,
            pedigree_updates INTEGER DEFAULT 1,
            reminders INTEGER DEFAULT 1
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS preferences (
            owner_id INTEGER PRIMARY KEY,
            display TEXT DEFAULT 'Grid',
            privacy TEXT DEFAULT 'Shared with breeder network',
            default_view TEXT DEFAULT 'Grid'
        )
        """
    )

    if not has_column("users", "email_verified"):
        db.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0")
    if not has_column("users", "verification_token"):
        db.execute("ALTER TABLE users ADD COLUMN verification_token TEXT")
    if not has_column("users", "verification_sent_at"):
        db.execute("ALTER TABLE users ADD COLUMN verification_sent_at TEXT")

    db.commit()

    demo_user = db.execute("SELECT id FROM users WHERE email = ?", ("demo@example.com",)).fetchone()
    if demo_user is None:
        db.execute(
            "INSERT INTO users (full_name, email, password_hash, dogs_count, created_at, email_verified) VALUES (?, ?, ?, ?, ?, ?)",
            ("Demo User", "demo@example.com", generate_password_hash("DemoPass!"), 3, "2026-01-01T00:00:00", 1),
        )
        demo_user_id = db.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
        db.execute(
            "INSERT INTO notifications (owner_id, email_alerts, in_app_alerts, pedigree_updates, reminders) VALUES (?, ?, ?, ?, ?)",
            (demo_user_id, 1, 1, 1, 1),
        )
        db.execute(
            "INSERT INTO preferences (owner_id, display, privacy, default_view) VALUES (?, ?, ?, ?)",
            (demo_user_id, "Grid", "Shared with breeder network", "Grid"),
        )
        db.execute(
            "INSERT INTO dogs (owner_id, name, breed, birthdate, sex, photo, is_saved, father, mother, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (demo_user_id, "Sunny", "Golden Retriever", "2021-05-14", "Female", "https://images.unsplash.com/photo-1517849845537-4d257902454a?auto=format&fit=crop&w=900&q=80", 1, "Cedar Ridge Atlas", "Willow Creek Nova", "Strong working lineage with award-winning siblings."),
        )
        db.execute(
            "INSERT INTO dogs (owner_id, name, breed, birthdate, sex, photo, is_saved, father, mother, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (demo_user_id, "Rex", "Labrador Retriever", "2019-09-02", "Male", "https://images.unsplash.com/photo-1537151608828-ea2b11777ee8?auto=format&fit=crop&w=900&q=80", 1, "Summit Harbor Ranger", "Meadowfield Bella", "Balanced temperament and excellent field record."),
        )
        db.execute(
            "INSERT INTO dogs (owner_id, name, breed, birthdate, sex, photo, is_saved, father, mother, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (demo_user_id, "Mia", "Bernese Mountain Dog", "2020-11-21", "Female", "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?auto=format&fit=crop&w=900&q=80", 0, "Northstar Bruno", "Snowline Tessa", "Gentle family dog with strong structure."),
        )
        db.commit()


@app.context_processor
def inject_user():
    user_id = session.get("user_id")
    if not user_id:
        return {"current_user": None}

    user = get_db().execute("SELECT id, full_name, email, dogs_count, email_verified FROM users WHERE id = ?", (user_id,)).fetchone()
    return {"current_user": user}


def login_required(view_function):
    @wraps(view_function)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)

    return wrapped


def password_meets_requirements(password):
    return len(password) >= 8 and any(char.isupper() for char in password) and any(not char.isalnum() for char in password)


def normalize_email(email):
    return email.strip().lower()


def save_uploaded_photo(file_storage):
    if not file_storage or not getattr(file_storage, "filename", ""):
        return None
    filename = secure_filename(file_storage.filename)
    if not filename:
        return None
    unique_name = f"{secrets.token_hex(8)}_{filename}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file_storage.save(path)
    return f"/static/uploads/{unique_name}"


def create_verification_token():
    return secrets.token_urlsafe(24)


def build_verification_link(token):
    return f"{request.host_url.rstrip('/')}/verify/{token}"


def send_verification_email(recipient, link):
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SMTP_FROM", "noreply@embark.local")

    if not smtp_host or not smtp_username or not smtp_password:
        print(f"Verification email for {recipient}: {link}")
        return False

    message = EmailMessage()
    message["Subject"] = "Verify your Embark account"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        f"Thanks for creating an account with Embark. Please verify your email by clicking the link below:\n\n{link}\n"
    )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(message)

    return True


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("homepage"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = normalize_email(request.form.get("email", ""))
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))
        if not user["email_verified"]:
            flash("Please verify your email before signing in.", "error")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        flash("Welcome back!", "success")
        return redirect(url_for("homepage"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("fullName", "").strip()
        email = normalize_email(request.form.get("email", ""))
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirmPassword", "")

        if not full_name:
            flash("Please enter your full name.", "error")
            return redirect(url_for("register"))
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))
        if not password_meets_requirements(password):
            flash("Password must be at least 8 characters, include a capital letter, and a special character.", "error")
            return redirect(url_for("register"))

        existing = get_db().execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash("An account with that email already exists.", "error")
            return redirect(url_for("register"))

        token = create_verification_token()
        db = get_db()
        db.execute(
            "INSERT INTO users (full_name, email, password_hash, dogs_count, created_at, email_verified, verification_token, verification_sent_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (full_name, email, generate_password_hash(password), 0, "now", 0, token, "now"),
        )
        user_id = db.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
        db.execute(
            "INSERT INTO notifications (owner_id, email_alerts, in_app_alerts, pedigree_updates, reminders) VALUES (?, ?, ?, ?, ?)",
            (user_id, 1, 1, 1, 1),
        )
        db.execute(
            "INSERT INTO preferences (owner_id, display, privacy, default_view) VALUES (?, ?, ?, ?)",
            (user_id, "Grid", "Shared with breeder network", "Grid"),
        )
        db.commit()

        verification_link = build_verification_link(token)
        email_sent = send_verification_email(email, verification_link)
        return render_template("confirmation.html", email=email, verification_link=verification_link, email_sent=email_sent)

    return render_template("create-account.html")


@app.route("/verify/<token>")
def verify_email(token):
    user = get_db().execute("SELECT id FROM users WHERE verification_token = ?", (token,)).fetchone()
    if not user:
        flash("That verification link is invalid or has already been used.", "error")
        return redirect(url_for("login"))

    db = get_db()
    db.execute(
        "UPDATE users SET email_verified = 1, verification_token = NULL WHERE id = ?",
        (user["id"],),
    )
    db.commit()
    flash("Your email address has been verified. Please sign in.", "success")
    return render_template("verified.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/homepage", methods=["GET", "POST"])
@login_required
def homepage():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        breed = request.form.get("breed", "").strip()
        birthdate = request.form.get("birthdate", "").strip()
        sex = request.form.get("sex", "").strip()

        if not name or not breed or not birthdate or not sex:
            flash("Please complete all required dog fields.", "error")
            return redirect(url_for("homepage"))

        photo_value = save_uploaded_photo(request.files.get("photo_file"))
        if not photo_value:
            photo_value = request.form.get("photo", "").strip() or DEFAULT_DOG_PHOTO

        db = get_db()
        db.execute(
            "INSERT INTO dogs (owner_id, name, breed, birthdate, sex, photo, is_saved, father, mother, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session["user_id"],
                name,
                breed,
                birthdate,
                sex,
                photo_value,
                0,
                "",
                "",
                "",
            ),
        )
        db.execute("UPDATE users SET dogs_count = dogs_count + 1 WHERE id = ?", (session["user_id"],))
        db.commit()
        flash("Dog added successfully.", "success")
        return redirect(url_for("homepage"))

    db = get_db()
    dogs = db.execute("SELECT * FROM dogs WHERE owner_id = ? ORDER BY id DESC", (session["user_id"],)).fetchall()
    return render_template("homepage.html", dogs=dogs, breed_options=BREED_OPTIONS, active_page="home")


@app.route("/saved-dogs")
@login_required
def saved_dogs():
    db = get_db()
    dogs = db.execute("SELECT * FROM dogs WHERE owner_id = ? AND is_saved = 1 ORDER BY id DESC", (session["user_id"],)).fetchall()
    return render_template("saved-dogs.html", dogs=dogs, active_page="saved")


@app.route("/pedigrees")
@login_required
def pedigrees():
    db = get_db()
    dogs = db.execute("SELECT * FROM dogs WHERE owner_id = ? ORDER BY id DESC", (session["user_id"],)).fetchall()
    selected_dog_id = request.args.get("selected_dog", type=int)

    def build_branch(dog, depth=0):
        if depth >= 3:
            return None

        parent_entries = []
        father_name = dog["father"].strip() if dog["father"] else ""
        mother_name = dog["mother"].strip() if dog["mother"] else ""

        if father_name:
            father_dog = next((item for item in dogs if item["name"] == father_name), None)
            if father_dog:
                parent_entries.append(("Father", father_dog, build_branch(father_dog, depth + 1)))
        if mother_name:
            mother_dog = next((item for item in dogs if item["name"] == mother_name), None)
            if mother_dog:
                parent_entries.append(("Mother", mother_dog, build_branch(mother_dog, depth + 1)))

        return {
            "dog": dog,
            "depth": depth,
            "parents": parent_entries,
        }

    pedigree_trees = {dog["id"]: build_branch(dog) for dog in dogs}

    return render_template(
        "pedigrees.html",
        dogs=dogs,
        active_page="pedigrees",
        selected_dog_id=selected_dog_id,
        pedigree_trees=pedigree_trees,
    )


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    db = get_db()
    user = db.execute("SELECT id, full_name, email, dogs_count, password_hash FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    show_change_form = request.args.get("show_change_form") == "1" or request.form.get("action") == "show-change-form"

    if request.method == "POST":
        action = request.form.get("action")
        if action == "show-change-form":
            show_change_form = True
            return render_template("profile.html", user=user, show_change_form=show_change_form, active_page="profile")

        if action == "cancel-change":
            return redirect(url_for("profile"))

        if action == "confirm-account-change":
            current_password = request.form.get("current_password", "")
            new_email = normalize_email(request.form.get("new_email", ""))
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not check_password_hash(user["password_hash"], current_password):
                flash("Current password is incorrect.", "error")
                return redirect(url_for("profile", show_change_form="1"))

            if not new_email and not new_password:
                flash("Please enter an email address or a new password to update.", "error")
                return redirect(url_for("profile", show_change_form="1"))

            if new_password:
                if new_password != confirm_password:
                    flash("New passwords do not match.", "error")
                    return redirect(url_for("profile", show_change_form="1"))
                if not password_meets_requirements(new_password):
                    flash("New password must be at least 8 characters, include a capital letter, and a special character.", "error")
                    return redirect(url_for("profile", show_change_form="1"))

            if new_email and new_email != user["email"]:
                existing = db.execute("SELECT id FROM users WHERE email = ? AND id != ?", (new_email, session["user_id"])).fetchone()
                if existing:
                    flash("That email address is already in use.", "error")
                    return redirect(url_for("profile", show_change_form="1"))

            updates = []
            values = []
            if new_email:
                updates.append("email = ?")
                values.append(new_email)
            if new_password:
                updates.append("password_hash = ?")
                values.append(generate_password_hash(new_password))
            if updates:
                values.extend([session["user_id"]])
                db.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
                db.commit()

            flash("Account details updated successfully.", "success")
            return redirect(url_for("profile"))

    return render_template("profile.html", user=user, show_change_form=show_change_form, active_page="profile")


@app.route("/notifications", methods=["GET", "POST"])
@login_required
def notifications():
    if request.method == "POST":
        db = get_db()
        db.execute(
            "INSERT INTO notifications (owner_id, email_alerts, in_app_alerts, pedigree_updates, reminders) VALUES (?, ?, ?, ?, ?) ON CONFLICT(owner_id) DO UPDATE SET email_alerts = excluded.email_alerts, in_app_alerts = excluded.in_app_alerts, pedigree_updates = excluded.pedigree_updates, reminders = excluded.reminders",
            (
                session["user_id"],
                1 if request.form.get("email") else 0,
                1 if request.form.get("inApp") else 0,
                1 if request.form.get("pedigreeUpdates") else 0,
                1 if request.form.get("reminders") else 0,
            ),
        )
        db.commit()
        flash("Notification settings updated.", "success")
        return redirect(url_for("notifications"))

    db = get_db()
    settings = db.execute("SELECT * FROM notifications WHERE owner_id = ?", (session["user_id"],)).fetchone()
    return render_template("notifications.html", settings=settings, active_page="notifications")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        db = get_db()
        db.execute(
            "INSERT INTO preferences (owner_id, display, privacy, default_view) VALUES (?, ?, ?, ?) ON CONFLICT(owner_id) DO UPDATE SET display = excluded.display, privacy = excluded.privacy, default_view = excluded.default_view",
            (
                session["user_id"],
                request.form.get("display", "Grid"),
                request.form.get("privacy", "Shared with breeder network"),
                request.form.get("defaultView", "Grid"),
            ),
        )
        db.commit()
        flash("Preferences updated.", "success")
        return redirect(url_for("settings"))

    db = get_db()
    prefs = db.execute("SELECT * FROM preferences WHERE owner_id = ?", (session["user_id"],)).fetchone()
    return render_template("settings.html", prefs=prefs, active_page="settings")


@app.route("/dogs/<int:dog_id>/edit", methods=["POST"])
@login_required
def edit_dog(dog_id):
    db = get_db()
    existing = db.execute("SELECT photo FROM dogs WHERE id = ? AND owner_id = ?", (dog_id, session["user_id"])).fetchone()
    photo_value = save_uploaded_photo(request.files.get("photo_file"))
    if not photo_value:
        photo_value = request.form.get("photo", "").strip() or (existing["photo"] if existing else DEFAULT_DOG_PHOTO)

    db.execute(
        "UPDATE dogs SET name = ?, breed = ?, birthdate = ?, sex = ?, photo = ? WHERE id = ? AND owner_id = ?",
        (
            request.form.get("name", "").strip(),
            request.form.get("breed", "").strip(),
            request.form.get("birthdate", ""),
            request.form.get("sex", "").strip(),
            photo_value,
            dog_id,
            session["user_id"],
        ),
    )
    db.commit()
    flash("Dog information updated.", "success")
    return redirect(request.referrer or url_for("homepage"))

@app.route("/dogs/<int:dog_id>/delete", methods=["POST"])
@login_required
def delete_dog(dog_id):
    db = get_db()
    dog = db.execute("SELECT id FROM dogs WHERE id = ? AND owner_id = ?", (dog_id, session["user_id"])).fetchone()
    if not dog:
        flash("Dog profile not found.", "error")
        return redirect(request.referrer or url_for("homepage"))

    db.execute("DELETE FROM dogs WHERE id = ? AND owner_id = ?", (dog_id, session["user_id"]))
    db.execute("UPDATE users SET dogs_count = MAX(dogs_count - 1, 0) WHERE id = ?", (session["user_id"],))
    db.commit()
    flash("Dog profile removed.", "success")
    return redirect(request.referrer or url_for("homepage"))

@app.route("/dogs/<int:dog_id>/save", methods=["POST"])
@login_required
def toggle_save(dog_id):
    db = get_db()
    dog = db.execute("SELECT is_saved FROM dogs WHERE id = ? AND owner_id = ?", (dog_id, session["user_id"])).fetchone()
    if dog:
        db.execute("UPDATE dogs SET is_saved = ? WHERE id = ? AND owner_id = ?", (0 if dog["is_saved"] else 1, dog_id, session["user_id"]))
        db.commit()
    flash("Dog saved state updated.", "success")
    return redirect(request.referrer or url_for("homepage"))


@app.route("/pedigrees/<int:dog_id>/relationships", methods=["POST"])
@login_required
def update_pedigree_relationships(dog_id):
    db = get_db()
    dog = db.execute("SELECT id FROM dogs WHERE id = ? AND owner_id = ?", (dog_id, session["user_id"])).fetchone()
    if not dog:
        flash("Dog profile not found.", "error")
        return redirect(url_for("pedigrees"))

    father_id = request.form.get("father_id", "").strip()
    mother_id = request.form.get("mother_id", "").strip()
    notes = request.form.get("notes", "").strip()

    if father_id and mother_id and father_id == mother_id:
        flash("Please choose different dogs for father and mother.", "error")
        return redirect(url_for("pedigrees", selected_dog=dog_id))

    if father_id == str(dog_id) or mother_id == str(dog_id):
        flash("A dog cannot be linked as its own parent.", "error")
        return redirect(url_for("pedigrees", selected_dog=dog_id))

    father_name = ""
    mother_name = ""

    if father_id:
        father_dog = db.execute("SELECT id, name FROM dogs WHERE id = ? AND owner_id = ?", (father_id, session["user_id"])).fetchone()
        if father_dog:
            father_name = father_dog["name"]

    if mother_id:
        mother_dog = db.execute("SELECT id, name FROM dogs WHERE id = ? AND owner_id = ?", (mother_id, session["user_id"])).fetchone()
        if mother_dog:
            mother_name = mother_dog["name"]

    db.execute(
        "UPDATE dogs SET father = ?, mother = ?, notes = ? WHERE id = ? AND owner_id = ?",
        (father_name, mother_name, notes, dog_id, session["user_id"]),
    )
    db.commit()
    flash("Pedigree updated.", "success")
    return redirect(url_for("pedigrees", selected_dog=dog_id))


@app.route("/dogs/<int:dog_id>/pedigree", methods=["POST"])
@login_required
def update_pedigree(dog_id):
    return update_pedigree_relationships(dog_id)


@app.route("/style.css")
def style_css():
    return send_file("style.css", mimetype="text/css")


@app.route("/logo.png")
def logo_png():
    return send_file("logo.png", mimetype="image/png")


@app.route("/script.js")
def script_js():
    return send_file("script.js", mimetype="application/javascript")


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
