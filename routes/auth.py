# routes/auth.py
# Authentication routes for ReturnImpact.
# References:
# - Flask sessions: https://flask.palletsprojects.com/en/3.0.x/quickstart/#sessions
# - Werkzeug password hashing: https://werkzeug.palletsprojects.com/en/3.0.x/utils/
# - CS50 Web Track login patterns: https://cs50.harvard.edu/x/2023/track/web/

from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from ..helpers import get_db, login_required 

auth_bp = Blueprint("auth", __name__)


# ------------------------------------------------------------
# Register route — creates company + first admin user
# ------------------------------------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        company_name = request.form.get("company_name")
        name = request.form.get("name")
        email = request.form.get("email").lower()
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if not company_name or not name or not email or not password:
            flash("All fields are required.")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.")
            return render_template("register.html")

        db = get_db()

        try:
            # Create company
            cur = db.execute("INSERT INTO companies (name) VALUES (?)", (company_name,))
            company_id = cur.lastrowid

            # Hash password (Werkzeug)
            password_hash = generate_password_hash(password)

            # Create user
            cur = db.execute(
                "INSERT INTO users (company_id, name, email, password_hash) VALUES (?, ?, ?, ?)",
                (company_id, name, email, password_hash)
            )
            user_id = cur.lastrowid

            # Assign admin role
            role = db.execute("SELECT id FROM roles WHERE name = 'admin'").fetchone()
            db.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role["id"]))

            db.commit()

        except Exception:
            db.rollback()
            flash("Company or email already exists.")
            return render_template("register.html")

        # Log user in
        session["user_id"] = user_id
        session["company_id"] = company_id
        session["user_name"] = name
        session["roles"] = ["admin"]

        return redirect(url_for("dashboard.dashboard"))

    return render_template("register.html")


# ------------------------------------------------------------
# Login route
# ------------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email").lower()
        password = request.form.get("password")

        db = get_db()

        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.")
            return render_template("login.html")

        # Load roles
        roles = db.execute(
            """
            SELECT r.name
            FROM roles r
            JOIN user_roles ur ON ur.role_id = r.id
            WHERE ur.user_id = ?
            """,
            (user["id"],)
        ).fetchall()

        session["user_id"] = user["id"]
        session["company_id"] = user["company_id"]
        session["user_name"] = user["name"]
        session["roles"] = [r["name"] for r in roles]

        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html")


# ------------------------------------------------------------
# Logout route
# ------------------------------------------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for("auth.login"))
