from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from utils.ocr import process_marksheet
from utils.auth import role_required
from models.tracking import Marksheet, SubjectMark
from models.profiles import Student
from app import db
import logging

logger = logging.getLogger(__name__)
marksheet_bp = Blueprint('marksheet', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@marksheet_bp.route('/upload', methods=['POST'])
@jwt_required()
@role_required(['teacher', 'admin'])
def upload_marksheet():
    """Upload and process marksheet"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Get student ID from request
        student_id = request.form.get('student_id')
        term_id = request.form.get('term_id')
        
        if not student_id or not term_id:
            return jsonify({'error': 'Student ID and Term ID are required'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process marksheet using OCR
        try:
            result = process_marksheet(filepath)
        except Exception as e:
            logger.error(f"OCR processing error: {str(e)}")
            return jsonify({'error': 'Error processing marksheet'}), 500
        
        # Create marksheet record
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        marksheet = Marksheet(
            student_id=student_id,
            term_id=term_id,
            total_marks=result['total_marks']['obtained'],
            percentage=result['total_marks']['percentage'],
            scanned_copy_path=filepath,
            verified=False,
            verified_by_id=None
        )
        
        db.session.add(marksheet)
        
        # Add subject marks
        for mark_data in result['marks_data']:
            subject_mark = SubjectMark(
                marksheet=marksheet,
                marks_obtained=mark_data['marks_obtained'],
                max_marks=mark_data['max_marks']
            )
            db.session.add(subject_mark)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Marksheet processed successfully',
            'marksheet_id': marksheet.id,
            'results': result
        }), 201
        
    except Exception as e:
        logger.error(f"Error in marksheet upload: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@marksheet_bp.route('/<int:marksheet_id>/verify', methods=['POST'])
@jwt_required()
@role_required(['teacher', 'admin'])
def verify_marksheet(marksheet_id):
    """Verify processed marksheet"""
    try:
        marksheet = Marksheet.query.get(marksheet_id)
        if not marksheet:
            return jsonify({'error': 'Marksheet not found'}), 404
        
        user_id = get_jwt_identity()
        
        marksheet.verified = True
        marksheet.verified_by_id = user_id
        db.session.commit()
        
        return jsonify({'message': 'Marksheet verified successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error in marksheet verification: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@marksheet_bp.route('/student/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_marksheets(student_id):
    """Get all marksheets for a student"""
    try:
        marksheets = Marksheet.query.filter_by(student_id=student_id).all()
        
        result = []
        for marksheet in marksheets:
            result.append({
                'id': marksheet.id,
                'term_id': marksheet.term_id,
                'total_marks': marksheet.total_marks,
                'percentage': marksheet.percentage,
                'grade': marksheet.grade,
                'verified': marksheet.verified,
                'created_at': marksheet.created_at.isoformat()
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error fetching student marksheets: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@marksheet_bp.route('/<int:marksheet_id>', methods=['GET'])
@jwt_required()
def get_marksheet_details(marksheet_id):
    """Get detailed information about a marksheet"""
    try:
        marksheet = Marksheet.query.get(marksheet_id)
        if not marksheet:
            return jsonify({'error': 'Marksheet not found'}), 404
        
        subject_marks = []
        for mark in marksheet.subject_marks:
            subject_marks.append({
                'subject': mark.course.name if mark.course else 'Unknown',
                'marks_obtained': mark.marks_obtained,
                'max_marks': mark.max_marks,
                'percentage': (mark.marks_obtained / mark.max_marks * 100) if mark.max_marks > 0 else 0
            })
        
        result = {
            'id': marksheet.id,
            'student': {
                'id': marksheet.student.id,
                'name': marksheet.student.user.name
            },
            'term': {
                'id': marksheet.term.id,
                'name': marksheet.term.name
            },
            'total_marks': marksheet.total_marks,
            'percentage': marksheet.percentage,
            'grade': marksheet.grade,
            'verified': marksheet.verified,
            'verified_by': marksheet.verified_by.name if marksheet.verified_by else None,
            'subject_marks': subject_marks,
            'created_at': marksheet.created_at.isoformat(),
            'updated_at': marksheet.updated_at.isoformat()
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error fetching marksheet details: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500