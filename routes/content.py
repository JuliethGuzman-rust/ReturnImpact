# routes/content.py
# Content Post CRUD for ReturnImpact.
#
# References:
# - Flask request handling: https://flask.palletsprojects.com/en/3.0.x/quickstart/
# - CS50 Finance admin-like patterns: https://cs50.harvard.edu/x/2023/track/web/finance/
# - SQLite INSERT/UPDATE docs: https://www.sqlite.org/lang_insert.html
# - MDN forms: https://developer.mozilla.org/en-US/docs/Learn/Forms

from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from helpers import get_db, login_required

content_bp = Blueprint("content", __name__)


# ------------------------------------------------------------
# ADMIN CHECK
# Only admins can manage content posts.
# ------------------------------------------------------------
def admin_required():
    if "admin" not in session.get("roles", []):
        flash("Admin access required.")
        return False
    return True


# ------------------------------------------------------------
# LIST POSTS (Admin Only)
# ------------------------------------------------------------
@content_bp.route("/content-posts")
@login_required
def list_posts():
    if not admin_required():
        return redirect(url_for("dashboard.dashboard"))

    db = get_db()

    posts = db.execute(
        """
        SELECT * FROM content_posts
        WHERE company_id = ?
        ORDER BY created_at DESC
        """,
        (session["company_id"],)
    ).fetchall()

    return render_template("content/list.html", posts=posts)


# ------------------------------------------------------------
# CREATE POST
# ------------------------------------------------------------
@content_bp.route("/content-posts/create", methods=["GET", "POST"])
@login_required
def create_post():
    if not admin_required():
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        title = request.form.get("title")
        body = request.form.get("body")

        if not title or not body:
            flash("Title and body are required.")
            return render_template("content/create.html")

        db = get_db()
        db.execute(
            "INSERT INTO content_posts (company_id, title, body) VALUES (?, ?, ?)",
            (session["company_id"], title, body)
        )
        db.commit()

        flash("Post created.")
        return redirect(url_for("content.list_posts"))

    return render_template("content/create.html")


# ------------------------------------------------------------
# EDIT POST
# ------------------------------------------------------------
@content_bp.route("/content-posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    if not admin_required():
        return redirect(url_for("dashboard.dashboard"))

    db = get_db()

    post = db.execute(
        "SELECT * FROM content_posts WHERE id = ? AND company_id = ?",
        (post_id, session["company_id"])
    ).fetchone()

    if post is None:
        flash("Post not found.")
        return redirect(url_for("content.list_posts"))

    if request.method == "POST":
        title = request.form.get("title")
        body = request.form.get("body")

        db.execute(
            "UPDATE content_posts SET title = ?, body = ? WHERE id = ?",
            (title, body, post_id)
        )
        db.commit()

        flash("Post updated.")
        return redirect(url_for("content.list_posts"))

    return render_template("content/edit.html", post=post)


# ------------------------------------------------------------
# DELETE POST
# ------------------------------------------------------------
@content_bp.route("/content-posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    if not admin_required():
        return redirect(url_for("dashboard.dashboard"))

    db = get_db()
    db.execute(
        "DELETE FROM content_posts WHERE id = ? AND company_id = ?",
        (post_id, session["company_id"])
    )
    db.commit()

    flash("Post deleted.")
    return redirect(url_for("content.list_posts"))
