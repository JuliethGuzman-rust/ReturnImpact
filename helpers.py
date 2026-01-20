# helpers.py
# Shared utilities for ReturnImpact 
#
# References:
# - Flask SQLite pattern:
#   https://flask.palletsprojects.com/en/3.0.x/patterns/sqlite3/
# - CS50 Finance login_required pattern:
#   https://cs50.harvard.edu/x/2023/track/web/
# - Python functools.wraps:
#   https://docs.python.org/3/library/functools.html#functools.wraps
#
# This module exists to avoid circular imports between app.py and route files.
# Routes import get_db() and login_required() from here instead of app.py.

import sqlite3
from flask import g, session, redirect, url_for, flash
from functools import wraps

import os
DATABASE = os.path.join(os.path.dirname(__file__), "returnimpact.db")
print(">>> USING DATABASE FILE:", DATABASE)


# ------------------------------------------------------------
# Database helper
# Based on Flask's official SQLite documentation.
# ------------------------------------------------------------
def get_db():
    """Open a new SQLite database connection for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # return rows as dictionaries
    return g.db


# ------------------------------------------------------------
# Login-required decorator
# Inspired by CS50 Finance and Flask documentation.
# ------------------------------------------------------------
def login_required(view):
    """Redirect user to login page if not logged in."""
    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped_view
