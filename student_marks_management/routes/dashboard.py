from flask import Blueprint, render_template, session, jsonify
from database import query_db
from utils import login_required, compute_student_result

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Main Dashboard with analytical metrics and performance charts."""
    # 1. Base counts
    student_count_row = query_db("SELECT COUNT(*) AS total FROM students", one=True)
    teacher_count_row = query_db("SELECT COUNT(*) AS total FROM teachers", one=True)
    subject_count_row = query_db("SELECT COUNT(*) AS total FROM subjects", one=True)
    exam_count_row = query_db("SELECT COUNT(*) AS total FROM examinations", one=True)

    total_students = student_count_row['total'] if student_count_row else 0
    total_teachers = teacher_count_row['total'] if teacher_count_row else 0
    total_subjects = subject_count_row['total'] if subject_count_row else 0
    total_exams = exam_count_row['total'] if exam_count_row else 0

    # 2. Compute academic statistics across active students and latest exams
    students = query_db("SELECT student_id, class_name, semester FROM students")
    exams = query_db("SELECT exam_id, exam_name FROM examinations ORDER BY exam_id DESC")

    passed_count = 0
    failed_count = 0
    incomplete_count = 0
    percentages = []
    
    # Grade distribution counter
    grade_counts = {'A+': 0, 'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}

    # Evaluate results using primary examination (or latest exam with marks)
    primary_exam = exams[0] if exams else None
    
    if primary_exam and students:
        for st in students:
            res = compute_student_result(st['student_id'], primary_exam['exam_id'])
            if res and res['is_complete']:
                if res['status'] == 'PASS':
                    passed_count += 1
                else:
                    failed_count += 1
                percentages.append(res['percentage'])
                grade = res['grade']
                if grade in grade_counts:
                    grade_counts[grade] += 1
                else:
                    grade_counts['F'] += 1
            elif res and not res['is_complete'] and res['entered_subjects'] > 0:
                incomplete_count += 1

    class_average = round(sum(percentages) / len(percentages), 2) if percentages else 0.0

    # 3. Subject-wise average marks for the primary exam
    subject_stats = []
    if primary_exam:
        subject_stats = query_db(
            """
            SELECT s.subject_code, s.subject_name, s.max_marks,
                   ROUND(AVG(m.marks_obtained), 2) AS avg_marks,
                   COUNT(m.mark_id) AS student_count
            FROM subjects s
            LEFT JOIN marks m ON s.subject_id = m.subject_id AND m.exam_id = %s
            GROUP BY s.subject_id, s.subject_code, s.subject_name, s.max_marks
            HAVING student_count > 0
            ORDER BY s.subject_code ASC
            """,
            (primary_exam['exam_id'],)
        )

    # 4. Recent activities / recent marks entries
    recent_marks = query_db(
        """
        SELECT m.mark_id, m.marks_obtained, m.created_at,
               s.roll_number, s.student_name, sub.subject_code, sub.subject_name, sub.max_marks
        FROM marks m
        JOIN students s ON m.student_id = s.student_id
        JOIN subjects sub ON m.subject_id = sub.subject_id
        ORDER BY m.created_at DESC
        LIMIT 6
        """
    )

    stats = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_subjects': total_subjects,
        'total_exams': total_exams,
        'total_passed': passed_count,
        'total_failed': failed_count,
        'incomplete_count': incomplete_count,
        'class_average': class_average,
        'primary_exam': primary_exam
    }

    # Chart data formatted as lists for easy Chart.js integration
    chart_data = {
        'grade_labels': list(grade_counts.keys()),
        'grade_values': list(grade_counts.values()),
        'pass_fail_labels': ['Passed Students', 'Failed Students'],
        'pass_fail_values': [passed_count, failed_count],
        'subject_labels': [f"{sub['subject_code']}" for sub in subject_stats],
        'subject_averages': [float(sub['avg_marks']) for sub in subject_stats]
    }

    return render_template(
        'dashboard.html',
        stats=stats,
        chart_data=chart_data,
        recent_marks=recent_marks,
        exams=exams
    )
