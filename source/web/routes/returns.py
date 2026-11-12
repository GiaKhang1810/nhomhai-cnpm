from flask import Blueprint, jsonify, request, session

from source.core.decorators import login_required, role_required
from source.services.return_service import ReturnItemRequest, ReturnService
from source.repositories.request_repository import RequestRepository

returns_bp = Blueprint("returns", __name__, url_prefix="/returns")
return_service = ReturnService()
request_repo = RequestRepository()


@returns_bp.post("/process")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def process_return():
    data = request.get_json(silent=True) or {}
    loan_id = str(data.get("loan_id", "")).strip()
    items_data = data.get("items", [])
    if not loan_id or not isinstance(items_data, list) or not items_data:
        return jsonify({"success": False, "message": "Thiếu mã phiếu mượn hoặc danh sách bản sao trả."}), 400
    try:
        items = [ReturnItemRequest(copy_id=str(item["copy_id"]), condition=str(item.get("condition", "NORMAL")).upper()) for item in items_data]
    except (KeyError, TypeError):
        return jsonify({"success": False, "message": "Dữ liệu sách trả không đúng định dạng."}), 400
    success, message, total_charge = return_service.process_returns(loan_id, items, processed_by=int(session["user_id"]))
    return jsonify({"success": success, "message": message, "total_charge": str(total_charge)}), 200 if success else 400


@returns_bp.post("/requests/<string:request_id>/reject")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def reject_return_request(request_id: str):
    data = request.get_json(silent=True) or {}
    success, message = request_repo.reject_return_request(
        request_id, int(session["user_id"]), str(data.get("note", "")),
    )
    return jsonify({"success": success, "message": message}), 200 if success else 400
