import os
from dotenv import load_dotenv
from flask import Flask
from backend.database.db import db, migrate
from backend.config import config

# Load environment variables from .env file at the beginning
load_dotenv()

def create_app(config_name=None):
    """Application factory for the backend service."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # We specify the template and static folders to ensure Flask finds them.
    # The paths are relative to the 'app' package directory.
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Import and register blueprints
    # This is where the routes are added to the application
    from .routes.pages import pages_bp
    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    from .routes.affiliate import affiliate_bp
    from .routes.client import client_bp
    from .routes.demo import demo_bp
    from .routes.tracking import tracking_bp
    
    # Register page routes (like /, /signup, /login)
    app.register_blueprint(pages_bp)
    
    # Register API routes with appropriate prefixes
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(affiliate_bp, url_prefix='/api/affiliate')
    app.register_blueprint(client_bp, url_prefix='/api/client')
    app.register_blueprint(demo_bp, url_prefix='/api/demo')
    app.register_blueprint(tracking_bp, url_prefix='/api/tracking')

    # A simple route to confirm the app is running
    @app.route('/health')
    def health_check():
        return "OK", 200

    return app

