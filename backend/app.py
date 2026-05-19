import os
import uuid
from datetime import date, datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Student, Attendance
from face_utils import (
    load_image_from_base64, save_uploaded_image,
    get_face_encoding, compare_faces,
    encode_face_encoding, decode_face_encoding
)

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "attendance.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads', 'faces')
app.config['TEMP_FOLDER'] = os.path.join(BASE_DIR, 'uploads', 'temp')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/api/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    roll_no = request.form.get('roll_no')
    department = request.form.get('department')

    if not all([name, email, roll_no, department]):
        return jsonify({'error': 'All fields are required'}), 400

    if Student.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409
    if Student.query.filter_by(roll_no=roll_no).first():
        return jsonify({'error': 'Roll No already registered'}), 409

    if 'image' not in request.files:
        return jsonify({'error': 'Face image is required'}), 400

    file = request.files['image']
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    save_uploaded_image(file, filepath)

    image = __import__('cv2').imread(filepath)
    encoding = get_face_encoding(image)
    if encoding is None:
        os.remove(filepath)
        return jsonify({'error': 'No face detected in the image. Please try again.'}), 400

    student = Student(
        name=name, email=email, roll_no=roll_no,
        department=department, image_path=filename,
        face_encoding=encode_face_encoding(encoding)
    )
    db.session.add(student)
    db.session.commit()

    return jsonify({'message': 'Registration successful', 'id': student.id}), 201

@app.route('/api/attendance', methods=['POST'])
def mark_attendance():
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'Image data is required'}), 400

    image = load_image_from_base64(data['image'])
    target_encoding = get_face_encoding(image)
    if target_encoding is None:
        return jsonify({'status': 'unknown', 'message': 'No face detected'}), 200

    students = Student.query.all()
    if not students:
        return jsonify({'status': 'unknown', 'message': 'No registered users'}), 200

    known_encodings = [decode_face_encoding(s.face_encoding) for s in students]
    matched, idx, distance = compare_faces(known_encodings, target_encoding)

    if not matched:
        return jsonify({'status': 'unknown', 'message': 'Face not recognized'}), 200

    student = students[idx]
    today = date.today()
    existing = Attendance.query.filter_by(student_id=student.id, date=today).first()
    if existing:
        return jsonify({
            'status': 'already_marked',
            'message': f'{student.name} already marked present',
            'name': student.name, 'roll_no': student.roll_no,
            'time': existing.time.strftime('%H:%M:%S')
        }), 200

    now = datetime.now()
    record = Attendance(student_id=student.id, date=today, time=now.time(), status='present')
    db.session.add(record)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Attendance marked successfully',
        'name': student.name, 'roll_no': student.roll_no,
        'time': now.strftime('%H:%M:%S')
    }), 200

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    date_param = request.args.get('date')
    query = Attendance.query

    if date_param:
        try:
            filter_date = date.fromisoformat(date_param)
            query = query.filter_by(date=filter_date)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    records = query.order_by(Attendance.date.desc(), Attendance.time.desc()).all()
    return jsonify({'records': [r.to_dict() for r in records]})

@app.route('/api/attendance/date/<date_str>', methods=['GET'])
def get_attendance_by_date(date_str):
    try:
        filter_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    records = Attendance.query.filter_by(date=filter_date).order_by(Attendance.time.desc()).all()
    return jsonify({'records': [r.to_dict() for r in records]})

@app.route('/api/students', methods=['GET'])
def get_students():
    students = Student.query.order_by(Student.name).all()
    return jsonify({'students': [s.to_dict() for s in students]})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_students = Student.query.count()
    today = date.today()
    present_today = Attendance.query.filter_by(date=today, status='present').count()
    return jsonify({
        'total_students': total_students,
        'present_today': present_today
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
