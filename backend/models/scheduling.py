from app import db
from datetime import datetime

class Timetable(db.Model):
    """Model for storing class timetables"""
    __tablename__ = 'timetables'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey('terms.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    generated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = db.relationship('Department')
    term = db.relationship('Term')
    generated_by = db.relationship('User')
    slots = db.relationship('TimeSlot', back_populates='timetable')

    def __repr__(self):
        return f'<Timetable {self.name}>'

class TimeSlot(db.Model):
    """Model for storing individual time slots in a timetable"""
    __tablename__ = 'time_slots'

    id = db.Column(db.Integer, primary_key=True)
    timetable_id = db.Column(db.Integer, db.ForeignKey('timetables.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room_number = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    timetable = db.relationship('Timetable', back_populates='slots')
    course = db.relationship('Course')
    teacher = db.relationship('Teacher')

    def __repr__(self):
        return f'<TimeSlot {self.day_of_week}-{self.start_time}>'

class Notification(db.Model):
    """Model for storing system notifications"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))  # announcement, reminder, alert, etc.
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User')

    def __repr__(self):
        return f'<Notification {self.id}>'

    def mark_as_read(self):
        """Mark notification as read"""
        self.read = True
        self.read_at = datetime.utcnow()
        db.session.commit()

class Assignment(db.Model):
    """Model for storing course assignments"""
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=False)
    max_marks = db.Column(db.Float)
    weight_percentage = db.Column(db.Float)  # Percentage weight in final grade
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = db.relationship('Course', back_populates='assignments')
    created_by = db.relationship('User')
    submissions = db.relationship('AssignmentSubmission', back_populates='assignment')

    def __repr__(self):
        return f'<Assignment {self.title}>'

class AssignmentSubmission(db.Model):
    """Model for storing assignment submissions"""
    __tablename__ = 'assignment_submissions'

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(255))
    marks_obtained = db.Column(db.Float)
    remarks = db.Column(db.Text)
    status = db.Column(db.String(20))  # submitted, graded, late
    graded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    graded_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignment = db.relationship('Assignment', back_populates='submissions')
    student = db.relationship('Student')
    graded_by = db.relationship('User')

    def __repr__(self):
        return f'<AssignmentSubmission {self.assignment_id}-{self.student_id}>'