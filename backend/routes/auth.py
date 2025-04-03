from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from models.profiles import Student, Teacher, Parent
from utils.auth import role_required
from app import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user with role-specific profile"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'name', 'role']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Validate role
        valid_roles = ['admin', 'teacher', 'student', 'parent']
        if data['role'] not in valid_roles:
            return jsonify({'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}), 400
        
        # Create user
        user = User(
            email=data['email'],
            password=generate_password_hash(data['password']),
            name=data['name'],
            role=data['role']
        )
        
        db.session.add(user)
        db.session.flush()  # Get user.id without committing
        
        # Create role-specific profile
        if data['role'] == 'student':
            profile = Student(
                user_id=user.id,
                roll_number=data.get('roll_number'),
                date_of_birth=datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date() \
                    if data.get('date_of_birth') else None,
                department_id=data.get('department_id')
            )
            db.session.add(profile)
            
        elif data['role'] == 'teacher':
            profile = Teacher(
                user_id=user.id,
                employee_id=data.get('employee_id'),
                department_id=data.get('department_id'),
                designation=data.get('designation'),
                joining_date=datetime.strptime(data.get('joining_date'), '%Y-%m-%d').date() \
                    if data.get('joining_date') else None
            )
            db.session.add(profile)
            
        elif data['role'] == 'parent':
            profile = Parent(
                user_id=user.id,
                occupation=data.get('occupation'),
                relationship=data.get('relationship'),
                alternate_phone=data.get('alternate_phone')
            )
            db.session.add(profile)
        
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error in user registration: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return access token"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(field in data for field in ['email', 'password']):
            return jsonify({'error': 'Missing email or password'}), 400
        
        # Find user
        user = User.query.filter_by(email=data['email']).first()
        
        # Verify password
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is inactive'}), 403
        
        # Update last login
        user.update_last_login()
        
        # Generate token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'role': user.role
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in user login: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user's profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get role-specific profile
        profile_data = {}
        if user.role == 'student' and user.student_profile:
            profile_data = {
                'roll_number': user.student_profile.roll_number,
                'date_of_birth': user.student_profile.date_of_birth.isoformat() \
                    if user.student_profile.date_of_birth else None,
                'department': user.student_profile.department.name \
                    if user.student_profile.department else None
            }
        elif user.role == 'teacher' and user.teacher_profile:
            profile_data = {
                'employee_id': user.teacher_profile.employee_id,
                'department': user.teacher_profile.department.name \
                    if user.teacher_profile.department else None,
                'designation': user.teacher_profile.designation,
                'joining_date': user.teacher_profile.joining_date.isoformat() \
                    if user.teacher_profile.joining_date else None
            }
        elif user.role == 'parent' and user.parent_profile:
            profile_data = {
                'occupation': user.parent_profile.occupation,
                'relationship': user.parent_profile.relationship,
                'alternate_phone': user.parent_profile.alternate_phone,
                'students': [{
                    'id': student.id,
                    'name': student.user.name,
                    'roll_number': student.roll_number
                } for student in user.parent_profile.students]
            }
        
        return jsonify({
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'role': user.role,
            'institution': {
                'id': user.institution_id,
                'name': user.institution.name if user.institution else None
            },
            'profile': profile_data,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update basic user info
        if 'name' in data:
            user.name = data['name']
        if 'password' in data:
            user.password = generate_password_hash(data['password'])
        
        # Update role-specific profile
        if user.role == 'student' and user.student_profile:
            if 'roll_number' in data:
                user.student_profile.roll_number = data['roll_number']
            if 'date_of_birth' in data:
                user.student_profile.date_of_birth = datetime.strptime(
                    data['date_of_birth'], '%Y-%m-%d'
                ).date()
            if 'department_id' in data:
                user.student_profile.department_id = data['department_id']
                
        elif user.role == 'teacher' and user.teacher_profile:
            if 'employee_id' in data:
                user.teacher_profile.employee_id = data['employee_id']
            if 'designation' in data:
                user.teacher_profile.designation = data['designation']
            if 'department_id' in data:
                user.teacher_profile.department_id = data['department_id']
                
        elif user.role == 'parent' and user.parent_profile:
            if 'occupation' in data:
                user.parent_profile.occupation = data['occupation']
            if 'relationship' in data:
                user.parent_profile.relationship = data['relationship']
            if 'alternate_phone' in data:
                user.parent_profile.alternate_phone = data['alternate_phone']
        
        db.session.commit()
        
        return jsonify({'message': 'Profile updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
@role_required(['admin'])
def list_users():
    """List all users (admin only)"""
    try:
        # Get query parameters
        role = request.args.get('role')
        institution_id = request.args.get('institution_id')
        
        # Build query
        query = User.query
        
        if role:
            query = query.filter_by(role=role)
        if institution_id:
            query = query.filter_by(institution_id=institution_id)
        
        users = query.all()
        
        result = [{
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'role': user.role,
            'institution_id': user.institution_id,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat()
        } for user in users]
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500