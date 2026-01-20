"""
routes/returns.py
Return + ReturnItem CRUD for ReturnImpact.

Academic References:
- CS50 SQL patterns for CRUD and filtering:
  https://cs50.harvard.edu/x/2023/sql/
- Flask Request & Form Handling:
  https://flask.palletsprojects.com/en/3.0.x/quickstart/#http-methods
- MDN Form Structure & Semantics:
  https://developer.mozilla.org/en-US/docs/Web/HTML/Element/form
- SQLite JOIN Documentation:
  https://www.sqlite.org/lang_select.html
- Climatiq Intermodal Freight API v3:
  https://www.climatiq.io/docs/api-reference/intermodal-freight/intermodal-freight-v3

Design Notes:
- Supports both single-mode and fully dynamic multimodal routing.
- Multimodal routing is parsed from create.html dynamic fields:
  legs[index][start], legs[index][mode], legs[index][end].
- CO₂ is calculated using calculate_co2_intermodal_route(), which expects
  alternating route parts:
    {"location": "..."},
    {"transport_mode": "road|air|sea|rail"},
    {"location": "..."},
    ...
  (NO "leg" wrapper for v3).
- transport_summary (TEXT) is stored on each return for easy display of
  multimodal transport sequences like "Road → Air → Rail".
- To prevent "not close enough to transition point" errors for air/sea,
  we attach location_options.tolerance_km to EACH location step.
"""

import csv
from io import StringIO

from flask import Blueprint, render_template, request, redirect, session, url_for, flash, Response

from helpers import get_db, login_required
from co2_api import calculate_co2_intermodal_route, ClimatiqError

returns_bp = Blueprint("returns", __name__)


# =====================================================================
# HELPERS
# =====================================================================
def _apply_location_options(route, tolerance_km=50):
    """
    Climatiq v3: location_options belongs inside each location object.
    We add tolerance_km so city-level locations can snap to airports/ports.
    """
    updated = []
    for step in route:
        if isinstance(step, dict) and "location" in step:
            loc = (step.get("location") or "").strip()
            updated.append(
                {"location": loc, "location_options": {"tolerance_km": tolerance_km}}
            )
        else:
            updated.append(step)
    return updated


# =====================================================================
# LIST RETURNS
# =====================================================================
@returns_bp.route("/returns")
@login_required
def list_returns():
    db = get_db()

    rows = db.execute(
        """
        SELECT r.id, r.order_number, r.return_date,
               r.departure_location, r.destination_location,
               r.weight_kg, r.co2_kg,
               r.cost_refund, r.cost_shipping, r.cost_handling, r.cost_restocking,
               r.transport_summary,
               tm.name AS transport_name
        FROM returns r
        LEFT JOIN transport_modes tm ON r.transport_mode_id = tm.id
        WHERE r.company_id = ?
        ORDER BY r.return_date DESC
        """,
        (session["company_id"],),
    ).fetchall()

    return render_template("returns/list.html", returns=rows)


