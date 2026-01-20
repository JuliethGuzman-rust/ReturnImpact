# routes/users.py
# User Management (Admin Only) for ReturnImpact.
#
# References:
# - Flask request handling and sessions:
#   https://flask.palletsprojects.com/en/3.0.x/quickstart/
# - CS50 Finance admin-like patterns (restricted actions):
#   https://cs50.harvard.edu/x/2023/track/web/finance/
# - SQLite JOIN documentation:
#   https://www.sqlite.org/lang_select.html
# - MDN forms for basic form structure:
#   https://developer.mozilla.org/en-US/docs/Learn/Forms
# - Werkzeug password hashing:
#   https://werkzeug.palletsprojects.com/en/3.0.x/utils/

from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash
from ..helpers import get_db, login_required

users_bp = Blueprint("users", __name__)


# ------------------------------------------------------------
# ADMIN CHECK HELPER
# Only admins can manage users.
# ------------------------------------------------------------
def admin_required():
    if "admin" not in session.get("roles", []):
        flash("Admin access required.")
        return False
    return True


# ------------------------------------------------------------
# LIST USERS (Admin Only)
# Shows all users belonging to the admin's company.
# ------------------------------------------------------------
@users_bp.route("/users")
@login_required
def list_users():
    if not admin_required():
        return redirect(url_for("dashboard.dashboard"))

    db = get_db()

    users = db.execute(
        """
        SELECT u.id, u.name, u.email, u.created_at,
               GROUP_CONCAT(r.name, ', ') AS roles
        FROM users u
        LEFT JOIN user_roles ur ON ur.user_id = u.id
        LEFT JOIN roles r ON r.id = ur.role_id
        WHERE u.company_id = ?
        GROUP BY u.id
        ORDER BY u.created_at DESC
        """,
        (session["company_id"],)
    ).fetchall()

    return render_template("users/list.html", users=users)


# ------------------------------------------------------------
# CREATE USER (Admin Only)
# ------------------------------------------------------------
@users_bp.route("/users/create", methods=["GET", "POST"])
@login_required
def create_user():
    if not admin_required():
        return redirect(url_for("dashboard.dashboard"))

    db = get_db()

    # Load available roles
    roles = db.execute("SELECT * FROM roles").fetchall()

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email").lower()
        password = request.form.get("password")
        role_ids = request.form.getlist("roles")  # multiple roles allowed

        if not name or not email or not password:
            flash("All fields are required.")
            return render_template("users/create.html", roles=roles)

        password_hash = generate_password_hash(password)

        try:
            # Create user
            cur = db.execute(
                "INSERT INTO users (company_id, name, email, password_hash) VALUES (?, ?, ?, ?)",
                (session["company_id"], name, email, password_hash)
            )
            user_id = cur.lastrowid

            # Assign roles
            for rid in role_ids:
                db.execute(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                    (user_id, rid)
                )

            db.commit()
            flash("User created.")
            return redirect(url_for("users.list_users"))

        except Exception:
            db.rollback()
            flash("Email already exists.")
            return render_template("users/create.html", roles=roles)

    return render_template("users/create.html", roles=roles)


# ------------------------------------------------------------
# EDIT USER (Admin Only)
# ------------------------------------------------------------
@users_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    if not admin_required():
        return redirect(url_for("dashboard.dashboard"))

    db = get_db()

    # Fetch user (must belong to same company)
    user = db.execute(
        "SELECT * FROM users WHERE id = ? AND company_id = ?",
        (user_id, session["company_id"])
    ).fetchone()

    if user is None:
        flash("User not found.")
        return redirect(url_for("users.list_users"))

    # Load all roles
    roles = db.execute("SELECT * FROM roles").fetchall()

    # Load user's current roles
    user_roles = db.execute(
        "SELECT role_id FROM user_roles WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    user_role_ids = {r["role_id"] for r in user_roles}

    if request.method == "POST":
        name = request.form.get("name")
        role_ids = request.form.getlist("roles")

        db.execute(
            "UPDATE users SET name = ? WHERE id = ?",
            (name, user_id)
        )

        # Reset roles
        db.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
        for rid in role_ids:
            db.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, rid)
            )

        db.commit()
        flash("User updated.")
        return redirect(url_for("users.list_users"))

    return render_template(
        "users/edit.html",
        user=user,
        roles=roles,
        user_role_ids=user_role_ids
    )


# ------------------------------------------------------------
# DELETE USER (Admin Only)
# ------------------------------------------------------------
@users_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    if not admin_required():
        return redirect(url_for("dashboard.dashboard"))

    db = get_db()

    # Prevent admin from deleting themselves
    if user_id == session["user_id"]:
        flash("You cannot delete your own account.")
        return redirect(url_for("users.list_users"))

    db.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM users WHERE id = ? AND company_id = ?", (user_id, session["company_id"]))
    db.commit()

    flash("User deleted.")
    return redirect(url_for("users.list_users"))
