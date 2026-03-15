"""
Authentication Routes - Login, Signup, Logout
"""
import logging
import re
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models.database import create_user, get_user_by_email, get_user_by_id, update_last_login, init_db

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# Initialize DB on first import
init_db()


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password):
    """Min 8 chars, at least one uppercase, one digit, one special char."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Valid"


@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')

        # Validation
        if not full_name or len(full_name) < 2:
            return jsonify({'error': 'Full name must be at least 2 characters'}), 400
        if not validate_email(email):
            return jsonify({'error': 'Invalid email address'}), 400
        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400

        valid, msg = validate_password(password)
        if not valid:
            return jsonify({'error': msg}), 400

        # Check if email exists
        existing = get_user_by_email(email)
        if existing:
            return jsonify({'error': 'Email already registered'}), 409

        # Create user
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        user_id = create_user(full_name, email, password_hash)

        if not user_id:
            return jsonify({'error': 'Failed to create account'}), 500

        access_token = create_access_token(identity=str(user_id))

        logger.info(f"New user registered: {email}")
        return jsonify({
            'message': 'Account created successfully',
            'access_token': access_token,
            'user': {'id': user_id, 'full_name': full_name, 'email': email}
        }), 201

    except Exception as e:
        logger.error(f"Signup error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        user = get_user_by_email(email)
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Invalid email or password'}), 401

        if not user['is_active']:
            return jsonify({'error': 'Account is deactivated'}), 403

        update_last_login(user['id'])
        access_token = create_access_token(identity=str(user['id']))

        logger.info(f"User logged in: {email}")
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user['id'],
                'full_name': user['full_name'],
                'email': user['email']
            }
        }), 200

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    try:
        user_id = int(get_jwt_identity())
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({
            'id': user['id'],
            'full_name': user['full_name'],
            'email': user['email'],
            'created_at': user['created_at']
        }), 200
    except Exception as e:
        logger.error(f"Me endpoint error: {e}")
        return jsonify({'error': 'Failed to get user info'}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # JWT is stateless; client should delete token
    return jsonify({'message': 'Logged out successfully'}), 200
