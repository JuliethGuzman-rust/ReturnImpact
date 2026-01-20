# routes/dashboard.py
# Dashboard + Analytics routes for ReturnImpact.
#
# Academic References:
# - SQL aggregation functions (COUNT, SUM):
#     https://www.sqlite.org/lang_aggfunc.html
# - CS50 Finance index route (aggregating totals for a user):
#     https://cs50.harvard.edu/x/2023/track/web/finance/
# - Flask template rendering:
#     https://flask.palletsprojects.com/en/3.0.x/quickstart/#rendering-templates
# - HTML-to-PDF conversion (pdfkit):
#     https://pypi.org/project/pdfkit/
#
# CO₂ equivalence scientific references:
# - Petrol car emissions (~0.16 kg CO₂ per km)
# - Smartphone charging (~0.0073 kg CO₂ per charge)
# - Tree absorption (~22 kg CO₂ per year)
#
# Design notes:
# - SUM() may return NULL → handled with `or 0`
# - All CO₂ values normalized to floats for Chart.js
# - Dashboard summary export supports CSV, JSON, and PDF

from flask import Blueprint, render_template, session, Response, jsonify, make_response
from ..helpers import get_db, login_required
from datetime import datetime
import csv
import io
import pdfkit

dashboard_bp = Blueprint("dashboard", __name__)


