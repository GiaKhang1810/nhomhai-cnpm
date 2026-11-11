from flask import Blueprint, request, jsonify
from source.services.account_service import AccountService
from source.core.decorators import login_required, role_required

accounts_bp = Blueprint('accounts', __name__, url_prefix='/api/accounts')
account_service = AccountService()

@accounts_bp.route('/', methods=['POST'])
@login_required
@role_required('ADMIN')
def create_staff():
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Dữ liệu không hợp lệ"}), 400
        
    success, message = account_service.create_staff_account(data)
    status_code = 201 if success else 400
    return jsonify({"success": success, "message": message}), status_code