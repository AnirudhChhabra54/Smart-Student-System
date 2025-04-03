from app import db
from datetime import datetime

class AttendanceRecord(db.Model):
    """Model for tracking student attendance"""
    __tablename__ = 'attendance_records'

    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late
    remarks = db.Column(db.String(255))
    marked_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    enrollment = db.relationship('Enrollment', back_populates='attendance_records')
    marked_by = db.relationship('User')

    def __repr__(self):
        return f'<AttendanceRecord {self.enrollment_id}-{self.date}>'

class Marksheet(db.Model):
    """Model for storing marksheet information"""
    __tablename__ = 'marksheets'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey('terms.id'), nullable=False)
    total_marks = db.Column(db.Float)
    percentage = db.Column(db.Float)
    grade = db.Column(db.String(2))
    remarks = db.Column(db.Text)
    scanned_copy_path = db.Column(db.String(255))
    verified = db.Column(db.Boolean, default=False)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student')
    term = db.relationship('Term')
    verified_by = db.relationship('User')
    subject_marks = db.relationship('SubjectMark', back_populates='marksheet')

    def __repr__(self):
        return f'<Marksheet {self.student_id}-{self.term_id}>'

    def calculate_total(self):
        """Calculate total marks and percentage"""
        total = sum(mark.marks_obtained for mark in self.subject_marks)
        max_total = sum(mark.max_marks for mark in self.subject_marks)
        
        self.total_marks = total
        self.percentage = (total / max_total * 100) if max_total > 0 else 0
        
        # Calculate grade based on percentage
        if self.percentage >= 90:
            self.grade = 'A+'
        elif self.percentage >= 80:
            self.grade = 'A'
        elif self.percentage >= 70:
            self.grade = 'B'
        elif self.percentage >= 60:
            self.grade = 'C'
        elif self.percentage >= 50:
            self.grade = 'D'
        else:
            self.grade = 'F'

class SubjectMark(db.Model):
    """Model for storing subject-wise marks in a marksheet"""
    __tablename__ = 'subject_marks'

    id = db.Column(db.Integer, primary_key=True)
    marksheet_id = db.Column(db.Integer, db.ForeignKey('marksheets.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    marksheet = db.relationship('Marksheet', back_populates='subject_marks')
    course = db.relationship('Course')

    def __repr__(self):
        return f'<SubjectMark {self.marksheet_id}-{self.course_id}>'

class PerformancePrediction(db.Model):
    """Model for storing AI-generated performance predictions"""
    __tablename__ = 'performance_predictions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    predicted_grade = db.Column(db.String(2))
    confidence_score = db.Column(db.Float)  # 0 to 1
    factors = db.Column(db.JSON)  # Store factors affecting prediction
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student')
    course = db.relationship('Course')

    def __repr__(self):
        return f'<PerformancePrediction {self.student_id}-{self.course_id}>'