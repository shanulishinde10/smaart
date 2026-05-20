from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

professor_courses = db.Table('professor_courses',
    db.Column('professor_id', db.Integer, db.ForeignKey('professors.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True)
)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin | professor | student
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
        }


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'code': self.code}


class Professor(db.Model):
    __tablename__ = 'professors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)

    user = db.relationship('User', backref=db.backref('professor_profile', uselist=False))
    courses = db.relationship('Course', secondary=professor_courses, lazy='subquery',
                              backref=db.backref('professors', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'employee_id': self.employee_id,
            'email': self.user.email if self.user else None,
            'username': self.user.username if self.user else None,
            'courses': [c.to_dict() for c in self.courses],
        }


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    face_encoding = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    course = db.relationship('Course')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'roll_no': self.roll_no,
            'course': self.course.to_dict() if self.course else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Lecture(db.Model):
    __tablename__ = 'lectures'
    id = db.Column(db.Integer, primary_key=True)
    professor_id = db.Column(db.Integer, db.ForeignKey('professors.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    professor = db.relationship('Professor')
    course = db.relationship('Course')

    def to_dict(self):
        return {
            'id': self.id,
            'professor_id': self.professor_id,
            'professor_name': self.professor.name if self.professor else None,
            'course_id': self.course_id,
            'course': self.course.to_dict() if self.course else None,
            'title': self.title or (f"{self.course.name} Lecture" if self.course else 'Lecture'),
            'date': self.date.isoformat() if self.date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    lecture_id = db.Column(db.Integer, db.ForeignKey('lectures.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    scan_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending | present | absent
    reviewed_at = db.Column(db.DateTime)

    student = db.relationship('Student')
    lecture = db.relationship('Lecture')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'student_roll_no': self.student.roll_no if self.student else None,
            'lecture_id': self.lecture_id,
            'lecture': self.lecture.to_dict() if self.lecture else None,
            'date': self.date.isoformat() if self.date else None,
            'scan_time': self.scan_time.isoformat() if self.scan_time else None,
            'status': self.status,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
