from flask import Blueprint, request, jsonify
from source.services.return_service import ReturnService, ReturnItemRequest
from source.core.decorators import login_required, role_required

returns_bp = Blueprint('returns', __name__, url_prefix='/returns')
return_service = ReturnService()

@returns_bp.route('/process', methods=['POST'])
@login_required
@role_required('LIBRARIAN')
def process_return():
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Dữ liệu không hợp lệ."}), 400

    loan_id = data.get('loan_id')
    items_data = data.get('items', []) 

    if not loan_id or not items_data:
        return jsonify({"success": False, "message": "Thiếu mã phiếu mượn hoặc danh sách sách trả."}), 400

    try:
        returned_items = [
            ReturnItemRequest(
                copy_id=item['copy_id'], 
                condition=item.get('condition', 'NORMAL')
            ) for item in items_data
        ]
    except KeyError:
        return jsonify({"success": False, "message": "Dữ liệu sách trả không đúng định dạng."}), 400

    success, message, total_charge = return_service.process_returns(loan_id, returned_items)

    status_code = 200 if success else 400
    return jsonify({
        "success": success, 
        "message": message,
        "total_charge": total_charge
    }), status_code