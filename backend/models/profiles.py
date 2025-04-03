from app import db
from datetime import datetime

class Student(db.Model):
    """Student profile model"""
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    roll_number = db.Column(db.String(50), unique=True)
    date_of_birth = db.Column(db.Date)
    admission_date = db.Column(db.Date)
    current_year = db.Column(db.Integer)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='student_profile')
    department = db.relationship('Department')
    enrollments = db.relationship('Enrollment', back_populates='student')
    parents = db.relationship('Parent', secondary='student_parent_association')
    achievements = db.relationship('Achievement', back_populates='student')

    def __repr__(self):
        return f'<Student {self.roll_number}>'

class Teacher(db.Model):
    """Teacher profile model"""
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    employee_id = db.Column(db.String(50), unique=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    designation = db.Column(db.String(100))
    joining_date = db.Column(db.Date)
    specialization = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='teacher_profile')
    department = db.relationship('Department', back_populates='teachers')
    courses_taught = db.relationship('Course', secondary='teacher_course_association')

    def __repr__(self):
        return f'<Teacher {self.employee_id}>'

class Parent(db.Model):
    """Parent profile model"""
    __tablename__ = 'parents'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    occupation = db.Column(db.String(100))
    relationship = db.Column(db.String(50))  # father, mother, guardian
    alternate_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='parent_profile')
    students = db.relationship('Student', secondary='student_parent_association')

    def __repr__(self):
        return f'<Parent {self.user_id}>'

# Association Tables
student_parent_association = db.Table('student_parent_association',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id'), primary_key=True),
    db.Column('parent_id', db.Integer, db.ForeignKey('parents.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

teacher_course_association = db.Table('teacher_course_association',
    db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class Achievement(db.Model):
    """Student achievements model"""
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    achievement_date = db.Column(db.Date)
    category = db.Column(db.String(50))  # academic, sports, extracurricular
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', back_populates='achievements')

    def __repr__(self):
        return f'<Achievement {self.title}>'