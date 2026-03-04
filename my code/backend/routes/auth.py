from flask import Blueprint, request, jsonify
from backend.database.db import db
from backend.database.models import User
from backend.utils.auth import generate_token, login_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """Create a new user account and return token."""
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'email already registered'}), 400

    user = User(email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = generate_token(user)
    return jsonify({'user': user.to_dict(), 'token': token}), 201


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first() if email else None
    if user is None or not user.check_password(password or ''):
        return jsonify({'error': 'invalid credentials'}), 401

    token = generate_token(user)
    return jsonify({'user': user.to_dict(), 'token': token})


@auth_bp.route('/auth/me', methods=['GET'])
@login_required
def me():
    user = request.environ.get('current_user')
    # actually login_required stores in g
    from flask import g
    return jsonify({'user': g.current_user.to_dict()})
