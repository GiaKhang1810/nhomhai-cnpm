from flask import Blueprint, request, jsonify
from source.services.reader_service import ReaderService
from source.core.decorators import login_required, role_required

readers_bp = Blueprint('readers', __name__, url_prefix='/api/readers')
reader_service = ReaderService()

@readers_bp.route('/search', methods=['GET'])
@login_required
@role_required('LIBRARIAN')
def search():
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        return jsonify({"success": False, "message": "Vui lòng nhập từ khóa tìm kiếm."}), 400
        
    readers = reader_service.search_readers(keyword)
    
    readers_data = [
        {
            "reader_id": r.reader_id,
            "full_name": r.full_name,
            "identity_number": r.identity_number,
            "account_status": r.account_status,
            "card_expiry_date": r.card_expiry_date.isoformat() if r.card_expiry_date else None
        } for r in readers
    ]
    
    return jsonify({
        "success": True,
        "data": readers_data
    })

@readers_bp.route('/', methods=['POST'])
@login_required
@role_required('LIBRARIAN')
def create_reader():
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Dữ liệu không hợp lệ."}), 400

    success, message = reader_service.create_new_reader(data)
    
    status_code = 201 if success else 400
    return jsonify({"success": success, "message": message}), status_code