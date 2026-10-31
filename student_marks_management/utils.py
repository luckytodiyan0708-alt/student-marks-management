from functools import wraps
from flask import session, flash, redirect, url_for
from database import query_db

def login_required(f):
    """Decorator to ensure user is logged in before accessing route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to restrict access to administrators only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_grade(percentage):
    """
    Returns the letter grade according to the academic specification:
    90-100: A+
    80-89 : A
    70-79 : B
    60-69 : C
    50-59 : D
    40-49 : E
    Below 40: F
    """
    if percentage >= 90.0:
        return 'A+'
    elif percentage >= 80.0:
        return 'A'
    elif percentage >= 70.0:
        return 'B'
    elif percentage >= 60.0:
        return 'C'
    elif percentage >= 50.0:
        return 'D'
    elif percentage >= 40.0:
        return 'E'
    else:
        return 'F'

def compute_student_result(student_id, exam_id):
    """
    Calculates detailed result for a student in a specific examination:
    - Subject-wise scores, max marks, passing marks, subject pass/fail
    - Total obtained marks and total maximum marks
    - Percentage calculation
    - Grade calculation
    - Final status (PASS / FAIL / INCOMPLETE)
    
    Rules:
    - Must achieve at least 33% (or passing_marks) in every subject to pass.
    - If fail in any subject -> Overall FAIL.
    - If marks are not entered for all registered subjects -> INCOMPLETE.
    """
    # 1. Fetch student info
    student = query_db(
        "SELECT * FROM students WHERE student_id = %s",
        (student_id,),
        one=True
    )
    if not student:
        return None

    # 2. Fetch examination info
    exam = query_db(
        "SELECT * FROM examinations WHERE exam_id = %s",
        (exam_id,),
        one=True
    )
    if not exam:
        return None

    # 3. Fetch all subjects for the student's class and semester
    subjects = query_db(
        "SELECT * FROM subjects WHERE class_name = %s AND semester = %s ORDER BY subject_code ASC",
        (student['class_name'], student['semester'])
    )

    # 4. Fetch marks entered for this student and exam
    marks_records = query_db(
        """
        SELECT m.mark_id, m.subject_id, m.marks_obtained,
               s.subject_code, s.subject_name, s.max_marks, s.passing_marks
        FROM marks m
        JOIN subjects s ON m.subject_id = s.subject_id
        WHERE m.student_id = %s AND m.exam_id = %s
        """,
        (student_id, exam_id)
    )

    marks_by_subject = {m['subject_id']: m for m in marks_records}

    subject_results = []
    total_obtained = 0.0
    total_max = 0.0
    all_subjects_entered = True
    any_subject_failed = False

    for sub in subjects:
        sub_id = sub['subject_id']
        max_marks = float(sub['max_marks'])
        passing_marks = float(sub['passing_marks'])
        total_max += max_marks

        if sub_id in marks_by_subject:
            m_rec = marks_by_subject[sub_id]
            obtained = float(m_rec['marks_obtained'])
            total_obtained += obtained
            sub_pct = (obtained / max_marks) * 100.0 if max_marks > 0 else 0.0
            
            # Subject pass rule: obtained >= passing_marks
            passed_subject = obtained >= passing_marks
            if not passed_subject:
                any_subject_failed = True

            subject_results.append({
                'subject_id': sub_id,
                'subject_code': sub['subject_code'],
                'subject_name': sub['subject_name'],
                'max_marks': max_marks,
                'passing_marks': passing_marks,
                'marks_obtained': obtained,
                'percentage': round(sub_pct, 2),
                'status': 'PASS' if passed_subject else 'FAIL',
                'grade': calculate_grade(sub_pct),
                'is_entered': True,
                'mark_id': m_rec['mark_id']
            })
        else:
            all_subjects_entered = False
            subject_results.append({
                'subject_id': sub_id,
                'subject_code': sub['subject_code'],
                'subject_name': sub['subject_name'],
                'max_marks': max_marks,
                'passing_marks': passing_marks,
                'marks_obtained': None,
                'percentage': 0.0,
                'status': 'PENDING',
                'grade': '-',
                'is_entered': False,
                'mark_id': None
            })

    total_subjects_count = len(subjects)
    entered_subjects_count = len(marks_records)

    if not all_subjects_entered or total_subjects_count == 0:
        return {
            'student': student,
            'exam': exam,
            'subjects': subject_results,
            'total_subjects': total_subjects_count,
            'entered_subjects': entered_subjects_count,
            'total_obtained': total_obtained,
            'total_max': total_max,
            'percentage': 0.0,
            'grade': 'INCOMPLETE',
            'status': 'INCOMPLETE',
            'is_complete': False,
            'message': f"Marks pending for {total_subjects_count - entered_subjects_count} subject(s)."
        }

    percentage = (total_obtained / total_max) * 100.0 if total_max > 0 else 0.0
    overall_status = 'FAIL' if any_subject_failed else 'PASS'
    overall_grade = calculate_grade(percentage) if overall_status == 'PASS' else 'F'

    return {
        'student': student,
        'exam': exam,
        'subjects': subject_results,
        'total_subjects': total_subjects_count,
        'entered_subjects': entered_subjects_count,
        'total_obtained': round(total_obtained, 2),
        'total_max': round(total_max, 2),
        'percentage': round(percentage, 2),
        'grade': overall_grade,
        'status': overall_status,
        'is_complete': True,
        'message': 'Result declared successfully.'
    }
