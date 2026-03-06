"""
API Routes
Blueprint initialization for all route modules
"""

from flask import Blueprint

# Import blueprints from route modules
from backend.app.routes.auth import auth_bp
from backend.app.routes.tracking import tracking_bp, ppc_bp
from backend.app.routes.affiliate import affiliate_bp
from backend.app.routes.client import client_bp
from backend.app.routes.admin import admin_bp
from backend.app.routes.pages import pages_bp

__all__ = ['auth_bp', 'tracking_bp', 'ppc_bp', 'affiliate_bp', 'client_bp', 'admin_bp', 'pages_bp']

