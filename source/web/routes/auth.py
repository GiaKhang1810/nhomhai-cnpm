from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from source.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
auth_service = AuthService()
ROLE_MAP = {"reader": "READER", "librarian": "LIBRARIAN", "admin": "ADMIN"}
DESTINATIONS = {
    "READER": "/profile/dashboard",
    "LIBRARIAN": "/librarian/workspace",
    "ADMIN": "/admin/dashboard",
}


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        target = DESTINATIONS.get(session.get("role"), "/auth/login")
        if request.is_json or request.accept_mimetypes.best == "application/json":
            return jsonify({"success": True, "redirect_url": target})
        return redirect(target)

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", ""))
        selected_role = ROLE_MAP.get(str(data.get("role", "")).lower())
        is_api = request.is_json or request.accept_mimetypes.best == "application/json"

        if not username or not password or not selected_role:
            message = "Vui lòng nhập tài khoản, mật khẩu và chọn đúng vai trò."
            if is_api:
                return jsonify({"success": False, "message": message}), 400
            flash(message, "danger")
            return render_template("auth/login.html"), 400

        user = auth_service.authenticate(username, password, selected_role)
        if user:
            session.clear()
            session.permanent = bool(data.get("rememberMe", False))
            session["user_id"] = user.user_id
            session["username"] = user.username
            session["role"] = user.role
            target = DESTINATIONS[user.role]
            if is_api:
                return jsonify({
                    "success": True,
                    "message": "Đăng nhập thành công!",
                    "redirect_url": target,
                    "data": {"username": user.username, "role": user.role},
                })
            flash("Đăng nhập thành công!", "success")
            return redirect(target)

        message = "Thông tin đăng nhập không chính xác hoặc vai trò không khớp với tài khoản."
        if is_api:
            return jsonify({"success": False, "message": message}), 401
        flash(message, "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    if request.is_json or request.accept_mimetypes.best == "application/json":
        return jsonify({"success": True, "message": "Đã đăng xuất thành công."})
    flash("Bạn đã đăng xuất khỏi hệ thống.", "info")
    return redirect(url_for("auth.login"))
