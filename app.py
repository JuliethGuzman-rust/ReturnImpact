# app.py
# ReturnImpact — CS50 Final Project
# Main Flask application file.
#
# References:
# - Flask documentation (app factory, blueprints):
#   https://flask.palletsprojects.com/en/3.0.x/
# - CS50 Web Track examples (sessions, decorators):
#   https://cs50.harvard.edu/x/2023/track/web/
# - SQLite connection pattern:
#   https://flask.palletsprojects.com/en/3.0.x/patterns/sqlite3/
# - python-dotenv for environment variables:
#   https://pypi.org/project/python-dotenv/

import os
import json
from dotenv import load_dotenv
from flask import Flask, g, session, redirect, url_for, flash, render_template

# Load environment variables from .env
load_dotenv()

# Import shared helpers (avoids circular imports)
from .helpers import get_db, login_required

app = Flask(__name__)

# Secret key stored securely in .env
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-key-change-this")

# ------------------------------------------------------------
# Inject external links from JSON into all templates
# ------------------------------------------------------------
@app.context_processor
def inject_links():
    json_path = os.path.join(app.static_folder, "data", "links.json")
    try:
        with open(json_path, "r") as f:
            links = json.load(f)
    except Exception:
        links = {}  # fallback if file missing
    return dict(LINKS=links)

# ------------------------------------------------------------
# Database teardown
# Based on Flask's official SQLite pattern.
# ------------------------------------------------------------
@app.teardown_appcontext
def close_db(exception):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ------------------------------------------------------------
# Register Blueprints
# Using package-relative imports to avoid circular imports.
# ------------------------------------------------------------
from .routes.auth import auth_bp
from .routes.products import products_bp
from .routes.variants import variants_bp
from .routes.dashboard import dashboard_bp
from .routes.returns import returns_bp
from .routes.users import users_bp
from .routes.content import content_bp

app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)
app.register_blueprint(variants_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(returns_bp)
app.register_blueprint(users_bp)
app.register_blueprint(content_bp)


# ------------------------------------------------------------
# Public landing page
# Shows recent posts for the selected company.
# ------------------------------------------------------------
@app.route("/")
def index():
    db = get_db()

    posts = db.execute(
        """
        SELECT * FROM content_posts
        WHERE company_id = ?
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (session.get("company_id", 1),)  # fallback for public view
    ).fetchall()

    return render_template("index.html", posts=posts)


# ------------------------------------------------------------
# Run the app (development only)
# ------------------------------------------------------------
if __name__ == "__main__":
    # When running as a module, use:
    # python -m returnImpact.app
    app.run(debug=True)
