from flask import Blueprint, jsonify, render_template, request, session

from source.core.decorators import login_required, role_required
from source.repositories.report_repository import ReportRepository

reports_bp = Blueprint("reports", __name__, url_prefix="/admin/reports")
report_repo = ReportRepository()


@reports_bp.get("/dashboard")
@login_required
@role_required("ADMIN", "LIBRARIAN")
def dashboard_data():
    return jsonify({"success": True, "data": report_repo.get_dashboard_metrics()})


@reports_bp.get("/activity")
@login_required
@role_required("ADMIN", "LIBRARIAN")
def activity_data():
    try:
        days = int(request.args.get("days", "7"))
    except ValueError:
        return jsonify({"success": False, "message": "Số ngày không hợp lệ."}), 400
    return jsonify({"success": True, "data": report_repo.get_activity_stats(days)})


@reports_bp.get("/categories")
@login_required
@role_required("ADMIN", "LIBRARIAN")
def category_data():
    return jsonify({"success": True, "data": report_repo.get_category_distribution()})


@reports_bp.get("/")
@login_required
@role_required("ADMIN", "LIBRARIAN")
def reports_page():
    return render_template("reports/dashboard.html", username=session.get("username", "Nhân viên"), role=session.get("role"))
