from app import db
from datetime import datetime

class Badge(db.Model):
    """Model for storing achievement badges"""
    __tablename__ = 'badges'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon_path = db.Column(db.String(255))
    category = db.Column(db.String(50))  # academic, attendance, participation, etc.
    points = db.Column(db.Integer, default=0)
    criteria = db.Column(db.JSON)  # Requirements to earn the badge
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student_badges = db.relationship('StudentBadge', back_populates='badge')

    def __repr__(self):
        return f'<Badge {self.name}>'

class StudentBadge(db.Model):
    """Model for tracking badges earned by students"""
    __tablename__ = 'student_badges'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    earned_date = db.Column(db.DateTime, default=datetime.utcnow)
    awarded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student')
    badge = db.relationship('Badge', back_populates='student_badges')
    awarded_by = db.relationship('User')

    def __repr__(self):
        return f'<StudentBadge {self.student_id}-{self.badge_id}>'

class Leaderboard(db.Model):
    """Model for managing leaderboards"""
    __tablename__ = 'leaderboards'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # academic, attendance, overall
    term_id = db.Column(db.Integer, db.ForeignKey('terms.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    term = db.relationship('Term')
    department = db.relationship('Department')
    rankings = db.relationship('LeaderboardRanking', back_populates='leaderboard')

    def __repr__(self):
        return f'<Leaderboard {self.name}>'

class LeaderboardRanking(db.Model):
    """Model for storing student rankings in leaderboards"""
    __tablename__ = 'leaderboard_rankings'

    id = db.Column(db.Integer, primary_key=True)
    leaderboard_id = db.Column(db.Integer, db.ForeignKey('leaderboards.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    points = db.Column(db.Integer, default=0)
    rank = db.Column(db.Integer)
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    leaderboard = db.relationship('Leaderboard', back_populates='rankings')
    student = db.relationship('Student')

    def __repr__(self):
        return f'<LeaderboardRanking {self.leaderboard_id}-{self.student_id}>'

class PointTransaction(db.Model):
    """Model for tracking point transactions"""
    __tablename__ = 'point_transactions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)  # Can be positive or negative
    reason = db.Column(db.String(255))
    category = db.Column(db.String(50))  # attendance, assignment, participation
    reference_type = db.Column(db.String(50))  # The type of entity that generated points
    reference_id = db.Column(db.Integer)  # ID of the referenced entity
    awarded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student')
    awarded_by = db.relationship('User')

    def __repr__(self):
        return f'<PointTransaction {self.student_id}-{self.points}>'

class Reward(db.Model):
    """Model for storing redeemable rewards"""
    __tablename__ = 'rewards'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    points_required = db.Column(db.Integer, nullable=False)
    quantity_available = db.Column(db.Integer, default=-1)  # -1 for unlimited
    is_active = db.Column(db.Boolean, default=True)
    expiry_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    redemptions = db.relationship('RewardRedemption', back_populates='reward')

    def __repr__(self):
        return f'<Reward {self.name}>'

class RewardRedemption(db.Model):
    """Model for tracking reward redemptions"""
    __tablename__ = 'reward_redemptions'

    id = db.Column(db.Integer, primary_key=True)
    reward_id = db.Column(db.Integer, db.ForeignKey('rewards.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    points_spent = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20))  # pending, approved, rejected, completed
    redeemed_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reward = db.relationship('Reward', back_populates='redemptions')
    student = db.relationship('Student')
    processed_by = db.relationship('User')

    def __repr__(self):
        return f'<RewardRedemption {self.reward_id}-{self.student_id}>'