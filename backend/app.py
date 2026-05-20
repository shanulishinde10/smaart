import os
import uuid
from datetime import datetime, date, timedelta
from functools import wraps

import jwt
from flask import Flask, request, jsonify
from flask_cors import CORS

from models import (
    db, User, Course, Professor, Student,
    Lecture, AttendanceRecord
)
from face_utils import (
    load_image_from_base64,
    get_face_encoding, compare_faces,
    encode_face_encoding, decode_face_encoding
)
from s3_utils import upload_face, delete_face

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "attendance.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

JWT_SECRET = os.environ.get('JWT_SECRET', 'scanora-secret-key-2024-change-in-prod')

db.init_app(app)


# ── Helpers ────────────────────────────────────────────────────────────

def create_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def require_auth(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
            if not token:
                return jsonify({'error': 'Authentication required'}), 401
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                request.user_id = payload['user_id']
                request.user_role = payload['role']
                if roles and payload['role'] not in roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_professor(user_id):
    return Professor.query.filter_by(user_id=user_id).first()


# ── DB init & seed ─────────────────────────────────────────────────────

with app.app_context():
    from sqlalchemy import inspect as sa_inspect
    existing = sa_inspect(db.engine).get_table_names()
    if 'users' not in existing:
        db.drop_all()
    db.create_all()

    if not User.query.filter_by(role='admin').first():
        admin = User(username='admin', email='admin@scanora.edu', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        for name, code in [
            ('Bachelor of Technology', 'BTECH'),
            ('Master of Business Administration', 'MBA'),
            ('Master of Technology', 'MTECH'),
            ('Master of Science', 'MSC'),
            ('Master of Computer Science', 'MCS'),
            ('Bachelor of Computer Applications', 'BCA'),
            ('Master of Computer Applications', 'MCA'),
        ]:
            db.session.add(Course(name=name, code=code))

        db.session.commit()


# ── Auth ───────────────────────────────────────────────────────────────

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_token(user.id, user.role)
    resp = {'token': token, 'user': user.to_dict()}

    if user.role == 'professor' and user.professor_profile:
        resp['professor'] = user.professor_profile.to_dict()
    elif user.role == 'student' and user.student_profile:
        resp['student'] = user.student_profile.to_dict()

    return jsonify(resp)


@app.route('/api/auth/me', methods=['GET'])
@require_auth()
def get_me():
    user = db.session.get(User, request.user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    resp = {'user': user.to_dict()}
    if user.role == 'professor' and user.professor_profile:
        resp['professor'] = user.professor_profile.to_dict()
    elif user.role == 'student' and user.student_profile:
        resp['student'] = user.student_profile.to_dict()
    return jsonify(resp)


# ── Courses (public) ───────────────────────────────────────────────────

@app.route('/api/courses', methods=['GET'])
def get_courses():
    courses = Course.query.order_by(Course.name).all()
    return jsonify({'courses': [c.to_dict() for c in courses]})


# ── Student self-registration ──────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register_student():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    roll_no = request.form.get('roll_no', '').strip()
    course_id = request.form.get('course_id', '').strip()
    password = request.form.get('password', '').strip()

    if not all([name, email, roll_no, course_id, password]):
        return jsonify({'error': 'All fields are required'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    if User.query.filter((User.email == email) | (User.username == roll_no)).first():
        return jsonify({'error': 'Email or Roll No already registered'}), 409
    if Student.query.filter_by(roll_no=roll_no).first():
        return jsonify({'error': 'Roll No already registered'}), 409

    course = db.session.get(Course, int(course_id))
    if not course:
        return jsonify({'error': 'Invalid course selected'}), 400

    if 'image' not in request.files:
        return jsonify({'error': 'Face image is required'}), 400

    file = request.files['image']
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'
    filename = f"{uuid.uuid4().hex}.{ext}"

    import cv2
    import numpy as np
    file_bytes = file.read()
    img_array = np.frombuffer(file_bytes, np.uint8)
    image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    encoding = get_face_encoding(image)
    if encoding is None:
        return jsonify({'error': 'No face detected. Please retake the photo.'}), 400

    s3_key = f"faces/{filename}"
    upload_face(file_bytes, s3_key)

    user = User(username=roll_no, email=email, role='student')
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    student = Student(
        user_id=user.id,
        name=name,
        email=email,
        roll_no=roll_no,
        course_id=int(course_id),
        image_path=s3_key,
        face_encoding=encode_face_encoding(encoding),
    )
    db.session.add(student)
    db.session.commit()

    token = create_token(user.id, 'student')
    return jsonify({
        'message': 'Registration successful',
        'token': token,
        'user': user.to_dict(),
        'student': student.to_dict(),
    }), 201


# ── Face scan (public — recognition identifies student) ─────────────────

@app.route('/api/scan', methods=['POST'])
def face_scan():
    data = request.get_json() or {}
    if 'image' not in data:
        return jsonify({'error': 'Image data is required'}), 400

    lecture_id = data.get('lecture_id')
    if not lecture_id:
        return jsonify({'error': 'lecture_id is required'}), 400

    lecture = db.session.get(Lecture, int(lecture_id))
    if not lecture:
        return jsonify({'error': 'Lecture not found'}), 404

    image = load_image_from_base64(data['image'])
    target_enc = get_face_encoding(image)
    if target_enc is None:
        return jsonify({'status': 'unknown', 'message': 'No face detected'}), 200

    students = Student.query.filter_by(course_id=lecture.course_id).all()
    if not students:
        return jsonify({'status': 'unknown', 'message': 'No students enrolled in this course'}), 200

    known = [decode_face_encoding(s.face_encoding) for s in students]
    matched, idx, _ = compare_faces(known, target_enc)

    if not matched:
        return jsonify({'status': 'unknown', 'message': 'Face not recognized'}), 200

    student = students[idx]
    existing = AttendanceRecord.query.filter_by(
        student_id=student.id, lecture_id=lecture.id
    ).first()

    if existing:
        return jsonify({
            'status': 'already_submitted',
            'message': f'{student.name} already submitted for this lecture',
            'name': student.name,
            'roll_no': student.roll_no,
            'attendance_status': existing.status,
        }), 200

    record = AttendanceRecord(
        student_id=student.id,
        lecture_id=lecture.id,
        date=date.today(),
        scan_time=datetime.now(),
        status='pending',
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Attendance submitted — awaiting professor review',
        'name': student.name,
        'roll_no': student.roll_no,
        'time': datetime.now().strftime('%H:%M:%S'),
    }), 200


# ── Admin ──────────────────────────────────────────────────────────────

@app.route('/api/admin/stats', methods=['GET'])
@require_auth(['admin'])
def admin_stats():
    today = date.today()
    return jsonify({
        'total_students': Student.query.count(),
        'total_professors': Professor.query.count(),
        'total_courses': Course.query.count(),
        'lectures_today': Lecture.query.filter_by(date=today).count(),
        'pending_attendance': AttendanceRecord.query.filter_by(status='pending').count(),
        'present_today': AttendanceRecord.query.filter_by(date=today, status='present').count(),
    })


@app.route('/api/admin/professors', methods=['GET'])
@require_auth(['admin'])
def admin_get_professors():
    return jsonify({'professors': [p.to_dict() for p in Professor.query.all()]})


@app.route('/api/admin/professors', methods=['POST'])
@require_auth(['admin'])
def admin_add_professor():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    employee_id = data.get('employee_id', '').strip()
    email = data.get('email', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    course_ids = data.get('course_ids', [])

    if not all([name, employee_id, email, username, password]):
        return jsonify({'error': 'All fields are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409
    if Professor.query.filter_by(employee_id=employee_id).first():
        return jsonify({'error': 'Employee ID already exists'}), 409

    user = User(username=username, email=email, role='professor')
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    professor = Professor(user_id=user.id, name=name, employee_id=employee_id)
    if course_ids:
        professor.courses = Course.query.filter(Course.id.in_(course_ids)).all()
    db.session.add(professor)
    db.session.commit()

    return jsonify({'message': 'Professor added', 'professor': professor.to_dict()}), 201


@app.route('/api/admin/professors/<int:pid>', methods=['DELETE'])
@require_auth(['admin'])
def admin_delete_professor(pid):
    professor = db.session.get(Professor, pid)
    if not professor:
        return jsonify({'error': 'Not found'}), 404
    user = professor.user
    db.session.delete(professor)
    if user:
        db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Professor removed'})


@app.route('/api/admin/professors/<int:pid>/courses', methods=['PUT'])
@require_auth(['admin'])
def admin_update_professor_courses(pid):
    professor = db.session.get(Professor, pid)
    if not professor:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json() or {}
    course_ids = data.get('course_ids', [])
    professor.courses = Course.query.filter(Course.id.in_(course_ids)).all()
    db.session.commit()
    return jsonify({'professor': professor.to_dict()})


@app.route('/api/admin/students', methods=['GET'])
@require_auth(['admin'])
def admin_get_students():
    students = Student.query.order_by(Student.name).all()
    return jsonify({'students': [s.to_dict() for s in students]})


@app.route('/api/admin/students/<int:sid>', methods=['DELETE'])
@require_auth(['admin'])
def admin_delete_student(sid):
    student = db.session.get(Student, sid)
    if not student:
        return jsonify({'error': 'Not found'}), 404
    user = student.user
    if student.image_path:
        delete_face(student.image_path)
    db.session.delete(student)
    if user:
        db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Student removed'})


@app.route('/api/admin/lectures', methods=['GET'])
@require_auth(['admin'])
def admin_get_lectures():
    date_param = request.args.get('date')
    q = Lecture.query
    if date_param:
        try:
            q = q.filter_by(date=date.fromisoformat(date_param))
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    lectures = q.order_by(Lecture.date.desc()).all()
    return jsonify({'lectures': [l.to_dict() for l in lectures]})


@app.route('/api/admin/attendance', methods=['GET'])
@require_auth(['admin'])
def admin_get_attendance():
    date_param = request.args.get('date')
    status_param = request.args.get('status')
    q = AttendanceRecord.query
    if date_param:
        try:
            q = q.filter_by(date=date.fromisoformat(date_param))
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    if status_param:
        q = q.filter_by(status=status_param)
    records = q.order_by(AttendanceRecord.date.desc(), AttendanceRecord.scan_time.desc()).all()
    return jsonify({'records': [r.to_dict() for r in records]})


@app.route('/api/admin/attendance', methods=['POST'])
@require_auth(['admin'])
def admin_mark_attendance():
    data = request.get_json() or {}
    student_id = data.get('student_id')
    lecture_id = data.get('lecture_id')
    status = data.get('status', 'present')

    if not all([student_id, lecture_id]):
        return jsonify({'error': 'student_id and lecture_id are required'}), 400

    existing = AttendanceRecord.query.filter_by(
        student_id=student_id, lecture_id=lecture_id
    ).first()

    if existing:
        existing.status = status
        existing.reviewed_at = datetime.now()
    else:
        db.session.add(AttendanceRecord(
            student_id=student_id,
            lecture_id=lecture_id,
            date=date.today(),
            scan_time=datetime.now(),
            status=status,
            reviewed_at=datetime.now(),
        ))
    db.session.commit()
    return jsonify({'message': 'Attendance marked'})


@app.route('/api/admin/attendance/<int:rid>', methods=['PUT'])
@require_auth(['admin'])
def admin_update_attendance(rid):
    record = db.session.get(AttendanceRecord, rid)
    if not record:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json() or {}
    if 'status' in data:
        record.status = data['status']
        record.reviewed_at = datetime.now()
    db.session.commit()
    return jsonify({'record': record.to_dict()})


@app.route('/api/admin/attendance/<int:rid>', methods=['DELETE'])
@require_auth(['admin'])
def admin_delete_attendance(rid):
    record = db.session.get(AttendanceRecord, rid)
    if not record:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(record)
    db.session.commit()
    return jsonify({'message': 'Record removed'})


# ── Professor ──────────────────────────────────────────────────────────

@app.route('/api/professor/lectures', methods=['POST'])
@require_auth(['professor'])
def create_lecture():
    professor = get_professor(request.user_id)
    if not professor:
        return jsonify({'error': 'Professor profile not found'}), 404

    data = request.get_json() or {}
    course_id = data.get('course_id')
    title = data.get('title', '').strip()
    lecture_date = data.get('date', date.today().isoformat())

    if not course_id:
        return jsonify({'error': 'Course is required'}), 400

    course = db.session.get(Course, int(course_id))
    if not course or course not in professor.courses:
        return jsonify({'error': 'You are not assigned to this course'}), 403

    try:
        lecture_date = date.fromisoformat(lecture_date)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    lecture = Lecture(
        professor_id=professor.id,
        course_id=int(course_id),
        title=title or f"{course.name} Lecture",
        date=lecture_date,
    )
    db.session.add(lecture)
    db.session.commit()
    return jsonify({'message': 'Lecture created', 'lecture': lecture.to_dict()}), 201


@app.route('/api/professor/lectures', methods=['GET'])
@require_auth(['professor'])
def professor_get_lectures():
    professor = get_professor(request.user_id)
    if not professor:
        return jsonify({'error': 'Professor profile not found'}), 404

    date_param = request.args.get('date', date.today().isoformat())
    try:
        filter_date = date.fromisoformat(date_param)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    lectures = Lecture.query.filter_by(
        professor_id=professor.id, date=filter_date
    ).all()
    return jsonify({'lectures': [l.to_dict() for l in lectures]})


@app.route('/api/professor/lectures/<int:lid>/attendance', methods=['GET'])
@require_auth(['professor'])
def professor_lecture_attendance(lid):
    professor = get_professor(request.user_id)
    lecture = db.session.get(Lecture, lid)
    if not lecture:
        return jsonify({'error': 'Lecture not found'}), 404
    if lecture.professor_id != professor.id:
        return jsonify({'error': 'Not authorized'}), 403

    records = AttendanceRecord.query.filter_by(lecture_id=lid).all()
    return jsonify({'records': [r.to_dict() for r in records], 'lecture': lecture.to_dict()})


@app.route('/api/professor/attendance/<int:rid>', methods=['PUT'])
@require_auth(['professor'])
def professor_review_attendance(rid):
    professor = get_professor(request.user_id)
    record = db.session.get(AttendanceRecord, rid)
    if not record:
        return jsonify({'error': 'Not found'}), 404
    if record.lecture.professor_id != professor.id:
        return jsonify({'error': 'Not authorized'}), 403

    data = request.get_json() or {}
    status = data.get('status')
    if status not in ('present', 'absent'):
        return jsonify({'error': 'Status must be present or absent'}), 400

    record.status = status
    record.reviewed_at = datetime.now()
    db.session.commit()
    return jsonify({'record': record.to_dict()})


@app.route('/api/professor/stats', methods=['GET'])
@require_auth(['professor'])
def professor_stats():
    professor = get_professor(request.user_id)
    if not professor:
        return jsonify({'error': 'Professor profile not found'}), 404

    today = date.today()
    today_lectures = Lecture.query.filter_by(professor_id=professor.id, date=today).all()

    pending_count = sum(
        AttendanceRecord.query.filter_by(lecture_id=lec.id, status='pending').count()
        for lec in today_lectures
    )

    course_ids = [c.id for c in professor.courses]
    student_count = Student.query.filter(Student.course_id.in_(course_ids)).count() if course_ids else 0

    return jsonify({
        'today_lectures': len(today_lectures),
        'pending_reviews': pending_count,
        'total_courses': len(professor.courses),
        'total_students': student_count,
    })


# ── Student ────────────────────────────────────────────────────────────

@app.route('/api/student/lectures', methods=['GET'])
@require_auth(['student'])
def student_get_lectures():
    user = db.session.get(User, request.user_id)
    student = user.student_profile if user else None
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404

    today = date.today()
    lectures = Lecture.query.filter_by(course_id=student.course_id, date=today).all()
    return jsonify({'lectures': [l.to_dict() for l in lectures]})


@app.route('/api/student/attendance', methods=['GET'])
@require_auth(['student'])
def student_get_attendance():
    user = db.session.get(User, request.user_id)
    student = user.student_profile if user else None
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404

    records = AttendanceRecord.query.filter_by(student_id=student.id).order_by(
        AttendanceRecord.date.desc()
    ).all()
    return jsonify({'records': [r.to_dict() for r in records]})


# ── Public lectures for scanner (no auth — students pick their lecture) ─

@app.route('/api/lectures/today', methods=['GET'])
def get_today_lectures():
    course_id = request.args.get('course_id')
    today = date.today()
    q = Lecture.query.filter_by(date=today)
    if course_id:
        q = q.filter_by(course_id=int(course_id))
    lectures = q.all()
    return jsonify({'lectures': [l.to_dict() for l in lectures]})


# ── Admin Stats Trends ────────────────────────────────────────────────

@app.route('/api/admin/stats/trends', methods=['GET'])
@require_auth(['admin'])
def admin_stats_trends():
    days = int(request.args.get('days', 7))
    today = date.today()
    result = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        result.append({
            'date': d.isoformat(),
            'present': AttendanceRecord.query.filter_by(date=d, status='present').count(),
            'absent': AttendanceRecord.query.filter_by(date=d, status='absent').count(),
            'pending': AttendanceRecord.query.filter_by(date=d, status='pending').count(),
        })
    return jsonify({'trends': result})


# ── Legacy compat ──────────────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def get_stats_compat():
    today = date.today()
    return jsonify({
        'total_students': Student.query.count(),
        'present_today': AttendanceRecord.query.filter_by(date=today, status='present').count(),
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
