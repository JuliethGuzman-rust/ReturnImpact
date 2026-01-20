# routes/variants.py
# Product Variant CRUD for ReturnImpact.
# References:
# - SQLite JOIN docs: https://www.sqlite.org/lang_select.html
# - CS50 Finance delete/update patterns: https://cs50.harvard.edu/x/2023/track/web/finance/

from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from ..helpers import get_db, login_required

variants_bp = Blueprint("variants", __name__)


# ------------------------------------------------------------
# List variants for a product
# ------------------------------------------------------------
@variants_bp.route("/products/<int:product_id>/variants")
@login_required
def variants(product_id):
    db = get_db()

    product = db.execute(
        "SELECT * FROM products WHERE id = ? AND company_id = ?",
        (product_id, session["company_id"])
    ).fetchone()

    if product is None:
        flash("Product not found.")
        return redirect(url_for("products.products"))

    rows = db.execute(
        "SELECT * FROM product_variants WHERE product_id = ? ORDER BY id DESC",
        (product_id,)
    ).fetchall()

    return render_template("variants/list.html", product=product, variants=rows)


# ------------------------------------------------------------
# Create variant
# ------------------------------------------------------------
@variants_bp.route("/products/<int:product_id>/variants/create", methods=["GET", "POST"])
@login_required
def create_variant(product_id):
    if "admin" not in session["roles"] and "manager" not in session["roles"]:
        flash("You do not have permission to create variants.")
        return redirect(url_for("products.products"))

    db = get_db()

    product = db.execute(
        "SELECT * FROM products WHERE id = ? AND company_id = ?",
        (product_id, session["company_id"])
    ).fetchone()

    if product is None:
        flash("Product not found.")
        return redirect(url_for("products.products"))

    if request.method == "POST":
        name = request.form.get("name")
        sku = request.form.get("sku")

        if not name:
            flash("Variant name is required.")
            return render_template("variants/create.html", product=product)

        db.execute(
            "INSERT INTO product_variants (product_id, name, sku) VALUES (?, ?, ?)",
            (product_id, name, sku)
        )
        db.commit()

        flash("Variant created.")
        return redirect(url_for("variants.variants", product_id=product_id))

    return render_template("variants/create.html", product=product)


# ------------------------------------------------------------
# Edit variant
# ------------------------------------------------------------
@variants_bp.route("/variants/<int:variant_id>/edit", methods=["GET", "POST"])
@login_required
def edit_variant(variant_id):
    db = get_db()

    variant = db.execute(
        """
        SELECT v.*, p.company_id, p.name AS product_name
        FROM product_variants v
        JOIN products p ON v.product_id = p.id
        WHERE v.id = ?
        """,
        (variant_id,)
    ).fetchone()

    if variant is None or variant["company_id"] != session["company_id"]:
        flash("Variant not found.")
        return redirect(url_for("products.products"))

    if "admin" not in session["roles"] and "manager" not in session["roles"]:
        flash("You do not have permission to edit variants.")
        return redirect(url_for("products.products"))

    if request.method == "POST":
        name = request.form.get("name")
        sku = request.form.get("sku")

        db.execute(
            "UPDATE product_variants SET name = ?, sku = ? WHERE id = ?",
            (name, sku, variant_id)
        )
        db.commit()

        flash("Variant updated.")
        return redirect(url_for("variants.variants", product_id=variant["product_id"]))

    return render_template("variants/edit.html", variant=variant)


# ------------------------------------------------------------
# Delete variant
# ------------------------------------------------------------
@variants_bp.route("/variants/<int:variant_id>/delete", methods=["POST"])
@login_required
def delete_variant(variant_id):
    db = get_db()

    variant = db.execute(
        """
        SELECT v.*, p.company_id
        FROM product_variants v
        JOIN products p ON v.product_id = p.id
        WHERE v.id = ?
        """,
        (variant_id,)
    ).fetchone()

    if variant is None or variant["company_id"] != session["company_id"]:
        flash("Variant not found.")
        return redirect(url_for("products.products"))

    if "admin" not in session["roles"] and "manager" not in session["roles"]:
        flash("You do not have permission to delete variants.")
        return redirect(url_for("products.products"))

    db.execute("DELETE FROM product_variants WHERE id = ?", (variant_id,))
    db.commit()

    flash("Variant deleted.")
    return redirect(url_for("variants.variants", product_id=variant["product_id"]))
