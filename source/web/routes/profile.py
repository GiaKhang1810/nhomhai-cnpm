from datetime import date

from flask import Blueprint, jsonify, render_template, request, session

from source.core.decorators import login_required, role_required
from source.database.connection import get_db_connection
from source.repositories.book_repository import BookRepository
from source.repositories.reader_repository import ReaderRepository
from source.repositories.request_repository import RequestRepository

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")
book_repo = BookRepository()
reader_repo = ReaderRepository()
request_repo = RequestRepository()


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


@profile_bp.get("/loans")
@login_required
@role_required("READER")
def loans():
    reader_id = _reader_id()
    active_loans = []
    borrow_requests = []
    if reader_id:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT bd.detail_id, br.loan_id, b.title, b.author, bc.copy_id,
                          br.borrow_date, br.due_date, bd.return_date,
                          rr.return_request_id, rr.status AS return_request_status, rr.staff_note AS return_request_note
                   FROM borrowing_records br
                   JOIN borrowing_details bd ON bd.loan_id=br.loan_id
                   JOIN book_copies bc ON bc.copy_id=bd.copy_id
                   JOIN books b ON b.book_code=bc.book_code
                   LEFT JOIN return_requests rr ON rr.return_request_id = (
                       SELECT rr2.return_request_id FROM return_requests rr2
                       WHERE rr2.detail_id=bd.detail_id
                       ORDER BY rr2.requested_at DESC, rr2.return_request_id DESC LIMIT 1
                   )
                   WHERE br.reader_id=%s AND bd.return_date IS NULL
                   ORDER BY br.due_date, br.borrow_date DESC""",
                (reader_id,),
            )
            active_loans = cursor.fetchall()
            cursor.execute(
                """SELECT brq.request_id, brq.status, brq.requested_at, brq.staff_note,
                          GROUP_CONCAT(CONCAT(b.title, ' × ', bri.quantity) ORDER BY b.title SEPARATOR ', ') AS requested_books
                   FROM borrow_requests brq
                   JOIN borrow_request_items bri ON bri.request_id=brq.request_id
                   JOIN books b ON b.book_code=bri.book_code
                   WHERE brq.reader_id=%s
                   GROUP BY brq.request_id, brq.status, brq.requested_at, brq.staff_note
                   ORDER BY brq.requested_at DESC LIMIT 50""",
                (reader_id,),
            )
            borrow_requests = cursor.fetchall()
        finally:
            cursor.close()
    return render_template(
        "reader/loans.html", username=session.get("username", "Độc giả"),
        active_loans=active_loans, borrow_requests=borrow_requests, today=date.today(),
    )


@profile_bp.post("/api/borrow-requests")
@login_required
@role_required("READER")
def create_borrow_request():
    reader_id = _reader_id()
    if not reader_id:
        return jsonify({"success": False, "message": "Tài khoản chưa có hồ sơ độc giả."}), 404
    data = request.get_json(silent=True) or {}
    book_code = str(data.get("book_code", "")).strip()
    try:
        quantity = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Số lượng yêu cầu không hợp lệ."}), 400
    if not book_code or quantity < 1 or quantity > 5:
        return jsonify({"success": False, "message": "Vui lòng chọn sách và số lượng từ 1 đến 5."}), 400
    try:
        success, message, request_id = request_repo.create_borrow_request(reader_id, book_code, quantity)
    except Exception:
        return jsonify({"success": False, "message": "Không thể gửi yêu cầu mượn do lỗi hệ thống."}), 500
    return jsonify({"success": success, "message": message, "request_id": request_id}), 201 if success else 400


@profile_bp.post("/api/return-requests")
@login_required
@role_required("READER")
def create_return_request():
    reader_id = _reader_id()
    if not reader_id:
        return jsonify({"success": False, "message": "Tài khoản chưa có hồ sơ độc giả."}), 404
    data = request.get_json(silent=True) or {}
    try:
        detail_id = int(data.get("detail_id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Mã chi tiết phiếu mượn không hợp lệ."}), 400
    try:
        success, message, request_id = request_repo.create_return_request(reader_id, detail_id)
    except Exception:
        return jsonify({"success": False, "message": "Không thể gửi yêu cầu trả do lỗi hệ thống."}), 500
    return jsonify({"success": success, "message": message, "request_id": request_id}), 201 if success else 400


@profile_bp.post("/api/borrow-requests/<string:request_id>/cancel")
@login_required
@role_required("READER")
def cancel_borrow_request(request_id: str):
    reader_id = _reader_id()
    if not reader_id:
        return jsonify({"success": False, "message": "Không tìm thấy hồ sơ độc giả."}), 404
    success, message = request_repo.cancel_borrow_request(reader_id, request_id)
    return jsonify({"success": success, "message": message}), 200 if success else 400


@profile_bp.post("/api/return-requests/<string:request_id>/cancel")
@login_required
@role_required("READER")
def cancel_return_request(request_id: str):
    reader_id = _reader_id()
    if not reader_id:
        return jsonify({"success": False, "message": "Không tìm thấy hồ sơ độc giả."}), 404
    success, message = request_repo.cancel_return_request(reader_id, request_id)
    return jsonify({"success": success, "message": message}), 200 if success else 400


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
