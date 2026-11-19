from flask import Blueprint, jsonify, request, session

from source.core.decorators import login_required, role_required
from source.domain.entities.administrator import Administrator
from source.services.account_service import AccountService

accounts_bp = Blueprint("accounts", __name__, url_prefix="/api/accounts")
account_service = AccountService()


def _administrator() -> Administrator:
    return Administrator(admin_id=int(session["user_id"]))


@accounts_bp.get("/")
@login_required
@role_required("ADMIN")
def list_staff():
    response = jsonify({"success": True, "data": _administrator().manage_staff_accounts(account_service, "list")})
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@accounts_bp.post("/")
@login_required
@role_required("ADMIN")
def create_staff():
    data = request.get_json(silent=True) or {}
    success, message = _administrator().manage_staff_accounts(account_service, "create", data)
    response = jsonify({"success": success, "message": message})
    response.status_code = 201 if success else 400
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@accounts_bp.put("/<int:user_id>")
@login_required
@role_required("ADMIN")
def update_staff(user_id: int):
    data = request.get_json(silent=True) or {}
    if user_id == session.get("user_id") and data.get("role"):
        return jsonify({"success": False, "message": "Không thể tự thay đổi vai trò tài khoản đang sử dụng."}), 400
    success, message = _administrator().manage_staff_accounts(account_service, "update", user_id, data)
    response = jsonify({"success": success, "message": message})
    response.status_code = 200 if success else 400
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@accounts_bp.patch("/<int:user_id>/deactivate")
@login_required
@role_required("ADMIN")
def deactivate_staff(user_id: int):
    success, message = _administrator().manage_staff_accounts(account_service, "deactivate", user_id, int(session["user_id"]))
    return jsonify({"success": success, "message": message}), 200 if success else 400


@accounts_bp.patch("/<int:user_id>/activate")
@login_required
@role_required("ADMIN")
def activate_staff(user_id: int):
    success, message = _administrator().manage_staff_accounts(account_service, "activate", user_id)
    response = jsonify({"success": success, "message": message})
    response.status_code = 200 if success else 400
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@accounts_bp.delete("/<int:user_id>")
@login_required
@role_required("ADMIN")
def delete_staff(user_id: int):
    success, message = _administrator().manage_staff_accounts(account_service, "delete", user_id, int(session["user_id"]))
    response = jsonify({"success": success, "message": message})
    response.status_code = 200 if success else 400
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response
