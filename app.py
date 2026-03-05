import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify
from backend.database.db import db, migrate
from backend.config import config

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'production')

    app = Flask(
        __name__,
        template_folder=os.path.join('backend', 'app', 'templates'),
        static_folder=os.path.join('backend', 'app', 'static')
    )
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints directly — no auto-discovery
    from backend.app.routes.pages import pages_bp
    from backend.app.routes.auth import auth_bp
    from backend.app.routes.admin import admin_bp
    from backend.app.routes.affiliate import affiliate_bp
    from backend.app.routes.client import client_bp
    from backend.app.routes.tracking import tracking_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp,       url_prefix='/api/auth')
    app.register_blueprint(admin_bp,      url_prefix='/api/admin')
    app.register_blueprint(affiliate_bp,  url_prefix='/api/affiliate')
    app.register_blueprint(client_bp,     url_prefix='/api/client')
    app.register_blueprint(tracking_bp,   url_prefix='/api/tracking')

    @app.route('/health')
    def health_check():
        return jsonify({"status": "ok"}), 200

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
