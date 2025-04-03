from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.auth import role_required, student_access_required
from models.gamification import (
    Badge, StudentBadge, Leaderboard, LeaderboardRanking,
    PointTransaction, Reward, RewardRedemption
)
from models.profiles import Student
from app import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
gamification_bp = Blueprint('gamification', __name__)

@gamification_bp.route('/badges', methods=['POST'])
@jwt_required()
@role_required(['admin', 'teacher'])
def create_badge():
    """Create a new badge"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'description', 'category', 'points']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        badge = Badge(
            name=data['name'],
            description=data['description'],
            category=data['category'],
            points=data['points'],
            icon_path=data.get('icon_path'),
            criteria=data.get('criteria', {})
        )
        
        db.session.add(badge)
        db.session.commit()
        
        return jsonify({
            'message': 'Badge created successfully',
            'badge_id': badge.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating badge: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@gamification_bp.route('/badges/award', methods=['POST'])
@jwt_required()
@role_required(['admin', 'teacher'])
def award_badge():
    """Award a badge to a student"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(field in data for field in ['student_id', 'badge_id']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if student already has this badge
        existing = StudentBadge.query.filter_by(
            student_id=data['student_id'],
            badge_id=data['badge_id']
        ).first()
        
        if existing:
            return jsonify({'error': 'Student already has this badge'}), 409
        
        # Award badge
        student_badge = StudentBadge(
            student_id=data['student_id'],
            badge_id=data['badge_id'],
            awarded_by_id=get_jwt_identity()
        )
        
        db.session.add(student_badge)
        
        # Add points transaction
        badge = Badge.query.get(data['badge_id'])
        if badge and badge.points > 0:
            transaction = PointTransaction(
                student_id=data['student_id'],
                points=badge.points,
                reason=f"Awarded badge: {badge.name}",
                category='badge',
                reference_type='badge',
                reference_id=badge.id,
                awarded_by_id=get_jwt_identity()
            )
            db.session.add(transaction)
        
        db.session.commit()
        
        return jsonify({'message': 'Badge awarded successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error awarding badge: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@gamification_bp.route('/student/<int:student_id>/badges', methods=['GET'])
@jwt_required()
@student_access_required
def get_student_badges(student_id):
    """Get all badges earned by a student"""
    try:
        student_badges = StudentBadge.query.filter_by(student_id=student_id).all()
        
        result = []
        for sb in student_badges:
            result.append({
                'badge': {
                    'id': sb.badge.id,
                    'name': sb.badge.name,
                    'description': sb.badge.description,
                    'category': sb.badge.category,
                    'points': sb.badge.points,
                    'icon_path': sb.badge.icon_path
                },
                'earned_date': sb.earned_date.isoformat(),
                'awarded_by': sb.awarded_by.name if sb.awarded_by else None
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error fetching student badges: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@gamification_bp.route('/leaderboard/create', methods=['POST'])
@jwt_required()
@role_required(['admin', 'teacher'])
def create_leaderboard():
    """Create a new leaderboard"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'category']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        leaderboard = Leaderboard(
            name=data['name'],
            category=data['category'],
            term_id=data.get('term_id'),
            department_id=data.get('department_id')
        )
        
        db.session.add(leaderboard)
        db.session.commit()
        
        return jsonify({
            'message': 'Leaderboard created successfully',
            'leaderboard_id': leaderboard.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating leaderboard: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@gamification_bp.route('/leaderboard/<int:leaderboard_id>/rankings', methods=['GET'])
@jwt_required()
def get_leaderboard_rankings(leaderboard_id):
    """Get rankings for a leaderboard"""
    try:
        rankings = LeaderboardRanking.query\
            .filter_by(leaderboard_id=leaderboard_id)\
            .order_by(LeaderboardRanking.points.desc())\
            .all()
        
        result = []
        for rank, ranking in enumerate(rankings, 1):
            result.append({
                'rank': rank,
                'student': {
                    'id': ranking.student.id,
                    'name': ranking.student.user.name,
                    'roll_number': ranking.student.roll_number
                },
                'points': ranking.points,
                'last_updated': ranking.last_calculated.isoformat()
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error fetching leaderboard rankings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@gamification_bp.route('/rewards', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def create_reward():
    """Create a new reward"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'description', 'points_required']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        reward = Reward(
            name=data['name'],
            description=data['description'],
            points_required=data['points_required'],
            quantity_available=data.get('quantity_available', -1),
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() \
                if 'expiry_date' in data else None
        )
        
        db.session.add(reward)
        db.session.commit()
        
        return jsonify({
            'message': 'Reward created successfully',
            'reward_id': reward.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating reward: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@gamification_bp.route('/rewards/redeem', methods=['POST'])
@jwt_required()
def redeem_reward():
    """Redeem a reward"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(field in data for field in ['reward_id']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        user_id = get_jwt_identity()
        student = Student.query.filter_by(user_id=user_id).first()
        
        if not student:
            return jsonify({'error': 'Only students can redeem rewards'}), 403
        
        reward = Reward.query.get(data['reward_id'])
        if not reward:
            return jsonify({'error': 'Reward not found'}), 404
        
        if not reward.is_active:
            return jsonify({'error': 'Reward is not active'}), 400
        
        if reward.expiry_date and reward.expiry_date < datetime.now().date():
            return jsonify({'error': 'Reward has expired'}), 400
        
        if reward.quantity_available == 0:
            return jsonify({'error': 'Reward is out of stock'}), 400
        
        # Check if student has enough points
        total_points = db.session.query(db.func.sum(PointTransaction.points))\
            .filter_by(student_id=student.id).scalar() or 0
        
        if total_points < reward.points_required:
            return jsonify({'error': 'Insufficient points'}), 400
        
        # Create redemption record
        redemption = RewardRedemption(
            reward_id=reward.id,
            student_id=student.id,
            points_spent=reward.points_required,
            status='pending'
        )
        
        db.session.add(redemption)
        
        # Deduct points
        transaction = PointTransaction(
            student_id=student.id,
            points=-reward.points_required,
            reason=f"Redeemed reward: {reward.name}",
            category='reward_redemption',
            reference_type='reward',
            reference_id=reward.id
        )
        
        db.session.add(transaction)
        
        # Update reward quantity
        if reward.quantity_available > 0:
            reward.quantity_available -= 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Reward redeemed successfully',
            'redemption_id': redemption.id
        }), 200
        
    except Exception as e:
        logger.error(f"Error redeeming reward: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@gamification_bp.route('/student/<int:student_id>/points', methods=['GET'])
@jwt_required()
@student_access_required
def get_student_points(student_id):
    """Get point transactions and total points for a student"""
    try:
        transactions = PointTransaction.query\
            .filter_by(student_id=student_id)\
            .order_by(PointTransaction.created_at.desc())\
            .all()
        
        total_points = sum(t.points for t in transactions)
        
        result = {
            'total_points': total_points,
            'transactions': [{
                'id': t.id,
                'points': t.points,
                'reason': t.reason,
                'category': t.category,
                'awarded_by': t.awarded_by.name if t.awarded_by else None,
                'created_at': t.created_at.isoformat()
            } for t in transactions]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error fetching student points: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500