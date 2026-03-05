import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'backend', 'app', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'backend', 'app', 'static')
    )

    # Config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///dev.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    # Health check
    @app.route('/health')
    def health():
        return {"status": "ok"}, 200

    # Register blueprints
    with app.app_context():
        from backend.app.routes.pages import pages_bp
        from backend.app.routes.auth import auth_bp
        from backend.app.routes.admin import admin_bp
        from backend.app.routes.affiliate import affiliate_bp
        from backend.app.routes.client import client_bp
        from backend.app.routes.tracking import tracking_bp

        app.register_blueprint(pages_bp)
        app.register_blueprint(auth_bp,      url_prefix='/api/auth')
        app.register_blueprint(admin_bp,     url_prefix='/api/admin')
        app.register_blueprint(affiliate_bp, url_prefix='/api/affiliate')
        app.register_blueprint(client_bp,    url_prefix='/api/client')
        app.register_blueprint(tracking_bp,  url_prefix='/api/tracking')

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
