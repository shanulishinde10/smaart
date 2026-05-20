"""
Scanora Database Seeder
Run: python seed.py
Adds professors, students, lectures, and attendance records.
"""
import sys
import os
import io
import json
import random
import numpy as np

# Force UTF-8 output on Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Course, Professor, Student, Lecture, AttendanceRecord


def fake_encoding():
    """Random normalized HOG-like vector (2916-dim) for dummy face data."""
    vec = np.random.rand(2916).astype(np.float32)
    norm = np.linalg.norm(vec)
    return json.dumps((vec / norm if norm > 0 else vec).tolist())


def seed():
    with app.app_context():

        # ── Courses ──────────────────────────────────────────────────────
        btech = Course.query.filter_by(code='BTECH').first()
        mba   = Course.query.filter_by(code='MBA').first()
        mtech = Course.query.filter_by(code='MTECH').first()
        msc   = Course.query.filter_by(code='MSC').first()
        mcs   = Course.query.filter_by(code='MCS').first()
        bca   = Course.query.filter_by(code='BCA').first()
        mca   = Course.query.filter_by(code='MCA').first()

        if not all([btech, mba, mtech, msc, mcs, bca, mca]):
            print("ERROR: Courses missing. Start the app once first to seed base courses.")
            return

        print("\n── Professors ──────────────────────────────────────────────────")

        profs_def = [
            {
                'name': 'Dr. Ravi Kumar',
                'employee_id': 'EMP001',
                'email': 'ravi.kumar@college.edu',
                'username': 'ravi.kumar',
                'password': 'prof123',
                'courses': [btech, mca],
            },
            {
                'name': 'Dr. Anjali Mehta',
                'employee_id': 'EMP002',
                'email': 'anjali.mehta@college.edu',
                'username': 'anjali.mehta',
                'password': 'prof123',
                'courses': [mba, msc],
            },
            {
                'name': 'Prof. Suresh Patel',
                'employee_id': 'EMP003',
                'email': 'suresh.patel@college.edu',
                'username': 'suresh.patel',
                'password': 'prof123',
                'courses': [bca, mcs, mtech],
            },
        ]

        prof_objects = {}
        for pd in profs_def:
            existing_user = User.query.filter_by(username=pd['username']).first()
            if existing_user:
                print(f"  [skip] {pd['name']} already exists")
                prof_objects[pd['username']] = Professor.query.filter_by(user_id=existing_user.id).first()
                continue

            u = User(username=pd['username'], email=pd['email'], role='professor')
            u.set_password(pd['password'])
            db.session.add(u)
            db.session.flush()

            p = Professor(user_id=u.id, name=pd['name'], employee_id=pd['employee_id'])
            p.courses = pd['courses']
            db.session.add(p)
            db.session.flush()
            prof_objects[pd['username']] = p
            print(f"  [+] {pd['name']}  ({pd['username']} / {pd['password']})  →  courses: {[c.code for c in pd['courses']]}")

        db.session.commit()

        # ── Students ────────────────────────────────────────────────────
        print("\n── Students ────────────────────────────────────────────────────")

        students_def = [
            # B.Tech students
            {'name': 'Priya Sharma',    'roll': 'CS2024001', 'email': 'priya.sharma@student.edu',    'course': btech},
            {'name': 'Aditya Singh',    'roll': 'CS2024002', 'email': 'aditya.singh@student.edu',    'course': btech},
            {'name': 'Rahul Mehta',     'roll': 'CS2024003', 'email': 'rahul.mehta@student.edu',     'course': btech},
            {'name': 'Shreya Kapoor',   'roll': 'CS2024004', 'email': 'shreya.kapoor@student.edu',   'course': btech},
            {'name': 'Varun Joshi',     'roll': 'CS2024005', 'email': 'varun.joshi@student.edu',     'course': btech},
            {'name': 'Neha Gupta',      'roll': 'CS2024006', 'email': 'neha.gupta@student.edu',      'course': btech},
            {'name': 'Kiran Reddy',     'roll': 'CS2024007', 'email': 'kiran.reddy@student.edu',     'course': btech},
            # MBA students
            {'name': 'Karan Patel',     'roll': 'MB2024001', 'email': 'karan.patel@student.edu',     'course': mba},
            {'name': 'Meera Nair',      'roll': 'MB2024002', 'email': 'meera.nair@student.edu',      'course': mba},
            {'name': 'Rohan Verma',     'roll': 'MB2024003', 'email': 'rohan.verma@student.edu',     'course': mba},
            {'name': 'Divya Reddy',     'roll': 'MB2024004', 'email': 'divya.reddy@student.edu',     'course': mba},
            # MCA students
            {'name': 'Saurabh Tiwari',  'roll': 'MC2024001', 'email': 'saurabh.tiwari@student.edu', 'course': mca},
            {'name': 'Pooja Yadav',     'roll': 'MC2024002', 'email': 'pooja.yadav@student.edu',     'course': mca},
            {'name': 'Amit Desai',      'roll': 'MC2024003', 'email': 'amit.desai@student.edu',      'course': mca},
            # BCA students
            {'name': 'Simran Kaur',     'roll': 'BC2024001', 'email': 'simran.kaur@student.edu',     'course': bca},
            {'name': 'Arjun Malhotra',  'roll': 'BC2024002', 'email': 'arjun.malhotra@student.edu', 'course': bca},
            {'name': 'Tanvi Shah',      'roll': 'BC2024003', 'email': 'tanvi.shah@student.edu',      'course': bca},
            # MCS students
            {'name': 'Deepak Nanda',    'roll': 'MCS2024001', 'email': 'deepak.nanda@student.edu',   'course': mcs},
            {'name': 'Ankita Bose',     'roll': 'MCS2024002', 'email': 'ankita.bose@student.edu',    'course': mcs},
            # M.Tech students
            {'name': 'Vikram Choudhary', 'roll': 'MT2024001', 'email': 'vikram.c@student.edu',       'course': mtech},
            {'name': 'Riya Jain',        'roll': 'MT2024002', 'email': 'riya.jain@student.edu',      'course': mtech},
        ]

        student_objects = []
        for sd in students_def:
            if Student.query.filter_by(roll_no=sd['roll']).first():
                print(f"  [skip] {sd['name']} ({sd['roll']}) already exists")
                student_objects.append(Student.query.filter_by(roll_no=sd['roll']).first())
                continue

            u = User(username=sd['roll'], email=sd['email'], role='student')
            u.set_password('student123')
            db.session.add(u)
            db.session.flush()

            s = Student(
                user_id=u.id,
                name=sd['name'],
                email=sd['email'],
                roll_no=sd['roll'],
                course_id=sd['course'].id,
                face_encoding=fake_encoding(),
            )
            db.session.add(s)
            db.session.flush()
            student_objects.append(s)
            print(f"  [+] {sd['name']:<22}  {sd['roll']:<12}  {sd['course'].code}")

        db.session.commit()

        # ── Lectures ─────────────────────────────────────────────────────
        print("\n── Lectures ────────────────────────────────────────────────────")

        today = date.today()
        ravi   = prof_objects.get('ravi.kumar')
        anjali = prof_objects.get('anjali.mehta')
        suresh = prof_objects.get('suresh.patel')

        lectures_def = [
            # ─ Today ─
            {'prof': ravi,   'course': btech, 'title': 'Unit 3 — Data Structures & Trees',       'days': 0},
            {'prof': anjali, 'course': mba,   'title': 'Business Strategy & Analytics',          'days': 0},
            {'prof': suresh, 'course': bca,   'title': 'Web Development — HTML & CSS',           'days': 0},
            # ─ Yesterday ─
            {'prof': ravi,   'course': btech, 'title': 'Unit 2 — Algorithms & Complexity',       'days': 1},
            {'prof': anjali, 'course': mba,   'title': 'Financial Management — Module 4',        'days': 1},
            {'prof': ravi,   'course': mca,   'title': 'Database Management Systems — SQL',      'days': 1},
            {'prof': suresh, 'course': mcs,   'title': 'Machine Learning — Linear Regression',   'days': 1},
            # ─ 2 days ago ─
            {'prof': ravi,   'course': btech, 'title': 'Unit 2 — Sorting & Searching',           'days': 2},
            {'prof': anjali, 'course': msc,   'title': 'Statistics — Probability & Distributions', 'days': 2},
            {'prof': suresh, 'course': mtech, 'title': 'Advanced OS — Process Scheduling',       'days': 2},
            # ─ 3 days ago ─
            {'prof': anjali, 'course': mba,   'title': 'Marketing Management — Module 3',        'days': 3},
            {'prof': ravi,   'course': btech, 'title': 'Unit 1 — Introduction to DSA',           'days': 3},
            {'prof': suresh, 'course': bca,   'title': 'Programming Basics — Functions',         'days': 3},
            # ─ 4 days ago ─
            {'prof': ravi,   'course': mca,   'title': 'DBMS — ER Modelling & Normalization',    'days': 4},
            {'prof': anjali, 'course': mba,   'title': 'Organizational Behaviour — Module 2',    'days': 4},
            {'prof': suresh, 'course': mcs,   'title': 'Machine Learning — Data Preprocessing',  'days': 4},
        ]

        lecture_objects = []
        for ld in lectures_def:
            if not ld['prof']:
                continue
            lec_date = today - timedelta(days=ld['days'])
            existing = Lecture.query.filter_by(
                professor_id=ld['prof'].id,
                course_id=ld['course'].id,
                title=ld['title'],
                date=lec_date,
            ).first()
            if existing:
                print(f"  [skip] '{ld['title']}' on {lec_date}")
                lecture_objects.append((existing, ld['course'].id, ld['days']))
                continue

            lec = Lecture(
                professor_id=ld['prof'].id,
                course_id=ld['course'].id,
                title=ld['title'],
                date=lec_date,
            )
            db.session.add(lec)
            db.session.flush()
            lecture_objects.append((lec, ld['course'].id, ld['days']))
            print(f"  [+] [{lec_date}]  {ld['course'].code:<6}  {ld['title']}")

        db.session.commit()

        # ── Attendance Records ───────────────────────────────────────────
        print("\n── Attendance Records ──────────────────────────────────────────")

        course_students = {}
        for s in student_objects:
            course_students.setdefault(s.course_id, []).append(s)

        new_records = 0
        for lec, course_id, days_ago in lecture_objects:
            enrolled = course_students.get(course_id, [])
            if not enrolled:
                continue

            for student in enrolled:
                if AttendanceRecord.query.filter_by(student_id=student.id, lecture_id=lec.id).first():
                    continue

                lec_date = today - timedelta(days=days_ago)

                if days_ago == 0:
                    # Today: mostly pending/present, a couple absent
                    status = random.choices(
                        ['present', 'pending', 'absent'],
                        weights=[40, 45, 15]
                    )[0]
                    scan_time = (
                        datetime.combine(lec_date, datetime.min.time()).replace(
                            hour=random.randint(8, 10),
                            minute=random.randint(0, 59),
                            second=random.randint(0, 59),
                        )
                        if status != 'absent' else None
                    )
                    reviewed_at = None
                else:
                    # Past: mostly reviewed (present/absent)
                    status = random.choices(
                        ['present', 'absent'],
                        weights=[75, 25]
                    )[0]
                    scan_time = datetime.combine(lec_date, datetime.min.time()).replace(
                        hour=random.randint(8, 11),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59),
                    )
                    reviewed_at = scan_time + timedelta(minutes=random.randint(20, 90))

                db.session.add(AttendanceRecord(
                    student_id=student.id,
                    lecture_id=lec.id,
                    date=lec_date,
                    scan_time=scan_time,
                    status=status,
                    reviewed_at=reviewed_at,
                ))
                new_records += 1

        db.session.commit()
        print(f"  [+] {new_records} attendance records created")

        # ── Summary ──────────────────────────────────────────────────────
        print("\n" + "═" * 55)
        print("  ✅  Seed complete!")
        print("═" * 55)
        print(f"  Professors : {Professor.query.count()}")
        print(f"  Students   : {Student.query.count()}")
        print(f"  Lectures   : {Lecture.query.count()}")
        print(f"  Attendance : {AttendanceRecord.query.count()}")
        print("═" * 55)
        print("  Login credentials")
        print("  ─────────────────────────────────────────────────")
        print("  Admin         admin           / admin123")
        print("  Professor     ravi.kumar      / prof123")
        print("  Professor     anjali.mehta    / prof123")
        print("  Professor     suresh.patel    / prof123")
        print("  Student       CS2024001       / student123")
        print("  Student       MB2024001       / student123")
        print("  Student       MC2024001       / student123")
        print("═" * 55 + "\n")


if __name__ == '__main__':
    seed()
