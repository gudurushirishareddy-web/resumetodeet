"""
Resume Routes - Upload, Extract, Quality Analysis
"""
import os
import logging
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from nlp.parser import parse_file
from nlp.extractor import get_extractor
from models.database import save_resume, get_resume, get_user_resumes

resume_bp = Blueprint('resume', __name__)
logger = logging.getLogger(__name__)


def allowed_file(filename):
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'docx', 'jpg', 'jpeg', 'png'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


@resume_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_resume():
    """
    POST /api/resume/upload
    Accepts: multipart/form-data with 'resume' file
    Returns: extracted data JSON
    """
    user_id = int(get_jwt_identity())

    if 'resume' not in request.files:
        return jsonify({'error': 'No file provided. Use key: resume'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({
            'error': 'Invalid file type. Allowed: PDF, DOCX, JPG, PNG'
        }), 400

    try:
        # Secure the filename and add UUID to avoid collisions
        original_name = secure_filename(file.filename)
        ext = original_name.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}_{original_name}"

        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_name)
        file.save(file_path)

        logger.info(f"File saved: {unique_name} for user {user_id}")

        # Parse file
        text, parse_method = parse_file(file_path, ext)

        if not text or len(text.strip()) < 20:
            return jsonify({
                'error': 'Could not extract text from the file. '
                         'Please ensure the file is not corrupted or encrypted.'
            }), 422

        # Extract structured data
        extractor = get_extractor()
        extracted = extractor.extract(text)
        extracted['parse_method'] = parse_method
        extracted['original_filename'] = original_name

        # Save to database
        resume_id = save_resume(
            user_id=user_id,
            filename=original_name,
            file_path=file_path,
            file_type=ext,
            extracted_data=extracted,
            quality_score=extracted.get('quality_score', 0)
        )

        logger.info(f"Resume extracted: ID={resume_id}, quality={extracted.get('quality_score')}")

        return jsonify({
            'success': True,
            'resume_id': resume_id,
            'extracted': extracted,
            'message': f'Resume parsed successfully using {parse_method}'
        }), 200

    except Exception as e:
        logger.error(f"Upload error for user {user_id}: {e}", exc_info=True)
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500


@resume_bp.route('/<int:resume_id>', methods=['GET'])
@jwt_required()
def get_resume_data(resume_id):
    """GET /api/resume/<id> - get previously extracted resume data"""
    user_id = int(get_jwt_identity())
    resume = get_resume(resume_id, user_id)
    if not resume:
        return jsonify({'error': 'Resume not found'}), 404
    return jsonify(resume), 200


@resume_bp.route('/list', methods=['GET'])
@jwt_required()
def list_resumes():
    """GET /api/resume/list - list all resumes for current user"""
    user_id = int(get_jwt_identity())
    resumes = get_user_resumes(user_id)
    return jsonify({'resumes': resumes}), 200


@resume_bp.route('/gap-analysis', methods=['POST'])
@jwt_required()
def gap_analysis():
    """POST /api/resume/gap-analysis - skill gap & job match suggestions"""
    data = request.get_json()
    skills = data.get('skills', [])
    job_role = data.get('job_role', '').lower()

    # Predefined job role skill requirements
    job_requirements = {
        'software engineer': ['python', 'javascript', 'git', 'algorithms', 'data structures', 'sql'],
        'data scientist': ['python', 'machine learning', 'pandas', 'numpy', 'sql', 'statistics'],
        'web developer': ['html', 'css', 'javascript', 'react', 'nodejs', 'git'],
        'devops engineer': ['docker', 'kubernetes', 'ci/cd', 'linux', 'aws', 'terraform'],
        'ml engineer': ['python', 'tensorflow', 'pytorch', 'machine learning', 'deep learning'],
        'frontend developer': ['html', 'css', 'javascript', 'react', 'typescript', 'figma'],
        'backend developer': ['python', 'java', 'nodejs', 'sql', 'rest api', 'docker'],
        'full stack developer': ['html', 'css', 'javascript', 'react', 'nodejs', 'sql', 'git'],
    }

    current_skills_lower = [s.lower() for s in skills]
    suggestions = {}

    for role, required in job_requirements.items():
        missing = [r for r in required if r not in current_skills_lower]
        match_pct = round((len(required) - len(missing)) / len(required) * 100)
        suggestions[role] = {
            'match_percentage': match_pct,
            'missing_skills': missing,
            'has_skills': [r for r in required if r in current_skills_lower]
        }

    # Sort by match percentage
    sorted_suggestions = dict(
        sorted(suggestions.items(), key=lambda x: x[1]['match_percentage'], reverse=True)
    )

    # Best match
    best_role = list(sorted_suggestions.keys())[0] if sorted_suggestions else None

    return jsonify({
        'job_suggestions': sorted_suggestions,
        'best_match': best_role,
        'recommendations': _get_recommendations(sorted_suggestions)
    }), 200


def _get_recommendations(suggestions):
    recs = []
    for role, data in list(suggestions.items())[:3]:
        if data['missing_skills']:
            recs.append({
                'role': role,
                'action': f"Learn {', '.join(data['missing_skills'][:3])} to qualify for {role}",
                'match': data['match_percentage']
            })
    return recs
