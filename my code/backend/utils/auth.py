from functools import wraps
from datetime import datetime, timedelta

import jwt
from flask import current_app, request, g, jsonify

from backend.database.models import User


def generate_token(user: User, expires_delta: timedelta | None = None) -> str:
    """Return a JWT for *user* using app secret key."""
    if expires_delta is None:
        expires_delta = timedelta(hours=1)
    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + expires_delta
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    # PyJWT returns str in 2.x
    return token


def verify_token(token: str) -> User | None:
    """Decode JWT and return the corresponding User or None."""
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        uid = data.get('user_id')
        if uid is None:
            return None
        return User.query.get(uid)
    except Exception:
        return None


def login_required(f):
    """Decorator that verifies JWT from the Authorization header."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'missing token'}), 401
        token = auth.split(None, 1)[1]
        user = verify_token(token)
        if user is None:
            return jsonify({'error': 'invalid token'}), 401
        g.current_user = user
        return f(*args, **kwargs)

    return decorated
