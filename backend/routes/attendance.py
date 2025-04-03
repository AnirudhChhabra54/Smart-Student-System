from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.auth import role_required, student_access_required
from models.tracking import AttendanceRecord
from models.academic import Enrollment
from models.profiles import Student
from app import db
import logging
from datetime import datetime, timedelta
from sqlalchemy import func

logger = logging.getLogger(__name__)
attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/mark', methods=['POST'])
@jwt_required()
@role_required(['teacher', 'admin'])
def mark_attendance():
    """Mark attendance for students"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(key in data for key in ['enrollment_id', 'date', 'status']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate status
        valid_statuses = ['present', 'absent', 'late']
        if data['status'] not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Parse date
        try:
            attendance_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Check if attendance already marked
        existing = AttendanceRecord.query.filter_by(
            enrollment_id=data['enrollment_id'],
            date=attendance_date
        ).first()
        
        if existing:
            # Update existing record
            existing.status = data['status']
            existing.remarks = data.get('remarks')
            existing.marked_by_id = get_jwt_identity()
        else:
            # Create new record
            record = AttendanceRecord(
                enrollment_id=data['enrollment_id'],
                date=attendance_date,
                status=data['status'],
                remarks=data.get('remarks'),
                marked_by_id=get_jwt_identity()
            )
            db.session.add(record)
        
        db.session.commit()
        
        return jsonify({'message': 'Attendance marked successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error marking attendance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@attendance_bp.route('/bulk-mark', methods=['POST'])
@jwt_required()
@role_required(['teacher', 'admin'])
def mark_bulk_attendance():
    """Mark attendance for multiple students"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(key in data for key in ['attendance_data', 'date']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Parse date
        try:
            attendance_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Process each attendance record
        records_processed = 0
        for record in data['attendance_data']:
            if all(key in record for key in ['enrollment_id', 'status']):
                # Check if attendance already marked
                existing = AttendanceRecord.query.filter_by(
                    enrollment_id=record['enrollment_id'],
                    date=attendance_date
                ).first()
                
                if existing:
                    existing.status = record['status']
                    existing.remarks = record.get('remarks')
                    existing.marked_by_id = get_jwt_identity()
                else:
                    new_record = AttendanceRecord(
                        enrollment_id=record['enrollment_id'],
                        date=attendance_date,
                        status=record['status'],
                        remarks=record.get('remarks'),
                        marked_by_id=get_jwt_identity()
                    )
                    db.session.add(new_record)
                
                records_processed += 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Bulk attendance marked successfully',
            'records_processed': records_processed
        }), 200
        
    except Exception as e:
        logger.error(f"Error marking bulk attendance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@attendance_bp.route('/student/<int:student_id>/report', methods=['GET'])
@jwt_required()
@student_access_required
def get_student_attendance_report(student_id):
    """Get attendance report for a student"""
    try:
        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Parse dates if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Query attendance records
        query = AttendanceRecord.query.join(Enrollment)\
            .filter(Enrollment.student_id == student_id)
        
        if start_date:
            query = query.filter(AttendanceRecord.date >= start_date)
        if end_date:
            query = query.filter(AttendanceRecord.date <= end_date)
        
        records = query.all()
        
        # Calculate statistics
        total_classes = len(records)
        present_count = sum(1 for r in records if r.status == 'present')
        absent_count = sum(1 for r in records if r.status == 'absent')
        late_count = sum(1 for r in records if r.status == 'late')
        
        attendance_percentage = (present_count / total_classes * 100) if total_classes > 0 else 0
        
        # Group by course
        course_wise = {}
        for record in records:
            course_id = record.enrollment.course_id
            course_name = record.enrollment.course.name
            
            if course_id not in course_wise:
                course_wise[course_id] = {
                    'course_name': course_name,
                    'total': 0,
                    'present': 0,
                    'absent': 0,
                    'late': 0
                }
            
            course_wise[course_id]['total'] += 1
            course_wise[course_id][record.status] += 1
        
        # Calculate percentage for each course
        for course in course_wise.values():
            course['percentage'] = (course['present'] / course['total'] * 100) \
                if course['total'] > 0 else 0
        
        result = {
            'overall_statistics': {
                'total_classes': total_classes,
                'present': present_count,
                'absent': absent_count,
                'late': late_count,
                'attendance_percentage': round(attendance_percentage, 2)
            },
            'course_wise_statistics': course_wise,
            'date_range': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            }
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error generating attendance report: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@attendance_bp.route('/analytics/course/<int:course_id>', methods=['GET'])
@jwt_required()
@role_required(['teacher', 'admin'])
def get_course_attendance_analytics(course_id):
    """Get attendance analytics for a course"""
    try:
        # Get enrollments for the course
        enrollments = Enrollment.query.filter_by(course_id=course_id).all()
        
        analytics = {
            'overall_statistics': {
                'total_students': len(enrollments),
                'average_attendance': 0,
                'attendance_distribution': {
                    'above_90': 0,
                    '75_90': 0,
                    '60_75': 0,
                    'below_60': 0
                }
            },
            'daily_statistics': {},
            'student_wise_statistics': []
        }
        
        total_attendance_percentage = 0
        
        for enrollment in enrollments:
            # Calculate student's attendance
            records = AttendanceRecord.query.filter_by(enrollment_id=enrollment.id).all()
            total = len(records)
            present = sum(1 for r in records if r.status == 'present')
            percentage = (present / total * 100) if total > 0 else 0
            
            # Update distribution counts
            if percentage >= 90:
                analytics['overall_statistics']['attendance_distribution']['above_90'] += 1
            elif percentage >= 75:
                analytics['overall_statistics']['attendance_distribution']['75_90'] += 1
            elif percentage >= 60:
                analytics['overall_statistics']['attendance_distribution']['60_75'] += 1
            else:
                analytics['overall_statistics']['attendance_distribution']['below_60'] += 1
            
            total_attendance_percentage += percentage
            
            # Add to student-wise statistics
            analytics['student_wise_statistics'].append({
                'student_id': enrollment.student_id,
                'student_name': enrollment.student.user.name,
                'attendance_percentage': round(percentage, 2),
                'total_classes': total,
                'present': present,
                'absent': sum(1 for r in records if r.status == 'absent'),
                'late': sum(1 for r in records if r.status == 'late')
            })
        
        # Calculate average attendance
        if enrollments:
            analytics['overall_statistics']['average_attendance'] = \
                round(total_attendance_percentage / len(enrollments), 2)
        
        # Get daily attendance statistics for the last 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        daily_records = db.session.query(
            AttendanceRecord.date,
            func.count().label('total'),
            func.sum(case([(AttendanceRecord.status == 'present', 1)], else_=0)).label('present')
        ).join(Enrollment)\
        .filter(
            Enrollment.course_id == course_id,
            AttendanceRecord.date.between(start_date, end_date)
        ).group_by(AttendanceRecord.date).all()
        
        for record in daily_records:
            analytics['daily_statistics'][record.date.isoformat()] = {
                'total': record.total,
                'present': record.present,
                'percentage': round((record.present / record.total * 100), 2)
            }
        
        return jsonify(analytics), 200
        
    except Exception as e:
        logger.error(f"Error generating course analytics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500