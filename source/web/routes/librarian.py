from flask import Blueprint, render_template, session

from source.core.decorators import login_required, role_required
from source.database.connection import get_db_connection
from source.repositories.report_repository import ReportRepository

librarian_bp = Blueprint("librarian", __name__, url_prefix="/librarian")
report_repo = ReportRepository()


@librarian_bp.get("/workspace")
@login_required
@role_required("LIBRARIAN")
def workspace():
    metrics = report_repo.get_dashboard_metrics()
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT COUNT(*) AS due_today FROM borrowing_details bd
               JOIN borrowing_records br ON br.loan_id=bd.loan_id
               WHERE bd.return_date IS NULL AND br.due_date=CURDATE()"""
        )
        due_today = int(cursor.fetchone()["due_today"])
        transactions = report_repo.get_recent_transactions(12)
    finally:
        cursor.close()

    formatted = []
    for row in transactions:
        status = row["status"]
        formatted.append({
            "loan_id": row["loan_id"],
            "reader": row["reader"],
            "book": row["book"],
            "borrow_date": row["borrow_date"].strftime("%d/%m/%Y") if row["borrow_date"] else "",
            "due_date": row["due_date"].strftime("%d/%m/%Y") if row["due_date"] else "",
            "status": {"BORROWED": "Đang mượn", "RETURNED": "Đã trả", "OVERDUE": "Quá hạn"}.get(status, status),
            "status_color": {"BORROWED": "bg-amber-50 text-amber-600", "RETURNED": "bg-emerald-50 text-emerald-600", "OVERDUE": "bg-red-50 text-red-600"}.get(status, "bg-slate-100 text-slate-600"),
            "action": "Chi tiết",
        })
    stats = {
        "available_copies": metrics["available_copies"],
        "active_loans": metrics["currently_borrowed"],
        "due_today": due_today,
        "overdue_books": metrics["overdue_loans"],
    }
    return render_template("librarian/workspace.html", username=session.get("username", "Thủ thư"), stats=stats, transactions=formatted)


@librarian_bp.get("/books")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def books_page():
    return render_template("librarian/books.html", username=session.get("username", "Thủ thư"), role=session.get("role"))


@librarian_bp.get("/readers")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def readers_page():
    return render_template("librarian/readers.html", username=session.get("username", "Thủ thư"), role=session.get("role"))


@librarian_bp.get("/borrow")
@login_required
@role_required("LIBRARIAN")
def borrow_page():
    return render_template("librarian/borrow.html", username=session.get("username", "Thủ thư"))


@librarian_bp.get("/returns")
@login_required
@role_required("LIBRARIAN")
def returns_page():
    return render_template("librarian/returns.html", username=session.get("username", "Thủ thư"))


@librarian_bp.get("/fines")
@login_required
@role_required("LIBRARIAN")
def fines_page():
    return render_template("librarian/fines.html", username=session.get("username", "Thủ thư"))
