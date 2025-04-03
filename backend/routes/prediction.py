from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.predict import predict_performance
from utils.auth import role_required, student_access_required
from models.tracking import PerformancePrediction
from models.profiles import Student
from models.academic import Enrollment
from app import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.route('/predict', methods=['POST'])
@jwt_required()
@student_access_required
def predict_student_performance():
    """Predict student's performance based on current data"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['student_id', 'course_id']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get student and course enrollment
        student = Student.query.get(data['student_id'])
        if not student:
            return jsonify({'error': 'Student not found'}), 404
            
        enrollment = Enrollment.query.filter_by(
            student_id=data['student_id'],
            course_id=data['course_id']
        ).first()
        
        if not enrollment:
            return jsonify({'error': 'Student not enrolled in this course'}), 404
        
        # Prepare student data for prediction
        student_data = {
            'previous_grade': data.get('previous_grade', 0),
            'attendance_percentage': enrollment.attendance_records.filter_by(status='present').count() / 
                                   enrollment.attendance_records.count() * 100 if enrollment.attendance_records.count() > 0 else 0,
            'assignment_completion_rate': _calculate_assignment_completion_rate(enrollment),
            'class_participation_score': data.get('class_participation_score', 0),
            'study_hours_per_week': data.get('study_hours_per_week', 0),
            'self_study_score': data.get('self_study_score', 0),
            'group_study_score': data.get('group_study_score', 0),
            'submission_timeliness': _calculate_submission_timeliness(enrollment),
            'extra_curricular_participation': data.get('extra_curricular_participation', 0),
            'project_scores': data.get('project_scores', 0)
        }
        
        # Get prediction
        prediction_result = predict_performance(student_data)
        
        # Store prediction
        prediction = PerformancePrediction(
            student_id=data['student_id'],
            course_id=data['course_id'],
            predicted_grade=prediction_result['predicted_grade'],
            confidence_score=prediction_result['confidence_score'],
            factors=prediction_result['importance_factors']
        )
        
        db.session.add(prediction)
        db.session.commit()
        
        return jsonify({
            'prediction_id': prediction.id,
            'results': prediction_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in performance prediction: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@prediction_bp.route('/student/<int:student_id>/history', methods=['GET'])
@jwt_required()
@student_access_required
def get_prediction_history(student_id):
    """Get prediction history for a student"""
    try:
        predictions = PerformancePrediction.query.filter_by(student_id=student_id)\
            .order_by(PerformancePrediction.prediction_date.desc()).all()
        
        result = []
        for prediction in predictions:
            result.append({
                'id': prediction.id,
                'course': {
                    'id': prediction.course.id,
                    'name': prediction.course.name
                },
                'predicted_grade': prediction.predicted_grade,
                'confidence_score': prediction.confidence_score,
                'factors': prediction.factors,
                'prediction_date': prediction.prediction_date.isoformat()
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error fetching prediction history: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@prediction_bp.route('/analytics/course/<int:course_id>', methods=['GET'])
@jwt_required()
@role_required(['teacher', 'admin'])
def get_course_analytics(course_id):
    """Get performance analytics for a course"""
    try:
        predictions = PerformancePrediction.query.filter_by(course_id=course_id).all()
        
        # Calculate grade distribution
        grade_distribution = {
            'A+': 0, 'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0
        }
        
        for prediction in predictions:
            grade_distribution[prediction.predicted_grade] += 1
        
        # Calculate average confidence score
        avg_confidence = sum(p.confidence_score for p in predictions) / len(predictions) if predictions else 0
        
        # Identify common factors
        all_factors = []
        for prediction in predictions:
            if prediction.factors:
                all_factors.extend(prediction.factors)
        
        common_factors = {}
        for factor in all_factors:
            if factor['factor'] not in common_factors:
                common_factors[factor['factor']] = {
                    'count': 1,
                    'avg_importance': factor['importance']
                }
            else:
                common_factors[factor['factor']]['count'] += 1
                common_factors[factor['factor']]['avg_importance'] += factor['importance']
        
        # Calculate average importance for each factor
        for factor in common_factors.values():
            factor['avg_importance'] /= factor['count']
        
        result = {
            'grade_distribution': grade_distribution,
            'average_confidence': round(avg_confidence, 2),
            'common_factors': common_factors,
            'total_predictions': len(predictions),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error fetching course analytics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def _calculate_assignment_completion_rate(enrollment):
    """Calculate assignment completion rate for an enrollment"""
    assignments = enrollment.course.assignments
    if not assignments:
        return 0
    
    completed = sum(1 for a in assignments if any(
        s.student_id == enrollment.student_id for s in a.submissions
    ))
    
    return (completed / len(assignments)) * 100

def _calculate_submission_timeliness(enrollment):
    """Calculate submission timeliness score"""
    submissions = []
    for assignment in enrollment.course.assignments:
        submission = next((s for s in assignment.submissions 
                         if s.student_id == enrollment.student_id), None)
        if submission:
            submissions.append(submission)
    
    if not submissions:
        return 0
    
    on_time = sum(1 for s in submissions if s.submission_date <= s.assignment.due_date)
    return (on_time / len(submissions)) * 100