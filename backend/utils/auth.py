from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models.user import User
import logging
from typing import List, Optional, Callable

logger = logging.getLogger(__name__)

def get_user_role() -> Optional[str]:
    """
    Get the role of the currently authenticated user
    
    Returns:
        Optional[str]: User role if authenticated, None otherwise
    """
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        return user.role if user else None
    except Exception as e:
        logger.error(f"Error getting user role: {str(e)}")
        return None

def role_required(allowed_roles: List[str]) -> Callable:
    """
    Decorator to check if user has required role
    
    Args:
        allowed_roles (List[str]): List of roles that are allowed to access the endpoint
        
    Returns:
        Callable: Decorated function
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                user = User.query.get(user_id)
                
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                
                if user.role not in allowed_roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                return fn(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in role verification: {str(e)}")
                return jsonify({'error': 'Authentication error'}), 401
        return wrapper
    return decorator

def institution_access_required(fn: Callable) -> Callable:
    """
    Decorator to check if user has access to the institution
    
    Args:
        fn (Callable): Function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Get institution_id from request
            institution_id = request.view_args.get('institution_id') or \
                           request.args.get('institution_id') or \
                           request.json.get('institution_id')
            
            if not institution_id:
                return jsonify({'error': 'Institution ID required'}), 400
            
            # Check if user belongs to the institution
            if user.institution_id != int(institution_id) and user.role != 'admin':
                return jsonify({'error': 'No access to this institution'}), 403
            
            return fn(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in institution access verification: {str(e)}")
            return jsonify({'error': 'Authentication error'}), 401
    return wrapper

def student_access_required(fn: Callable) -> Callable:
    """
    Decorator to check if user has access to student data
    
    Args:
        fn (Callable): Function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Get student_id from request
            student_id = request.view_args.get('student_id') or \
                        request.args.get('student_id') or \
                        request.json.get('student_id')
            
            if not student_id:
                return jsonify({'error': 'Student ID required'}), 400
            
            # Allow access if user is:
            # 1. The student themselves
            # 2. A parent of the student
            # 3. A teacher in the same institution
            # 4. An admin
            has_access = False
            
            if user.role == 'admin':
                has_access = True
            elif user.role == 'student':
                has_access = user.student_profile and user.student_profile.id == int(student_id)
            elif user.role == 'parent':
                has_access = any(s.id == int(student_id) for s in user.parent_profile.students)
            elif user.role == 'teacher':
                # Check if teacher and student are in same institution
                student = User.query.join(User.student_profile).filter_by(id=student_id).first()
                has_access = student and student.institution_id == user.institution_id
            
            if not has_access:
                return jsonify({'error': 'No access to this student\'s data'}), 403
            
            return fn(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in student access verification: {str(e)}")
            return jsonify({'error': 'Authentication error'}), 401
    return wrapper

def validate_token(token: str) -> bool:
    """
    Validate JWT token
    
    Args:
        token (str): JWT token to validate
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    try:
        verify_jwt_in_request()
        return True
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return False

def get_current_user() -> Optional[User]:
    """
    Get currently authenticated user
    
    Returns:
        Optional[User]: User object if authenticated, None otherwise
    """
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        return User.query.get(user_id)
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return None

class RoleChecker:
    """Class for checking user roles and permissions"""
    
    @staticmethod
    def is_admin(user: User) -> bool:
        """Check if user is admin"""
        return user.role == 'admin'
    
    @staticmethod
    def is_teacher(user: User) -> bool:
        """Check if user is teacher"""
        return user.role == 'teacher'
    
    @staticmethod
    def is_student(user: User) -> bool:
        """Check if user is student"""
        return user.role == 'student'
    
    @staticmethod
    def is_parent(user: User) -> bool:
        """Check if user is parent"""
        return user.role == 'parent'
    
    @staticmethod
    def can_access_institution(user: User, institution_id: int) -> bool:
        """Check if user can access institution"""
        return user.institution_id == institution_id or user.role == 'admin'
    
    @staticmethod
    def can_access_student(user: User, student_id: int) -> bool:
        """Check if user can access student data"""
        if user.role == 'admin':
            return True
        elif user.role == 'student':
            return user.student_profile and user.student_profile.id == student_id
        elif user.role == 'parent':
            return any(s.id == student_id for s in user.parent_profile.students)
        elif user.role == 'teacher':
            student = User.query.join(User.student_profile).filter_by(id=student_id).first()
            return student and student.institution_id == user.institution_id
        return False