# =====================================================================
# CREATE RETURN (Single-mode + Multimodal)
# =====================================================================
@returns_bp.route("/returns/create", methods=["GET", "POST"])
@login_required
def create_return():
    """
    Create a new return record with support for both single-mode and
    fully dynamic multimodal routing.
    """
    db = get_db()
    transport_modes = db.execute("SELECT * FROM transport_modes").fetchall()

    if request.method == "POST":
        # ------------------------------------------------------------
        # BASIC FIELDS
        # ------------------------------------------------------------
        order_number = (request.form.get("order_number") or "").strip()
        return_date = request.form.get("return_date")
        routing_type = request.form.get("routing_type")

        # Weight (validated)
        raw_weight = (request.form.get("weight_kg", "") or "").replace(",", ".").strip()
        if raw_weight == "":
            flash("Weight is required.")
            return redirect(url_for("returns.create_return"))

        try:
            weight_kg = float(raw_weight)
        except ValueError:
            flash("Weight must be a valid number.")
            return redirect(url_for("returns.create_return"))

        # Optional cost fields
        cost_refund = float(request.form.get("cost_refund") or 0)
        cost_shipping = float(request.form.get("cost_shipping") or 0)
        cost_handling = float(request.form.get("cost_handling") or 0)
        cost_restocking = float(request.form.get("cost_restocking") or 0)
        notes = request.form.get("notes")

        # ------------------------------------------------------------
        # ROUTE BUILDING (Climatiq v3 format)
        # route must alternate: location, transport_mode, location, ...
        # ------------------------------------------------------------
        route = []
        departure_location = ""
        destination_location = ""
        transport_mode_id_final = None
        transport_summary = None

        if routing_type == "single":
            transport_mode_id = request.form.get("transport_mode_id")

            mode_row = db.execute(
                "SELECT api_value FROM transport_modes WHERE id = ?",
                (transport_mode_id,),
            ).fetchone()

            if mode_row is None:
                flash("Invalid transport mode.")
                return redirect(url_for("returns.create_return"))

            mode = (mode_row["api_value"] or "").strip()  # road/air/sea/rail
            departure = (request.form.get("departure_location") or "").strip()
            destination = (request.form.get("destination_location") or "").strip()

            route = [
                {"location": departure},
                {"transport_mode": mode},
                {"location": destination},
            ]

            departure_location = departure
            destination_location = destination
            transport_mode_id_final = transport_mode_id
            transport_summary = mode.title() if mode else "—"

        else:
            # MULTIMODAL
            legs = []

            for key in request.form:
                if key.startswith("legs["):
                    index = key.split("[")[1].split("]")[0]
                    field = key.split("[")[2].split("]")[0]

                    while len(legs) <= int(index):
                        legs.append({"start": None, "mode": None, "end": None})

                    legs[int(index)][field] = request.form.get(key)

            if legs:
                first_start = (legs[0].get("start") or "").strip()
                route.append({"location": first_start})

                for leg in legs:
                    mode = (leg.get("mode") or "").strip()
                    end = (leg.get("end") or "").strip()
                    route.append({"transport_mode": mode})
                    route.append({"location": end})

            departure_location = (route[0].get("location") or "").strip() if route else ""
            destination_location = (route[-1].get("location") or "").strip() if route else ""
            transport_mode_id_final = None

            modes = []
            for step in route:
                if "transport_mode" in step:
                    m = (step.get("transport_mode") or "").strip()
                    if m:
                        modes.append(m.title())
            transport_summary = " → ".join(modes) if modes else "—"

        # Add tolerance_km to each location (helps with airports/ports snapping)
        route = _apply_location_options(route, tolerance_km=50)

        # ------------------------------------------------------------
        # CO₂ CALCULATION + VALIDATION
        # ------------------------------------------------------------
        try:
            if len(route) < 3:
                raise ClimatiqError("Route must include at least: location → transport_mode → location.")

            if "location" not in route[0] or "location" not in route[-1]:
                raise ClimatiqError("Route must start and end with a location.")

            for i, step in enumerate(route):
                if i % 2 == 0:
                    if "location" not in step:
                        raise ClimatiqError("Route must alternate: location, transport_mode, location, ...")
                    loc = (step.get("location") or "").strip()
                    if not loc:
                        raise ClimatiqError("Locations cannot be empty. Please fill in all start/end locations.")
                else:
                    if "transport_mode" not in step:
                        raise ClimatiqError("Route must alternate: location, transport_mode, location, ...")
                    mode = (step.get("transport_mode") or "").strip()
                    if not mode:
                        raise ClimatiqError("Each route leg must include a transport mode.")

            co2_kg = calculate_co2_intermodal_route(route, weight_kg)
            flash(f"CO₂ calculation successful: {co2_kg:.3f} kg", "success")

        except ClimatiqError as e:
            co2_kg = 0
            flash(f"CO₂ calculation failed: {e}. CO₂ set to 0.", "warning")

        # ------------------------------------------------------------
        # INSERT RETURN
        # ------------------------------------------------------------
        db.execute(
            """
            INSERT INTO returns (
                company_id, order_number, return_date,
                transport_mode_id, transport_summary,
                departure_location, destination_location,
                weight_kg, co2_kg,
                cost_refund, cost_shipping, cost_handling, cost_restocking,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["company_id"],
                order_number,
                return_date,
                transport_mode_id_final,
                transport_summary,
                departure_location,
                destination_location,
                weight_kg,
                co2_kg,
                cost_refund,
                cost_shipping,
                cost_handling,
                cost_restocking,
                notes,
            ),
        )
        db.commit()

        flash("Return created.")
        return redirect(url_for("returns.list_returns"))

    return render_template("returns/create.html", transport_modes=transport_modes)


# =====================================================================
# VIEW RETURN + ITEMS
# =====================================================================
@returns_bp.route("/returns/<int:return_id>")
@login_required
def view_return(return_id):
    db = get_db()

    ret = db.execute(
        """
        SELECT r.*,
               tm.name AS transport_name
        FROM returns r
        LEFT JOIN transport_modes tm ON r.transport_mode_id = tm.id
        WHERE r.id = ? AND r.company_id = ?
        """,
        (return_id, session["company_id"]),
    ).fetchone()

    if ret is None:
        flash("Return not found.")
        return redirect(url_for("returns.list_returns"))

    items = db.execute(
        """
        SELECT ri.*, p.name AS product_name, v.name AS variant_name
        FROM return_items ri
        LEFT JOIN products p ON ri.product_id = p.id
        LEFT JOIN product_variants v ON ri.variant_id = v.id
        WHERE ri.return_id = ?
        """,
        (return_id,),
    ).fetchall()

    return render_template("returns/view.html", ret=ret, items=items)


# =====================================================================
# ADD ITEM TO RETURN
# =====================================================================
@returns_bp.route("/returns/<int:return_id>/add-item", methods=["GET", "POST"])
@login_required
def add_return_item(return_id):
    db = get_db()

    ret = db.execute(
        "SELECT * FROM returns WHERE id = ? AND company_id = ?",
        (return_id, session["company_id"]),
    ).fetchone()

    if ret is None:
        flash("Return not found.")
        return redirect(url_for("returns.list_returns"))

    products = db.execute(
        "SELECT * FROM products WHERE company_id = ?",
        (session["company_id"],),
    ).fetchall()

    variants = db.execute(
        """
        SELECT v.*, p.name AS product_name
        FROM product_variants v
        JOIN products p ON v.product_id = p.id
        WHERE p.company_id = ?
        """,
        (session["company_id"],),
    ).fetchall()

    if request.method == "POST":
        db.execute(
            """
            INSERT INTO return_items (
                return_id, product_id, variant_id,
                quantity, weight, dimensions, condition,
                restockable, hazardous, temperature_sensitive
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                return_id,
                request.form.get("product_id"),
                request.form.get("variant_id") or None,
                request.form.get("quantity"),
                request.form.get("weight"),
                request.form.get("dimensions"),
                request.form.get("condition"),
                1 if request.form.get("restockable") else 0,
                1 if request.form.get("hazardous") else 0,
                1 if request.form.get("temperature_sensitive") else 0,
            ),
        )
        db.commit()
        flash("Item added.")
        return redirect(url_for("returns.view_return", return_id=return_id))

    return render_template(
        "returns/add_item.html",
        ret=ret,
        products=products,
        variants=variants,
    )


