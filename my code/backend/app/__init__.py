"""
TechFest Backend Application
Main application factory and initialization
"""

from flask import Flask
from backend.app.config import Config
from backend.app.extensions import db, migrate, login_manager, cors


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    # initialize realtime extension
    from app.extensions import socketio
    socketio.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.tracking import tracking_bp, ppc_bp
    from app.routes.affiliate import affiliate_bp
    from app.routes.client import client_bp
    from app.routes.admin import admin_bp
    from app.routes.demo import demo_bp
    from app.routes.pages import pages_bp
    
    app.register_blueprint(pages_bp)  # Frontend: /, /signup, /login, /dashboard/*
    app.register_blueprint(ppc_bp)  # Public PPC: /t/<campaign_id>?aff=affiliateID
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tracking_bp, url_prefix='/api/tracking')
    app.register_blueprint(affiliate_bp, url_prefix='/api/affiliate')
    app.register_blueprint(client_bp, url_prefix='/api/client')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(demo_bp, url_prefix='/api/demo')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

