from flask import Blueprint, jsonify, render_template, session

from source.core.decorators import login_required, role_required
from source.database.connection import get_db_connection
from source.repositories.book_repository import BookRepository
from source.repositories.reader_repository import ReaderRepository

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")
book_repo = BookRepository()
reader_repo = ReaderRepository()


def _reader_id():
    reader = reader_repo.get_by_user_id(int(session["user_id"]))
    return reader.reader_id if reader else None


@profile_bp.get("/dashboard")
@login_required
@role_required("READER")
def dashboard():
    reader = reader_repo.get_by_user_id(int(session["user_id"]))
    stats = {"borrowed_count": 0, "due_soon_count": 0}
    history = []
    profile = None
    if reader:
        profile = reader
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT COUNT(*) AS borrowed_count,
                          SUM(CASE WHEN br.due_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 3 DAY) THEN 1 ELSE 0 END) AS due_soon_count
                   FROM borrowing_records br JOIN borrowing_details bd ON bd.loan_id=br.loan_id
                   WHERE br.reader_id=%s AND bd.return_date IS NULL""",
                (reader.reader_id,),
            )
            result = cursor.fetchone() or {}
            stats["borrowed_count"] = int(result.get("borrowed_count") or 0)
            stats["due_soon_count"] = int(result.get("due_soon_count") or 0)
            cursor.execute(
                """SELECT br.loan_id, b.title, b.author, br.borrow_date, br.due_date,
                          bd.return_date, br.status
                   FROM borrowing_records br JOIN borrowing_details bd ON bd.loan_id=br.loan_id
                   JOIN book_copies bc ON bc.copy_id=bd.copy_id JOIN books b ON b.book_code=bc.book_code
                   WHERE br.reader_id=%s ORDER BY br.borrow_date DESC LIMIT 5""",
                (reader.reader_id,),
            )
            history = cursor.fetchall()
        finally:
            cursor.close()

    recommended_books = book_repo.search_books("")[:4]
    return render_template(
        "reader/dashboard.html",
        username=session.get("username", "Độc giả"),
        stats=stats,
        recommended_books=recommended_books,
        history=history,
        reader=profile,
    )


@profile_bp.get("/history")
@login_required
@role_required("READER")
def borrowing_history():
    reader_id = _reader_id()
    records = []
    if reader_id:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT br.loan_id, b.title, b.author, br.borrow_date, br.due_date,
                          bd.return_date, bd.overdue_fine, bd.compensation,
                          CASE WHEN bd.return_date IS NOT NULL THEN 'RETURNED'
                               WHEN br.due_date < CURDATE() THEN 'OVERDUE'
                               ELSE 'BORROWED' END AS status
                   FROM borrowing_records br JOIN borrowing_details bd ON bd.loan_id=br.loan_id
                   JOIN book_copies bc ON bc.copy_id=bd.copy_id JOIN books b ON b.book_code=bc.book_code
                   WHERE br.reader_id=%s ORDER BY br.borrow_date DESC, br.loan_id DESC""",
                (reader_id,),
            )
            records = cursor.fetchall()
        finally:
            cursor.close()
    return render_template("reader/history.html", username=session.get("username", "Độc giả"), records=records)


@profile_bp.get("/api/me")
@login_required
@role_required("READER")
def personal_profile():
    reader = reader_repo.get_by_user_id(int(session["user_id"]))
    if not reader:
        return jsonify({"success": False, "message": "Không tìm thấy hồ sơ độc giả."}), 404
    return jsonify({"success": True, "data": {
        "reader_id": reader.reader_id,
        "full_name": reader.full_name,
        "dob": reader.dob.isoformat() if reader.dob else None,
        "gender": reader.gender,
        "identity_number": reader.identity_number,
        "phone": reader.phone,
        "card_issue_date": reader.card_issue_date.isoformat(),
        "card_expiry_date": reader.card_expiry_date.isoformat(),
        "account_status": reader.account_status,
    }})


@profile_bp.get("/api/history")
@login_required
@role_required("READER")
def personal_history_api():
    reader_id = _reader_id()
    if not reader_id:
        return jsonify({"success": True, "data": []})
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT br.loan_id, b.title, bd.copy_id, br.borrow_date, br.due_date,
                      bd.return_date, bd.overdue_fine, bd.compensation
               FROM borrowing_records br JOIN borrowing_details bd ON bd.loan_id=br.loan_id
               JOIN book_copies bc ON bc.copy_id=bd.copy_id JOIN books b ON b.book_code=bc.book_code
               WHERE br.reader_id=%s ORDER BY br.borrow_date DESC""",
            (reader_id,),
        )
        rows = cursor.fetchall()
        return jsonify({"success": True, "data": rows})
    finally:
        cursor.close()


@profile_bp.get("/catalogue")
@login_required
@role_required("READER")
def catalogue():
    books = book_repo.search_books("")
    return render_template("reader/catalogue.html", username=session.get("username", "Độc giả"), books=books)
