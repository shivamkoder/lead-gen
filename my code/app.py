import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from backend.app.extensions import db, migrate, login_manager, cors, socketio

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'backend', 'app', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'backend', 'app', 'static')
    )

    # Config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    db_url = os.getenv('DATABASE_URL', 'sqlite:///dev.db')
    # SQLAlchemy requires postgresql:// not postgres://
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    socketio.init_app(app)

    # Register blueprints
    from backend.app.routes.pages import pages_bp
    from backend.app.routes.auth import auth_bp
    from backend.app.routes.admin import admin_bp
    from backend.app.routes.affiliate import affiliate_bp
    from backend.app.routes.client import client_bp
    from backend.app.routes.tracking import tracking_bp
    from backend.app.routes.demo import demo_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp,      url_prefix='/api/auth')
    app.register_blueprint(admin_bp,     url_prefix='/api/admin')
    app.register_blueprint(affiliate_bp, url_prefix='/api/affiliate')
    app.register_blueprint(client_bp,    url_prefix='/api/client')
    app.register_blueprint(tracking_bp)
    app.register_blueprint(demo_bp,      url_prefix='/api/demo')

    @app.route('/health')
    def health():
        return {"status": "ok"}, 200

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
