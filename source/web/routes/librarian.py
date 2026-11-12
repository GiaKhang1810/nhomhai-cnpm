from datetime import date

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


@librarian_bp.get("/loans")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def loans_page():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT brq.request_id, brq.reader_id, r.full_name, brq.requested_at,
                      GROUP_CONCAT(CONCAT(b.title, ' × ', bri.quantity) ORDER BY b.title SEPARATOR ', ') AS requested_books
               FROM borrow_requests brq
               JOIN readers r ON r.reader_id=brq.reader_id
               JOIN borrow_request_items bri ON bri.request_id=brq.request_id
               JOIN books b ON b.book_code=bri.book_code
               WHERE brq.status='PENDING'
               GROUP BY brq.request_id, brq.reader_id, r.full_name, brq.requested_at
               ORDER BY brq.requested_at ASC"""
        )
        pending_borrow_requests = cursor.fetchall()
        cursor.execute(
            """SELECT rr.return_request_id, rr.reader_id, r.full_name, rr.requested_at,
                      bd.detail_id, bd.copy_id, br.loan_id, br.due_date, b.title
               FROM return_requests rr
               JOIN readers r ON r.reader_id=rr.reader_id
               JOIN borrowing_details bd ON bd.detail_id=rr.detail_id
               JOIN borrowing_records br ON br.loan_id=bd.loan_id
               JOIN book_copies bc ON bc.copy_id=bd.copy_id
               JOIN books b ON b.book_code=bc.book_code
               WHERE rr.status='PENDING' AND bd.return_date IS NULL
               ORDER BY rr.requested_at ASC"""
        )
        pending_return_requests = cursor.fetchall()
        cursor.execute(
            """SELECT br.loan_id, br.reader_id, r.full_name, br.borrow_date, br.due_date, br.status,
                      COUNT(bd.detail_id) AS total_copies,
                      SUM(CASE WHEN bd.return_date IS NULL THEN 1 ELSE 0 END) AS unreturned_copies,
                      GROUP_CONCAT(b.title ORDER BY b.title SEPARATOR ', ') AS books
               FROM borrowing_records br
               JOIN readers r ON r.reader_id=br.reader_id
               JOIN borrowing_details bd ON bd.loan_id=br.loan_id
               JOIN book_copies bc ON bc.copy_id=bd.copy_id
               JOIN books b ON b.book_code=bc.book_code
               GROUP BY br.loan_id, br.reader_id, r.full_name, br.borrow_date, br.due_date, br.status
               ORDER BY br.borrow_date DESC, br.loan_id DESC LIMIT 200"""
        )
        loan_records = cursor.fetchall()
    finally:
        cursor.close()
    return render_template(
        "librarian/loans.html", username=session.get("username", "Thủ thư"),
        pending_borrow_requests=pending_borrow_requests,
        pending_return_requests=pending_return_requests,
        loan_records=loan_records, today=date.today(),
    )


@librarian_bp.get("/borrow")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def borrow_page():
    return render_template("librarian/borrow.html", username=session.get("username", "Thủ thư"))


@librarian_bp.get("/returns")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def returns_page():
    return render_template("librarian/returns.html", username=session.get("username", "Thủ thư"))


@librarian_bp.get("/fines")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def fines_page():
    return render_template("librarian/fines.html", username=session.get("username", "Thủ thư"))
