from flask import Blueprint, jsonify, request

from source.core.decorators import login_required, role_required
from source.services.reader_service import ReaderService

readers_bp = Blueprint("readers", __name__, url_prefix="/api/readers")
reader_service = ReaderService()


@readers_bp.get("/search")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def search():
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return jsonify({"success": False, "message": "Vui lòng nhập từ khóa tìm kiếm."}), 400
    readers = reader_service.search_readers(keyword)
    return jsonify({
        "success": True,
        "data": [{
            "reader_id": reader.reader_id,
            "full_name": reader.full_name,
            "dob": reader.dob.isoformat() if reader.dob else None,
            "gender": reader.gender,
            "identity_number": reader.identity_number,
            "account_status": reader.account_status,
            "card_expiry_date": reader.card_expiry_date.isoformat() if reader.card_expiry_date else None,
            "phone": reader.phone,
        } for reader in readers],
    })


@readers_bp.post("/")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def create_reader():
    data = request.get_json(silent=True) or {}
    success, message = reader_service.create_new_reader(data)
    return jsonify({"success": success, "message": message}), 201 if success else 400


@readers_bp.put("/<string:reader_id>")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def update_reader(reader_id: str):
    data = request.get_json(silent=True) or {}
    success, message = reader_service.update_reader(reader_id, data)
    return jsonify({"success": success, "message": message}), 200 if success else 400


@readers_bp.patch("/<string:reader_id>/deactivate")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def deactivate_reader(reader_id: str):
    success, message = reader_service.deactivate_reader(reader_id)
    return jsonify({"success": success, "message": message}), 200 if success else 400
