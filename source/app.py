from flask import Flask
from source.configs.settings import Config
from source.database.connection import close_db_connection

def create_app(config_class=Config) -> Flask:
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config_class)
    
    app.secret_key = config_class.SECRET_KEY

    app.teardown_appcontext(close_db_connection)

    from source.web.routes.auth import auth_bp
    from source.web.routes.auth import auth_bp
    from source.web.routes.borrowing import borrowing_bp
    from source.web.routes.returns import returns_bp
    from source.web.routes.books import books_bp
    from source.web.routes.readers import readers_bp
    from source.web.routes.reports import reports_bp
    from source.web.routes.accounts import accounts_bp
    from source.web.routes.profile import profile_bp
    from source.web.routes.librarian import librarian_bp
    from source.web.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(borrowing_bp)
    app.register_blueprint(returns_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(readers_bp)
    app.register_blueprint(reports_bp)  
    app.register_blueprint(accounts_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(librarian_bp)
    app.register_blueprint(admin_bp)

    @app.route('/health')
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)