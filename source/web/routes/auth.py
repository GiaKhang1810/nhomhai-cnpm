from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from source.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
auth_service = AuthService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        role = session.get('role')
        redirect_map = {
            'READER': '/profile/dashboard',
            'LIBRARIAN': '/borrowing/workspace',
            'ADMIN': '/admin/dashboard'
        }
        target = redirect_map.get(role, '/auth/login')
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({"success": True, "redirect_url": target}), 200
        return redirect(target)

    if request.method == 'POST':
        req_data = request.get_json(silent=True) or request.form
        username = req_data.get('username', '').strip()
        password = req_data.get('password', '')
        
        is_api_request = request.is_json or request.headers.get('Accept') == 'application/json' or request.content_type == 'application/json'

        if not username or not password:
            msg = "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu."
            if is_api_request:
                return jsonify({"success": False, "message": msg}), 400
            flash(msg, "danger")
            return render_template('auth/login.html')

        user = auth_service.authenticate(username, password)

        if user:
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['role'] = user.role

            redirect_map = {
                'READER': '/profile/dashboard',
                'LIBRARIAN': '/borrowing/workspace',
                'ADMIN': '/admin/dashboard'
            }
            redirect_url = redirect_map.get(user.role, '/auth/login')

            if is_api_request:
                return jsonify({
                    "success": True,
                    "message": "Đăng nhập thành công!",
                    "redirect_url": redirect_url,
                    "data": {
                        "username": user.username,
                        "role": user.role
                    }
                }), 200
            
            flash("Đăng nhập thành công!", "success")
            return redirect(redirect_url)
        else:
            msg = "Tên đăng nhập hoặc mật khẩu không chính xác, hoặc tài khoản đã bị khóa."
            if is_api_request:
                return jsonify({"success": False, "message": msg}), 401
            flash(msg, "danger")

    return render_template('auth/login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({"success": True, "message": "Đã đăng xuất thành công."})
    flash("Bạn đã đăng xuất khỏi hệ thống.", "info")
    return redirect(url_for('auth.login'))