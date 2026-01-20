# routes/products.py
# Product CRUD routes for ReturnImpact.
#
# References:
# - CS50 Finance SQL filtering patterns: https://cs50.harvard.edu/x/2023/track/web/finance/
# - Flask request handling: https://flask.palletsprojects.com/en/3.0.x/quickstart/
# - MDN forms: https://developer.mozilla.org/en-US/docs/Learn/Forms

from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from ..helpers import get_db, login_required

products_bp = Blueprint("products", __name__)


# ------------------------------------------------------------
# LIST PRODUCTS
# ------------------------------------------------------------
@products_bp.route("/products")
@login_required
def list_products():
    """Show all products for the logged-in company."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM products WHERE company_id = ? ORDER BY created_at DESC",
        (session["company_id"],)
    ).fetchall()
    return render_template("products/list.html", products=rows)


# ------------------------------------------------------------
# CREATE PRODUCT
# ------------------------------------------------------------
@products_bp.route("/products/create", methods=["GET", "POST"])
@login_required
def create_product():
    """Create a new product (admin or manager only)."""
    if "admin" not in session["roles"] and "manager" not in session["roles"]:
        flash("You do not have permission to create products.")
        return redirect(url_for("products.list_products"))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")

        if not name:
            flash("Product name is required.")
            return render_template("products/create.html")

        db = get_db()
        db.execute(
            "INSERT INTO products (company_id, name, description) VALUES (?, ?, ?)",
            (session["company_id"], name, description)
        )
        db.commit()

        flash("Product created.")
        return redirect(url_for("products.list_products"))

    return render_template("products/create.html")


# ------------------------------------------------------------
# EDIT PRODUCT
# ------------------------------------------------------------
@products_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    """Edit an existing product (admin or manager only)."""
    if "admin" not in session["roles"] and "manager" not in session["roles"]:
        flash("You do not have permission to edit products.")
        return redirect(url_for("products.list_products"))

    db = get_db()

    product = db.execute(
        "SELECT * FROM products WHERE id = ? AND company_id = ?",
        (product_id, session["company_id"])
    ).fetchone()

    if product is None:
        flash("Product not found.")
        return redirect(url_for("products.list_products"))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")

        db.execute(
            "UPDATE products SET name = ?, description = ? WHERE id = ?",
            (name, description, product_id)
        )
        db.commit()

        flash("Product updated.")
        return redirect(url_for("products.list_products"))

    return render_template("products/edit.html", product=product)


# ------------------------------------------------------------
# DELETE PRODUCT
# ------------------------------------------------------------
@products_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    """Delete a product (admin or manager only)."""
    if "admin" not in session["roles"] and "manager" not in session["roles"]:
        flash("You do not have permission to delete products.")
        return redirect(url_for("products.list_products"))

    db = get_db()
    db.execute(
        "DELETE FROM products WHERE id = ? AND company_id = ?",
        (product_id, session["company_id"])
    )
    db.commit()

    flash("Product deleted.")
    return redirect(url_for("products.list_products"))

