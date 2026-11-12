from flask import Blueprint, jsonify, request, render_template, session

from source.core.decorators import login_required, role_required
from source.database.connection import get_db_connection
from source.services.borrowing_service import BorrowingService
from source.repositories.request_repository import RequestRepository

borrowing_bp = Blueprint("borrowing", __name__, url_prefix="/borrowing")
borrowing_service = BorrowingService()
request_repo = RequestRepository()


@borrowing_bp.get("/workspace")
@login_required
@role_required("LIBRARIAN")
def workspace():
    from flask import session
    return render_template("librarian/workspace.html", username=session.get("username", "Thủ thư"))


@borrowing_bp.post("/create")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def create_loan():
    data = request.get_json(silent=True) or {}
    reader_id = str(data.get("reader_id", "")).strip()
    copy_ids = data.get("copy_ids", [])
    if not isinstance(copy_ids, list):
        return jsonify({"success": False, "message": "Danh sách bản sao không hợp lệ."}), 400
    success, message = borrowing_service.process_borrowing(reader_id, copy_ids)
    return jsonify({"success": success, "message": message}), 201 if success else 400


@borrowing_bp.post("/requests/<string:request_id>/approve")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def approve_borrow_request(request_id: str):
    borrow_request = request_repo.get_pending_borrow_request(request_id)
    if not borrow_request:
        return jsonify({"success": False, "message": "Không tìm thấy yêu cầu mượn."}), 404
    if borrow_request["status"] != "PENDING":
        return jsonify({"success": False, "message": "Yêu cầu này đã được xử lý."}), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    copy_ids = []
    try:
        for item in borrow_request["items"]:
            cursor.execute(
                "SELECT copy_id FROM book_copies WHERE book_code=%s AND status='AVAILABLE' ORDER BY copy_id LIMIT %s",
                (item["book_code"], item["quantity"]),
            )
            copies = cursor.fetchall()
            if len(copies) != int(item["quantity"]):
                return jsonify({"success": False, "message": "Không đủ bản sao khả dụng để duyệt yêu cầu. Hãy kiểm tra tồn kho hoặc từ chối yêu cầu."}), 409
            copy_ids.extend(row["copy_id"] for row in copies)
    finally:
        cursor.close()

    success, message = borrowing_service.process_borrowing(
        borrow_request["reader_id"], copy_ids,
        request_id=request_id, processed_by=int(session["user_id"]),
    )
    return jsonify({"success": success, "message": message}), 201 if success else 400


@borrowing_bp.post("/requests/<string:request_id>/reject")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def reject_borrow_request(request_id: str):
    data = request.get_json(silent=True) or {}
    success, message = request_repo.reject_borrow_request(
        request_id, int(session["user_id"]), str(data.get("note", "")),
    )
    return jsonify({"success": success, "message": message}), 200 if success else 400


@borrowing_bp.get("/lookup/<string:loan_id>")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def lookup_loan(loan_id: str):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT br.loan_id, br.reader_id, r.full_name, br.borrow_date, br.due_date, br.status
               FROM borrowing_records br JOIN readers r ON r.reader_id=br.reader_id
               WHERE br.loan_id=%s""",
            (loan_id,),
        )
        loan = cursor.fetchone()
        if not loan:
            return jsonify({"success": False, "message": "Không tìm thấy phiếu mượn."}), 404
        cursor.execute(
            """SELECT bd.copy_id, b.title, bd.return_date, bc.status
               FROM borrowing_details bd JOIN book_copies bc ON bc.copy_id=bd.copy_id
               JOIN books b ON b.book_code=bc.book_code WHERE bd.loan_id=%s""",
            (loan_id,),
        )
        loan["items"] = cursor.fetchall()
        return jsonify({"success": True, "data": loan})
    finally:
        cursor.close()


@borrowing_bp.get("/lookup")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def lookup_reader_loans():
    reader_id = request.args.get("reader_id", "").strip()
    if not reader_id:
        return jsonify({"success": False, "message": "Vui lòng nhập mã độc giả."}), 400
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT br.loan_id, br.reader_id, r.full_name, br.borrow_date, br.due_date, br.status,
                      SUM(CASE WHEN bd.return_date IS NULL THEN 1 ELSE 0 END) AS unreturned_copies,
                      COUNT(*) AS total_copies
               FROM borrowing_records br
               JOIN readers r ON r.reader_id=br.reader_id
               JOIN borrowing_details bd ON bd.loan_id=br.loan_id
               WHERE br.reader_id=%s
               GROUP BY br.loan_id, br.reader_id, r.full_name, br.borrow_date, br.due_date, br.status
               ORDER BY br.borrow_date DESC, br.loan_id DESC
               LIMIT 100""",
            (reader_id,),
        )
        loans = cursor.fetchall()
        return jsonify({"success": True, "data": loans, "count": len(loans)})
    finally:
        cursor.close()
