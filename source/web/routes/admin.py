from flask import Blueprint, render_template, session

from source.core.decorators import login_required, role_required
from source.repositories.report_repository import ReportRepository

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
report_repo = ReportRepository()


@admin_bp.get("/dashboard")
@login_required
@role_required("ADMIN")
def dashboard():
    metrics_data = report_repo.get_dashboard_metrics()
    metrics = {
        "total_titles": f"{metrics_data['total_titles']:,}",
        "title_trend": f"{metrics_data['total_copies']:,} bản sao trong kho",
        "active_readers": f"{metrics_data['active_readers']:,}",
        "reader_trend": f"{metrics_data['new_readers_30_days']:,} độc giả mới trong 30 ngày",
        "active_loans": f"{metrics_data['currently_borrowed']:,}",
        "loan_note": "Bản sao đang được mượn",
        "overdue_books": f"{metrics_data['overdue_loans']:,}",
        "overdue_note": "Bản sao cần xử lý",
    }
    transactions = report_repo.get_recent_transactions(8)
    formatted = []
    for row in transactions:
        status = row["status"]
        formatted.append({
            "loan_id": row["loan_id"],
            "reader": row["reader"],
            "book": row["book"],
            "date": row["borrow_date"].strftime("%d/%m/%Y") if row["borrow_date"] else "",
            "due_date": row["due_date"].strftime("%d/%m/%Y") if row["due_date"] else "",
            "status": {"BORROWED": "Đang mượn", "RETURNED": "Đã trả", "OVERDUE": "Quá hạn"}.get(status, status),
            "status_color": {"BORROWED": "bg-amber-50 text-amber-600", "RETURNED": "bg-slate-100 text-slate-600", "OVERDUE": "bg-red-50 text-red-600"}.get(status, "bg-slate-100 text-slate-600"),
        })
    return render_template(
        "admin/dashboard.html",
        username=session.get("username", "Quản trị viên"),
        metrics=metrics,
        recent_transactions=formatted,
    )


@admin_bp.get("/accounts")
@login_required
@role_required("ADMIN")
def accounts_page():
    return render_template("admin/accounts.html", username=session.get("username", "Quản trị viên"))
