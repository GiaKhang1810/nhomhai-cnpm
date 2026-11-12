from flask import Blueprint, jsonify, request

from source.core.decorators import login_required, role_required
from source.services.return_service import ReturnItemRequest, ReturnService

returns_bp = Blueprint("returns", __name__, url_prefix="/returns")
return_service = ReturnService()


@returns_bp.post("/process")
@login_required
@role_required("LIBRARIAN")
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
    success, message, total_charge = return_service.process_returns(loan_id, items)
    return jsonify({"success": success, "message": message, "total_charge": str(total_charge)}), 200 if success else 400