# ------------------------------------------------------------
# MAIN DASHBOARD
# ------------------------------------------------------------
# ------------------------------------------------------------
# ANALYTICS DASHBOARD (PAGE VIEW)
# ------------------------------------------------------------
@dashboard_bp.route("/analytics")
@login_required
def analytics():
    db = get_db()

    total_co2 = db.execute(
        "SELECT SUM(co2_kg) AS total FROM returns WHERE company_id = ?",
        (session["company_id"],)
    ).fetchone()["total"] or 0

    # CO₂ by transport mode
    raw_modes = db.execute(
        """
        SELECT tm.name AS mode, SUM(r.co2_kg) AS total
        FROM returns r
        LEFT JOIN transport_modes tm ON r.transport_mode_id = tm.id
        WHERE r.company_id = ?
        GROUP BY tm.name
        ORDER BY total DESC
        """,
        (session["company_id"],)
    ).fetchall()

    co2_by_mode = [
        {"mode": row["mode"], "total": float(row["total"] or 0)}
        for row in raw_modes
    ]

    # Monthly CO₂ trend
    raw_months = db.execute(
        """
        SELECT strftime('%Y-%m', return_date) AS month,
               SUM(co2_kg) AS total
        FROM returns
        WHERE company_id = ?
        GROUP BY month
        ORDER BY month ASC
        """,
        (session["company_id"],)
    ).fetchall()

    co2_by_month = [
        {"month": row["month"], "total": float(row["total"] or 0)}
        for row in raw_months
    ]

    # Equivalences
    CAR_CO2_PER_KM = 0.16
    PHONE_CO2_PER_CHARGE = 0.0073
    TREE_CO2_PER_YEAR = 22

    km_driven = total_co2 / CAR_CO2_PER_KM if total_co2 else 0
    phone_charges = total_co2 / PHONE_CO2_PER_CHARGE if total_co2 else 0
    trees_needed = total_co2 / TREE_CO2_PER_YEAR if total_co2 else 0

    return render_template(
        "analytics.html",
        total_co2=total_co2,
        co2_by_mode=co2_by_mode,
        co2_by_month=co2_by_month,
        km_driven=km_driven,
        phone_charges=phone_charges,
        trees_needed=trees_needed
    )

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    db = get_db()

    # Total returns
    total_returns = db.execute(
        "SELECT COUNT(*) AS count FROM returns WHERE company_id = ?",
        (session["company_id"],)
    ).fetchone()["count"]

    # Total CO₂ emissions
    total_co2 = db.execute(
        "SELECT SUM(co2_kg) AS total FROM returns WHERE company_id = ?",
        (session["company_id"],)
    ).fetchone()["total"] or 0

    # Total cost (refund + shipping + handling + restocking)
    total_cost = db.execute(
        """
        SELECT SUM(
            COALESCE(cost_refund, 0) +
            COALESCE(cost_shipping, 0) +
            COALESCE(cost_handling, 0) +
            COALESCE(cost_restocking, 0)
        ) AS total
        FROM returns
        WHERE company_id = ?
        """,
        (session["company_id"],)
    ).fetchone()["total"] or 0

    # Recent returns (last 5)
    recent = db.execute(
        """
        SELECT id, order_number, return_date, co2_kg
        FROM returns
        WHERE company_id = ?
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (session["company_id"],)
    ).fetchall()

    return render_template(
        "dashboard.html",
        total_returns=total_returns,
        total_co2=total_co2,
        total_cost=total_cost,
        recent=recent
    )


# ------------------------------------------------------------
# ANALYTICS DASHBOARD
# ------------------------------------------------------------
@dashboard_bp.route("/download-analytics-pdf")
@login_required
def download_analytics_pdf():
    db = get_db()

    total_co2 = db.execute(
        "SELECT SUM(co2_kg) AS total FROM returns WHERE company_id = ?",
        (session["company_id"],)
    ).fetchone()["total"] or 0

    # CO₂ by transport mode
    raw_modes = db.execute(
        """
        SELECT tm.name AS mode, SUM(r.co2_kg) AS total
        FROM returns r
        LEFT JOIN transport_modes tm ON r.transport_mode_id = tm.id
        WHERE r.company_id = ?
        GROUP BY tm.name
        ORDER BY total DESC
        """,
        (session["company_id"],)
    ).fetchall()

    co2_by_mode = [
        {"mode": row["mode"], "total": float(row["total"] or 0)}
        for row in raw_modes
    ]

    # Monthly CO₂ trend
    raw_months = db.execute(
        """
        SELECT strftime('%Y-%m', return_date) AS month,
               SUM(co2_kg) AS total
        FROM returns
        WHERE company_id = ?
        GROUP BY month
        ORDER BY month ASC
        """,
        (session["company_id"],)
    ).fetchall()

    co2_by_month = [
        {"month": row["month"], "total": float(row["total"] or 0)}
        for row in raw_months
    ]

    # Equivalences
    CAR_CO2_PER_KM = 0.16
    PHONE_CO2_PER_CHARGE = 0.0073
    TREE_CO2_PER_YEAR = 22

    km_driven = total_co2 / CAR_CO2_PER_KM if total_co2 else 0
    phone_charges = total_co2 / PHONE_CO2_PER_CHARGE if total_co2 else 0
    trees_needed = total_co2 / TREE_CO2_PER_YEAR if total_co2 else 0

    html = render_template(
        "analytics_pdf.html",
        total_co2=total_co2,
        co2_by_mode=co2_by_mode,
        co2_by_month=co2_by_month,
        km_driven=km_driven,
        phone_charges=phone_charges,
        trees_needed=trees_needed,
        generated_date=datetime.now().strftime("%Y-%m-%d")
    )

    config = pdfkit.configuration(wkhtmltopdf="/usr/local/bin/wkhtmltopdf")
    options = {"enable-local-file-access": None}

    pdf = pdfkit.from_string(html, False, configuration=config, options=options)

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=analytics_report.pdf"
    return response

@dashboard_bp.route("/download-analytics/<format>")
@login_required
def download_analytics(format):
    db = get_db()

    total_co2 = db.execute(
        "SELECT SUM(co2_kg) AS total FROM returns WHERE company_id = ?",
        (session["company_id"],)
    ).fetchone()["total"] or 0

    raw_modes = db.execute(
        """
        SELECT tm.name AS mode, SUM(r.co2_kg) AS total
        FROM returns r
        LEFT JOIN transport_modes tm ON r.transport_mode_id = tm.id
        WHERE r.company_id = ?
        GROUP BY tm.name
        ORDER BY total DESC
        """,
        (session["company_id"],)
    ).fetchall()

    raw_months = db.execute(
        """
        SELECT strftime('%Y-%m', return_date) AS month,
               SUM(co2_kg) AS total
        FROM returns
        WHERE company_id = ?
        GROUP BY month
        ORDER BY month ASC
        """,
        (session["company_id"],)
    ).fetchall()

    data = {
        "total_co2": total_co2,
        "co2_by_mode": [dict(row) for row in raw_modes],
        "co2_by_month": [dict(row) for row in raw_months]
    }

    if format == "json":
        return jsonify(data)

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total CO₂ (kg)", total_co2])

        writer.writerow([])
        writer.writerow(["CO₂ by Transport Mode"])
        writer.writerow(["Mode", "CO₂ (kg)"])
        for row in raw_modes:
            writer.writerow([row["mode"], row["total"]])

        writer.writerow([])
        writer.writerow(["Monthly CO₂ Trend"])
        writer.writerow(["Month", "CO₂ (kg)"])
        for row in raw_months:
            writer.writerow([row["month"], row["total"]])

        response = Response(output.getvalue(), mimetype="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=analytics_summary.csv"
        return response

    return "Invalid format", 400

# ------------------------------------------------------------
# DOWNLOAD DASHBOARD SUMMARY (CSV / JSON)
# ------------------------------------------------------------
@dashboard_bp.route("/download-dashboard/<format>")
@login_required
def download_dashboard(format):
    db = get_db()

    total_returns = db.execute(
        "SELECT COUNT(*) AS count FROM returns WHERE company_id = ?",
        (session["company_id"],)
    ).fetchone()["count"]

    total_co2 = db.execute(
        "SELECT SUM(co2_kg) AS total FROM returns WHERE company_id = ?",
        (session["company_id"],)
    ).fetchone()["total"] or 0

    total_cost = db.execute(
        """
        SELECT SUM(
            COALESCE(cost_refund,0) +
            COALESCE(cost_shipping,0) +
            COALESCE(cost_handling,0) +
            COALESCE(cost_restocking,0)
        ) AS total
        FROM returns
        WHERE company_id = ?
        """,
        (session["company_id"],)
    ).fetchone()["total"] or 0

    recent = db.execute(
        """
        SELECT id, order_number, return_date, co2_kg
        FROM returns
        WHERE company_id = ?
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (session["company_id"],)
    ).fetchall()

    data = {
        "total_returns": total_returns,
        "total_co2": total_co2,
        "total_cost": total_cost,
        "recent": [dict(r) for r in recent]
    }

    # JSON export
    if format == "json":
        return jsonify(data)

    # CSV export
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Returns", total_returns])
        writer.writerow(["Total CO₂ (kg)", total_co2])
        writer.writerow(["Total Cost ($)", total_cost])

        writer.writerow([])
        writer.writerow(["Recent Returns"])
        writer.writerow(["ID", "Order #", "Date", "CO₂ (kg)"])

        for r in recent:
            writer.writerow([r["id"], r["order_number"], r["return_date"], r["co2_kg"]])

        response = Response(output.getvalue(), mimetype="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=dashboard_summary.csv"
        return response

    return "Invalid format", 400


# ------------------------------------------------------------
# PDF EXPORT — DASHBOARD SUMMARY
# ------------------------------------------------------------
@dashboard_bp.route("/download-dashboard-pdf")
@login_required
def download_dashboard_pdf():
    db = get_db()

    total_returns = db.execute(
        "SELECT COUNT(*) AS count FROM returns WHERE company_id = ?",
        (session["company_id"],)
    ).fetchone()["count"]

    total_co2 = db.execute(
        "SELECT SUM(co2_kg) AS total FROM returns WHERE company_id = ?",
        (session["company_id"],)
    ).fetchone()["total"] or 0

    total_cost = db.execute(
        """
        SELECT SUM(
            COALESCE(cost_refund,0) +
            COALESCE(cost_shipping,0) +
            COALESCE(cost_handling,0) +
            COALESCE(cost_restocking,0)
        ) AS total
        FROM returns
        WHERE company_id = ?
        """,
        (session["company_id"],)
    ).fetchone()["total"] or 0

    recent = db.execute(
        """
        SELECT id, order_number, return_date, co2_kg
        FROM returns
        WHERE company_id = ?
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (session["company_id"],)
    ).fetchall()

    html = render_template(
        "dashboard_pdf.html",
        total_returns=total_returns,
        total_co2=total_co2,
        total_cost=total_cost,
        recent=recent,
        generated_date=datetime.now().strftime("%Y-%m-%d")
    )

    config = pdfkit.configuration(wkhtmltopdf="/usr/local/bin/wkhtmltopdf")
    options = {"enable-local-file-access": None}
    pdf = pdfkit.from_string(html, False, configuration=config, options=options)
    
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=dashboard_summary.pdf"
    return response