# =====================================================================
# DELETE RETURN
# =====================================================================
@returns_bp.route("/returns/<int:return_id>/delete", methods=["POST"])
@login_required
def delete_return(return_id):
    db = get_db()

    db.execute(
        "DELETE FROM returns WHERE id = ? AND company_id = ?",
        (return_id, session["company_id"]),
    )
    db.commit()

    flash("Return deleted.")
    return redirect(url_for("returns.list_returns"))


# =====================================================================
# DOWNLOAD RETURNS TABLE (CSV)
# =====================================================================
@returns_bp.route("/returns/download/csv")
@login_required
def download_returns_csv():
    db = get_db()

    rows = db.execute(
        """
        SELECT r.id, r.order_number, r.return_date,
               r.transport_summary,
               tm.name AS transport_name,
               r.departure_location, r.destination_location,
               r.weight_kg, r.co2_kg,
               r.cost_refund, r.cost_shipping, r.cost_handling, r.cost_restocking,
               r.notes
        FROM returns r
        LEFT JOIN transport_modes tm ON r.transport_mode_id = tm.id
        WHERE r.company_id = ?
        ORDER BY r.return_date DESC
        """,
        (session["company_id"],),
    ).fetchall()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "id",
            "order_number",
            "return_date",
            "transport",
            "departure_location",
            "destination_location",
            "weight_kg",
            "co2_kg",
            "cost_refund_eur",
            "cost_shipping_eur",
            "cost_handling_eur",
            "cost_restocking_eur",
            "total_cost_eur",
            "notes",
        ]
    )

    for r in rows:
        total_cost = (
            (r["cost_refund"] or 0)
            + (r["cost_shipping"] or 0)
            + (r["cost_handling"] or 0)
            + (r["cost_restocking"] or 0)
        )

        transport = r["transport_summary"] or r["transport_name"] or ""

        writer.writerow(
            [
                r["id"],
                r["order_number"],
                r["return_date"],
                transport,
                r["departure_location"] or "",
                r["destination_location"] or "",
                r["weight_kg"] if r["weight_kg"] is not None else "",
                r["co2_kg"] if r["co2_kg"] is not None else "",
                r["cost_refund"] or 0,
                r["cost_shipping"] or 0,
                r["cost_handling"] or 0,
                r["cost_restocking"] or 0,
                round(total_cost, 2),
                r["notes"] or "",
            ]
        )

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=returns.csv"},
    )
