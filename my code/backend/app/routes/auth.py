"""
Authentication Routes
Register, login, logout, profile, password reset, and email verification.

Email verification flow:
  POST /api/auth/register            → creates user + returns _dev_verify_url in dev
  GET|POST /api/auth/verify/<token>  → marks user.is_verified = True
  POST /api/auth/verify/resend       → resends token (requires login)

Password reset flow:
  POST /api/auth/password/reset           → returns _dev_reset_url in dev
  POST /api/auth/password/reset/<token>   → sets new password
"""

import os
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.extensions import db
from app.models import User
import re

auth_bp = Blueprint('auth', __name__)

IS_PRODUCTION = os.getenv('FLASK_ENV') == 'production'

# ── Helpers ───────────────────────────────────────────────────────────────────

def validate_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, None

def _make_token(payload: str, salt: str) -> str:
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(payload, salt=salt)

def _verify_token(token: str, salt: str, max_age: int):
    """Returns (payload, None) or (None, error_message)."""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        return s.loads(token, salt=salt, max_age=max_age), None
    except SignatureExpired:
        return None, 'Link has expired. Please request a new one.'
    except BadSignature:
        return None, 'Invalid or tampered link.'

_RESET_SALT  = 'password-reset-salt'
_VERIFY_SALT = 'email-verification-salt'

# ── Register ──────────────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    for field in ('email', 'username', 'password'):
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 400
    is_valid, err = validate_password(data['password'])
    if not is_valid:
        return jsonify({'error': err}), 400

    user = User(
        email=data['email'],
        username=data['username'],
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        role=data.get('role', 'user'),
    )
    # Set is_verified=False if the model supports it; gracefully skip if not
    if hasattr(user, 'is_verified'):
        user.is_verified = False
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    login_user(user)  # log in immediately — verified check is soft

    # Email verification token
    token = _make_token(user.email, _VERIFY_SALT)
    verify_url = f"{request.host_url.rstrip('/')}/api/auth/verify/{token}"

    # TODO (production): send verify_url to user.email via your email provider
    # e.g. send_email(to=user.email, subject="Verify your email", body=verify_url)

    resp = {
        'message': 'Account created. Please verify your email address.',
        'user': {
            'id': user.id, 'email': user.email,
            'username': user.username, 'role': user.role,
            'is_verified': getattr(user, 'is_verified', True),
        }
    }
    if not IS_PRODUCTION:
        resp['_dev_verify_url'] = verify_url   # remove in production

    return jsonify(resp), 201


# ── Email Verification ────────────────────────────────────────────────────────

@auth_bp.route('/verify/<token>', methods=['GET', 'POST'])
def verify_email(token):
    """Confirm email address from the link in the verification email."""
    email, error = _verify_token(token, _VERIFY_SALT, max_age=86400)  # 24 h
    if error:
        return jsonify({'error': error}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    if getattr(user, 'is_verified', True):
        return jsonify({'message': 'Email already verified.'}), 200

    user.is_verified = True
    db.session.commit()
    return jsonify({'message': 'Email verified successfully!'}), 200


@auth_bp.route('/verify/resend', methods=['POST'])
@login_required
def resend_verification():
    """Resend verification email to the logged-in user."""
    if getattr(current_user, 'is_verified', True):
        return jsonify({'message': 'Your email is already verified.'}), 200

    token = _make_token(current_user.email, _VERIFY_SALT)
    verify_url = f"{request.host_url.rstrip('/')}/api/auth/verify/{token}"

    # TODO (production): send verify_url via email

    resp = {'message': 'Verification email resent.'}
    if not IS_PRODUCTION:
        resp['_dev_verify_url'] = verify_url

    return jsonify(resp), 200


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403

    login_user(user, remember=data.get('remember', False))
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id, 'email': user.email,
            'username': user.username, 'role': user.role,
            'is_verified': getattr(user, 'is_verified', True),
        }
    }), 200


# ── Logout ────────────────────────────────────────────────────────────────────

@auth_bp.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200


# ── Current user ──────────────────────────────────────────────────────────────

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({
        'user': {
            'id': current_user.id, 'email': current_user.email,
            'username': current_user.username,
            'first_name': current_user.first_name, 'last_name': current_user.last_name,
            'role': current_user.role, 'is_active': current_user.is_active,
            'is_verified': getattr(current_user, 'is_verified', True),
            'created_at': current_user.created_at.isoformat(),
        }
    }), 200


@auth_bp.route('/me', methods=['PUT'])
@login_required
def update_current_user():
    data = request.get_json()
    if 'first_name' in data: current_user.first_name = data['first_name']
    if 'last_name'  in data: current_user.last_name  = data['last_name']
    if 'new_password' in data:
        if not data.get('current_password'):
            return jsonify({'error': 'Current password required'}), 400
        if not current_user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        is_valid, err = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': err}), 400
        current_user.set_password(data['new_password'])
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200


# ── Password Reset ────────────────────────────────────────────────────────────

@auth_bp.route('/password/reset', methods=['POST'])
def request_password_reset():
    data = request.get_json()
    if not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'message': 'If that email exists, a reset link has been sent.'}), 200

    max_age  = current_app.config.get('PASSWORD_RESET_MAX_AGE', 3600)
    token    = _make_token(user.email, _RESET_SALT)
    reset_url = f"{request.host_url.rstrip('/')}/reset-password?token={token}"

    # TODO (production): send reset_url to user.email via your email provider

    resp = {'message': 'If that email exists, a reset link has been sent.'}
    if not IS_PRODUCTION:
        resp['_dev_reset_url'] = reset_url
        resp['_dev_token']     = token

    return jsonify(resp), 200


@auth_bp.route('/password/reset/<token>', methods=['POST'])
def reset_password(token):
    data = request.get_json()
    if not data.get('password'):
        return jsonify({'error': 'New password is required'}), 400

    max_age = current_app.config.get('PASSWORD_RESET_MAX_AGE', 3600)
    email, error = _verify_token(token, _RESET_SALT, max_age)
    if error:
        return jsonify({'error': error}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    is_valid, err = validate_password(data['password'])
    if not is_valid:
        return jsonify({'error': err}), 400

    user.set_password(data['password'])
    db.session.commit()
    return jsonify({'message': 'Password reset successfully. You can now log in.'}), 200
