"""
Decorators
Custom decorators for routes
"""

from functools import wraps
from flask import jsonify
from flask_login import current_user
from werkzeug.http import HTTP_STATUS_CODES


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to access this resource'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def roles_required(*roles):
    """Decorator to require specific roles for routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this resource'
                }), 401
            
            if current_user.role not in roles:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'message': f'This resource requires one of the following roles: {", ".join(roles)}'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to access this resource'
            }), 401
        
        if current_user.role != 'admin':
            return jsonify({
                'error': 'Insufficient permissions',
                'message': 'This resource requires admin privileges'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function


def rate_limit(max_requests=100, window=60):
    """Decorator to rate limit routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # In production, implement actual rate limiting
            # using Redis or similar
            # This is a placeholder
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_key_required(f):
    """Decorator to require API key for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In production, implement API key validation
        # This is a placeholder
        return f(*args, **kwargs)
    return decorated_function


def validate_request(*required_fields):
    """Decorator to validate required fields in request"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request
            
            if request.method in ['POST', 'PUT', 'PATCH']:
                data = request.get_json()
                if not data:
                    return jsonify({
                        'error': 'Invalid request',
                        'message': 'Request body must be JSON'
                    }), 400
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'fields': missing_fields
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
