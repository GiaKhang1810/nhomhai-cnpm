from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from source.services.borrowing_service import BorrowingService
from source.core.decorators import login_required, role_required

borrowing_bp = Blueprint('borrowing', __name__, url_prefix='/borrowing')
borrowing_service = BorrowingService()

@borrowing_bp.route('/workspace', methods=['GET'])
@login_required
@role_required('LIBRARIAN')
def workspace():
    return render_template('librarian/workspace.html')

@borrowing_bp.route('/create', methods=['POST'])
@login_required
@role_required('LIBRARIAN')
def create_loan():
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Dữ liệu không hợp lệ."}), 400

    reader_id = data.get('reader_id')
    copy_ids = data.get('copy_ids', []) 

    if not reader_id or not copy_ids:
        return jsonify({"success": False, "message": "Vui lòng cung cấp mã độc giả và chọn sách."}), 400

    success, message = borrowing_service.process_borrowing(reader_id, copy_ids)

    status_code = 200 if success else 400
    return jsonify({"success": success, "message": message}), status_code