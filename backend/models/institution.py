from app import db
from datetime import datetime

class Institution(db.Model):
    """Institution model for storing educational institution details"""
    __tablename__ = 'institutions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # school, college, university
    address = db.Column(db.Text)
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    website = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    users = db.relationship('User', back_populates='institution')
    departments = db.relationship('Department', back_populates='institution')
    courses = db.relationship('Course', back_populates='institution')
    academic_years = db.relationship('AcademicYear', back_populates='institution')

    def __init__(self, name, code, type, address=None, contact_email=None, 
                 contact_phone=None, website=None):
        self.name = name
        self.code = code
        self.type = type
        self.address = address
        self.contact_email = contact_email
        self.contact_phone = contact_phone
        self.website = website

    def __repr__(self):
        return f'<Institution {self.name}>'

    def to_dict(self):
        """Convert institution object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'type': self.type,
            'address': self.address,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'website': self.website,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

    @staticmethod
    def get_active_institutions():
        """Get all active institutions"""
        return Institution.query.filter_by(is_active=True).all()

    def deactivate(self):
        """Deactivate institution"""
        self.is_active = False
        db.session.commit()

    def activate(self):
        """Activate institution"""
        self.is_active = True
        db.session.commit()