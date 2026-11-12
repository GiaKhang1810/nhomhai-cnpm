from __future__ import annotations

from flask import Flask, jsonify, redirect, request, session, url_for

from source.configs.settings import Config
from source.database.connection import close_db_connection


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    app.teardown_appcontext(close_db_connection)

    from source.web.routes.accounts import accounts_bp
    from source.web.routes.admin import admin_bp
    from source.web.routes.auth import auth_bp
    from source.web.routes.books import books_bp
    from source.web.routes.borrowing import borrowing_bp
    from source.web.routes.fines import fines_bp
    from source.web.routes.librarian import librarian_bp
    from source.web.routes.profile import profile_bp
    from source.web.routes.readers import readers_bp
    from source.web.routes.reports import reports_bp
    from source.web.routes.returns import returns_bp

    for blueprint in (
        auth_bp, accounts_bp, admin_bp, books_bp, borrowing_bp, fines_bp,
        librarian_bp, profile_bp, readers_bp, reports_bp, returns_bp,
    ):
        app.register_blueprint(blueprint)

    @app.get("/")
    def index():
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        destinations = {
            "READER": "profile.dashboard",
            "LIBRARIAN": "librarian.workspace",
            "ADMIN": "admin.dashboard",
        }
        endpoint = destinations.get(session.get("role"))
        return redirect(url_for(endpoint)) if endpoint else redirect(url_for("auth.logout"))

    @app.get("/health")
    def health_check():
        return jsonify({"status": "ok"})

    @app.errorhandler(401)
    def unauthorized(_error):
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"success": False, "message": "Bạn cần đăng nhập để thực hiện thao tác này."}), 401
        return redirect(url_for("auth.login"))

    @app.errorhandler(403)
    def forbidden(_error):
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"success": False, "message": "Bạn không có quyền thực hiện thao tác này."}), 403
        return "Bạn không có quyền truy cập chức năng này.", 403

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"success": False, "message": "Không tìm thấy tài nguyên."}), 404
        return "Không tìm thấy trang được yêu cầu.", 404

    @app.errorhandler(500)
    def internal_error(_error):
        app.logger.exception("Unhandled application error")
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"success": False, "message": "Lỗi hệ thống. Vui lòng thử lại sau."}), 500
        return "Đã xảy ra lỗi hệ thống.", 500

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="127.0.0.1", port=5000, debug=False)
