"""
Frontend page routes — serve HTML templates (landing, signup, login, dashboards).
"""

from flask import Blueprint, render_template, redirect, url_for

pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
def landing():
    return render_template('landing.html')


@pages_bp.route('/signup')
def signup():
    return render_template('signup.html')


@pages_bp.route('/login')
def login():
    return render_template('login.html')


@pages_bp.route('/dashboard')
def dashboard_root():
    """Redirect to role-specific dashboard; JS will redirect if not logged in."""
    return render_template('dashboard_redirect.html')


@pages_bp.route('/dashboard/client')
def dashboard_client():
    return render_template('client_dashboard.html')


@pages_bp.route('/dashboard/affiliate')
def dashboard_affiliate():
    return render_template('affiliate_dashboard.html')
