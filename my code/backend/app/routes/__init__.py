"""
API Routes
Blueprint initialization for all route modules
"""

from flask import Blueprint

# Import blueprints from route modules
from app.routes.auth import auth_bp
from app.routes.tracking import tracking_bp, ppc_bp
from app.routes.affiliate import affiliate_bp
from app.routes.client import client_bp
from app.routes.admin import admin_bp
from app.routes.pages import pages_bp

__all__ = ['auth_bp', 'tracking_bp', 'ppc_bp', 'affiliate_bp', 'client_bp', 'admin_bp', 'pages_bp']
