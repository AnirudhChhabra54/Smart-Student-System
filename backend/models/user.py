from app import db
from datetime import datetime

class User(db.Model):
    """User model for storing user related details"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student, parent
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)

    # Relationships
    institution = db.relationship('Institution', back_populates='users')
    student_profile = db.relationship('Student', back_populates='user', uselist=False)
    teacher_profile = db.relationship('Teacher', back_populates='user', uselist=False)
    parent_profile = db.relationship('Parent', back_populates='user', uselist=False)

    def __init__(self, email, password, name, role):
        self.email = email
        self.password = password
        self.name = name
        self.role = role

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'institution_id': self.institution_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def update_last_login(self):
        """Update user's last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()