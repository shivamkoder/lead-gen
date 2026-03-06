"""
Authentication Routes
User registration, login, logout, and password management
"""

from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user
from backend.app.extensions import db
from backend.app.models import User
import re

auth_bp = Blueprint('auth', __name__)


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, None


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate email format
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    # Check if username already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 400
    
    # Validate password strength
    is_valid, error_message = validate_password(data['password'])
    if not is_valid:
        return jsonify({'error': error_message}), 400
    
    # Create new user
    user = User(
        email=data['email'],
        username=data['username'],
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        role=data.get('role', 'user')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'role': user.role
        }
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
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
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'role': user.role
        }
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current logged in user"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify({
        'user': {
            'id': current_user.id,
            'email': current_user.email,
            'username': current_user.username,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'role': current_user.role,
            'is_active': current_user.is_active,
            'created_at': current_user.created_at.isoformat()
        }
    }), 200


@auth_bp.route('/me', methods=['PUT'])
def update_current_user():
    """Update current user profile"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    
    # Update allowed fields
    if 'first_name' in data:
        current_user.first_name = data['first_name']
    if 'last_name' in data:
        current_user.last_name = data['last_name']
    
    # Password update requires current password
    if 'new_password' in data:
        if not data.get('current_password'):
            return jsonify({'error': 'Current password required to change password'}), 400
        
        if not current_user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        is_valid, error_message = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        current_user.set_password(data['new_password'])
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully',
        'user': {
            'id': current_user.id,
            'email': current_user.email,
            'username': current_user.username,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name
        }
    }), 200


@auth_bp.route('/password/reset', methods=['POST'])
def request_password_reset():
    """Request password reset"""
    data = request.get_json()
    
    if not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    # Always return success to prevent email enumeration
    if user:
        # TODO: Send password reset email
        # In production, generate reset token and send email
        pass
    
    return jsonify({
        'message': 'If the email exists, a password reset link has been sent'
    }), 200


@auth_bp.route('/password/reset/<token>', methods=['POST'])
def reset_password(token):
    """Reset password with token"""
    data = request.get_json()
    
    if not data.get('password'):
        return jsonify({'error': 'New password is required'}), 400
    
    # TODO: Validate token and reset password
    # In production, verify the token and update the password
    
    return jsonify({'message': 'Password reset successful'}), 200



