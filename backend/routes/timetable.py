from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.auth import role_required, institution_access_required
from models.scheduling import Timetable, TimeSlot
from models.academic import Department, Course
from models.profiles import Teacher
from app import db
import logging
from datetime import datetime, time

logger = logging.getLogger(__name__)
timetable_bp = Blueprint('timetable', __name__)

@timetable_bp.route('/create', methods=['POST'])
@jwt_required()
@role_required(['admin', 'teacher'])
def create_timetable():
    """Create a new timetable"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'department_id', 'term_id']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if department exists
        department = Department.query.get(data['department_id'])
        if not department:
            return jsonify({'error': 'Department not found'}), 404
        
        # Create timetable
        timetable = Timetable(
            name=data['name'],
            department_id=data['department_id'],
            term_id=data['term_id'],
            generated_by_id=get_jwt_identity()
        )
        
        db.session.add(timetable)
        db.session.commit()
        
        return jsonify({
            'message': 'Timetable created successfully',
            'timetable_id': timetable.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating timetable: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@timetable_bp.route('/<int:timetable_id>/slots', methods=['POST'])
@jwt_required()
@role_required(['admin', 'teacher'])
def add_time_slot(timetable_id):
    """Add a time slot to timetable"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['course_id', 'teacher_id', 'day_of_week', 
                         'start_time', 'end_time', 'room_number']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate time format
        try:
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Invalid time format. Use HH:MM'}), 400
        
        # Check for time slot conflicts
        conflicts = TimeSlot.query.filter_by(
            timetable_id=timetable_id,
            day_of_week=data['day_of_week']
        ).filter(
            ((TimeSlot.start_time <= start_time) & (TimeSlot.end_time > start_time)) |
            ((TimeSlot.start_time < end_time) & (TimeSlot.end_time >= end_time))
        ).first()
        
        if conflicts:
            return jsonify({'error': 'Time slot conflicts with existing schedule'}), 409
        
        # Create time slot
        time_slot = TimeSlot(
            timetable_id=timetable_id,
            course_id=data['course_id'],
            teacher_id=data['teacher_id'],
            day_of_week=data['day_of_week'],
            start_time=start_time,
            end_time=end_time,
            room_number=data['room_number']
        )
        
        db.session.add(time_slot)
        db.session.commit()
        
        return jsonify({
            'message': 'Time slot added successfully',
            'slot_id': time_slot.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding time slot: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@timetable_bp.route('/<int:timetable_id>/slots/<int:slot_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin', 'teacher'])
def delete_time_slot(timetable_id, slot_id):
    """Delete a time slot from timetable"""
    try:
        slot = TimeSlot.query.filter_by(id=slot_id, timetable_id=timetable_id).first()
        if not slot:
            return jsonify({'error': 'Time slot not found'}), 404
        
        db.session.delete(slot)
        db.session.commit()
        
        return jsonify({'message': 'Time slot deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting time slot: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@timetable_bp.route('/<int:timetable_id>', methods=['GET'])
@jwt_required()
def get_timetable(timetable_id):
    """Get timetable details"""
    try:
        timetable = Timetable.query.get(timetable_id)
        if not timetable:
            return jsonify({'error': 'Timetable not found'}), 404
        
        # Organize slots by day
        slots_by_day = {i: [] for i in range(7)}  # 0=Monday to 6=Sunday
        
        for slot in timetable.slots:
            slots_by_day[slot.day_of_week].append({
                'id': slot.id,
                'course': {
                    'id': slot.course.id,
                    'name': slot.course.name,
                    'code': slot.course.code
                },
                'teacher': {
                    'id': slot.teacher.id,
                    'name': slot.teacher.user.name
                },
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'room_number': slot.room_number
            })
        
        result = {
            'id': timetable.id,
            'name': timetable.name,
            'department': {
                'id': timetable.department.id,
                'name': timetable.department.name
            },
            'term': {
                'id': timetable.term.id,
                'name': timetable.term.name
            },
            'slots_by_day': slots_by_day,
            'is_active': timetable.is_active,
            'created_at': timetable.created_at.isoformat(),
            'updated_at': timetable.updated_at.isoformat()
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error fetching timetable: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@timetable_bp.route('/department/<int:department_id>/active', methods=['GET'])
@jwt_required()
def get_active_timetable(department_id):
    """Get active timetable for a department"""
    try:
        timetable = Timetable.query.filter_by(
            department_id=department_id,
            is_active=True
        ).first()
        
        if not timetable:
            return jsonify({'error': 'No active timetable found'}), 404
        
        return get_timetable(timetable.id)
        
    except Exception as e:
        logger.error(f"Error fetching active timetable: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@timetable_bp.route('/<int:timetable_id>/activate', methods=['POST'])
@jwt_required()
@role_required(['admin', 'teacher'])
def activate_timetable(timetable_id):
    """Set a timetable as active"""
    try:
        timetable = Timetable.query.get(timetable_id)
        if not timetable:
            return jsonify({'error': 'Timetable not found'}), 404
        
        # Deactivate other timetables for the department
        Timetable.query.filter_by(department_id=timetable.department_id)\
            .update({'is_active': False})
        
        # Activate selected timetable
        timetable.is_active = True
        db.session.commit()
        
        return jsonify({'message': 'Timetable activated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error activating timetable: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@timetable_bp.route('/teacher/<int:teacher_id>/schedule', methods=['GET'])
@jwt_required()
def get_teacher_schedule(teacher_id):
    """Get schedule for a specific teacher"""
    try:
        slots = TimeSlot.query.filter_by(teacher_id=teacher_id)\
            .join(Timetable)\
            .filter(Timetable.is_active == True)\
            .all()
        
        schedule = {i: [] for i in range(7)}
        
        for slot in slots:
            schedule[slot.day_of_week].append({
                'id': slot.id,
                'course': {
                    'id': slot.course.id,
                    'name': slot.course.name,
                    'code': slot.course.code
                },
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'room_number': slot.room_number,
                'timetable': {
                    'id': slot.timetable.id,
                    'name': slot.timetable.name
                }
            })
        
        return jsonify(schedule), 200
        
    except Exception as e:
        logger.error(f"Error fetching teacher schedule: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500