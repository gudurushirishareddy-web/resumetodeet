"""
DEET Registration Routes - Save, Submit, List
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models.database import (
    save_registration, submit_registration,
    get_user_registrations, get_registration
)

deet_bp = Blueprint('deet', __name__)
logger = logging.getLogger(__name__)


@deet_bp.route('/save', methods=['POST'])
@jwt_required()
def save_draft():
    """POST /api/deet/save - Save a draft DEET registration."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    resume_id = data.get('resume_id')
    form_data = data.get('form_data', {})

    reg_id = save_registration(user_id, resume_id, form_data, status='draft')
    return jsonify({
        'success': True,
        'registration_id': reg_id,
        'message': 'Draft saved successfully'
    }), 201


@deet_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit():
    """POST /api/deet/submit - Final submission of DEET registration."""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    reg_id = data.get('registration_id')
    final_data = data.get('form_data', {})

    # Validate required fields
    required = ['full_name', 'email', 'phone']
    missing = [f for f in required if not final_data.get(f)]
    if missing:
        return jsonify({
            'error': f"Missing required fields: {', '.join(missing)}"
        }), 400

    if reg_id:
        # Update existing
        submit_registration(reg_id, user_id, final_data)
    else:
        # Create new
        resume_id = data.get('resume_id')
        reg_id = save_registration(user_id, resume_id, final_data, status='submitted')
        from models.database import submit_registration as do_submit
        do_submit(reg_id, user_id, final_data)

    logger.info(f"DEET registration submitted: ID={reg_id} user={user_id}")

    return jsonify({
        'success': True,
        'registration_id': reg_id,
        'message': 'Registration submitted successfully!',
        'confirmation_number': f"DEET-{reg_id:06d}"
    }), 200


@deet_bp.route('/list', methods=['GET'])
@jwt_required()
def list_registrations():
    """GET /api/deet/list - List all registrations for current user."""
    user_id = int(get_jwt_identity())
    registrations = get_user_registrations(user_id)
    return jsonify({'registrations': registrations}), 200


@deet_bp.route('/<int:reg_id>', methods=['GET'])
@jwt_required()
def get_reg(reg_id):
    """GET /api/deet/<id> - Get a specific registration."""
    user_id = int(get_jwt_identity())
    reg = get_registration(reg_id, user_id)
    if not reg:
        return jsonify({'error': 'Registration not found'}), 404
    return jsonify(reg), 200
