from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    face_encoding = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'roll_no': self.roll_no,
            'department': self.department,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    time = db.Column(db.Time, default=datetime.now().time, nullable=False)
    status = db.Column(db.String(20), default='present')

    student = db.relationship('Student', backref=db.backref('attendance_records', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.student.name if self.student else 'Unknown',
            'roll_no': self.student.roll_no if self.student else 'N/A',
            'department': self.student.department if self.student else 'N/A',
            'date': self.date.isoformat() if self.date else None,
            'time': self.time.strftime('%H:%M:%S') if self.time else None,
            'status': self.status
        }