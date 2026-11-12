from flask import Blueprint, jsonify, request, session

from source.core.decorators import login_required, role_required
from source.services.account_service import AccountService

accounts_bp = Blueprint("accounts", __name__, url_prefix="/api/accounts")
account_service = AccountService()


@accounts_bp.get("/")
@login_required
@role_required("ADMIN")
def list_staff():
    return jsonify({"success": True, "data": account_service.list_staff_accounts()})


@accounts_bp.post("/")
@login_required
@role_required("ADMIN")
def create_staff():
    data = request.get_json(silent=True) or {}
    success, message = account_service.create_staff_account(data)
    return jsonify({"success": success, "message": message}), 201 if success else 400


@accounts_bp.put("/<int:user_id>")
@login_required
@role_required("ADMIN")
def update_staff(user_id: int):
    data = request.get_json(silent=True) or {}
    if user_id == session.get("user_id") and data.get("role"):
        return jsonify({"success": False, "message": "Không thể tự thay đổi vai trò tài khoản đang sử dụng."}), 400
    success, message = account_service.update_staff_account(user_id, data)
    return jsonify({"success": success, "message": message}), 200 if success else 400


@accounts_bp.patch("/<int:user_id>/deactivate")
@login_required
@role_required("ADMIN")
def deactivate_staff(user_id: int):
    success, message = account_service.deactivate_staff_account(user_id, int(session["user_id"]))
    return jsonify({"success": success, "message": message}), 200 if success else 400
