from app import db
from datetime import datetime

class Department(db.Model):
    """Department model for storing department details"""
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    head_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    institution = db.relationship('Institution', back_populates='departments')
    head = db.relationship('User')
    courses = db.relationship('Course', back_populates='department')
    teachers = db.relationship('Teacher', back_populates='department')

    def __repr__(self):
        return f'<Department {self.name}>'

class Course(db.Model):
    """Course model for storing course details"""
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    credits = db.Column(db.Integer)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    department = db.relationship('Department', back_populates='courses')
    institution = db.relationship('Institution', back_populates='courses')
    assignments = db.relationship('Assignment', back_populates='course')
    enrollments = db.relationship('Enrollment', back_populates='course')

    def __repr__(self):
        return f'<Course {self.name}>'

class AcademicYear(db.Model):
    """Academic Year model for storing academic calendar details"""
    __tablename__ = 'academic_years'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    institution = db.relationship('Institution', back_populates='academic_years')
    terms = db.relationship('Term', back_populates='academic_year')

    def __repr__(self):
        return f'<AcademicYear {self.name}>'

class Term(db.Model):
    """Term model for storing term/semester details"""
    __tablename__ = 'terms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    academic_year_id = db.Column(db.Integer, db.ForeignKey('academic_years.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    academic_year = db.relationship('AcademicYear', back_populates='terms')
    enrollments = db.relationship('Enrollment', back_populates='term')

    def __repr__(self):
        return f'<Term {self.name}>'

class Enrollment(db.Model):
    """Enrollment model for storing student course enrollments"""
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey('terms.id'), nullable=False)
    status = db.Column(db.String(20), default='enrolled')  # enrolled, completed, dropped
    grade = db.Column(db.String(2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')
    term = db.relationship('Term', back_populates='enrollments')
    attendance_records = db.relationship('AttendanceRecord', back_populates='enrollment')

    def __repr__(self):
        return f'<Enrollment {self.student_id}-{self.course_id}>'