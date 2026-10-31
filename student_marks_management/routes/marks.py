from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import query_db, execute_db
from utils import login_required

marks_bp = Blueprint('marks', __name__)

@marks_bp.route('/marks')
@login_required
def index():
    """View entered marks with student, subject, and examination filters."""
    exam_filter = request.args.get('exam_id', '').strip()
    class_filter = request.args.get('class_name', '').strip()
    sem_filter = request.args.get('semester', '').strip()
    student_filter = request.args.get('student_id', '').strip()

    conditions = []
    params = []

    if exam_filter:
        conditions.append("m.exam_id = %s")
        params.append(exam_filter)
    if class_filter:
        conditions.append("st.class_name = %s")
        params.append(class_filter)
    if sem_filter:
        conditions.append("st.semester = %s")
        params.append(sem_filter)
    if student_filter:
        conditions.append("m.student_id = %s")
        params.append(student_filter)

    where_sql = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f"""
        SELECT m.mark_id, m.marks_obtained, m.created_at, m.updated_at,
               st.student_id, st.roll_number, st.student_name, st.class_name, st.semester,
               sub.subject_id, sub.subject_code, sub.subject_name, sub.max_marks, sub.passing_marks,
               ex.exam_id, ex.exam_name, ex.academic_year
        FROM marks m
        JOIN students st ON m.student_id = st.student_id
        JOIN subjects sub ON m.subject_id = sub.subject_id
        JOIN examinations ex ON m.exam_id = ex.exam_id
        {where_sql}
        ORDER BY st.roll_number ASC, sub.subject_code ASC
    """
    marks_list = query_db(sql, tuple(params))

    # Dropdown collections for modal & filter
    students = query_db("SELECT student_id, roll_number, student_name, class_name, semester FROM students ORDER BY roll_number ASC")
    subjects = query_db("SELECT subject_id, subject_code, subject_name, class_name, semester, max_marks, passing_marks FROM subjects ORDER BY class_name ASC, semester ASC, subject_code ASC")
    examinations = query_db("SELECT exam_id, exam_name, academic_year, semester FROM examinations ORDER BY exam_id DESC")
    classes = query_db("SELECT DISTINCT class_name FROM students ORDER BY class_name ASC")

    return render_template(
        'marks.html',
        marks=marks_list,
        students=students,
        subjects=subjects,
        examinations=examinations,
        classes=[c['class_name'] for c in classes if c['class_name']],
        selected_exam=exam_filter,
        selected_class=class_filter,
        selected_sem=sem_filter,
        selected_student=student_filter
    )

@marks_bp.route('/marks/api/student-subjects/<int:student_id>')
@login_required
def get_student_subjects(student_id):
    """API endpoint to dynamically fetch subjects matching a student's class and semester."""
    student = query_db("SELECT class_name, semester FROM students WHERE student_id = %s", (student_id,), one=True)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found', 'subjects': []}), 404

    subjects = query_db(
        """
        SELECT subject_id, subject_code, subject_name, max_marks, passing_marks
        FROM subjects
        WHERE class_name = %s AND semester = %s
        ORDER BY subject_code ASC
        """,
        (student['class_name'], student['semester'])
    )
    return jsonify({'success': True, 'subjects': subjects})

@marks_bp.route('/marks/add', methods=['POST'])
@login_required
def add():
    """
    Add marks for a student in a specific subject and examination.
    Enforces strict validation:
    1. Obtained marks cannot be negative.
    2. Obtained marks cannot exceed maximum marks.
    3. Duplicate marks entries are strictly prevented.
    """
    student_id = request.form.get('student_id', '').strip()
    subject_id = request.form.get('subject_id', '').strip()
    exam_id = request.form.get('exam_id', '').strip()
    marks_obtained_str = request.form.get('marks_obtained', '').strip()

    if not all([student_id, subject_id, exam_id, marks_obtained_str]):
        flash('All fields (Student, Subject, Examination, and Marks) are mandatory.', 'danger')
        return redirect(url_for('marks.index'))

    # Validate numbers
    try:
        marks_obtained = float(marks_obtained_str)
    except ValueError:
        flash('Obtained marks must be a valid numeric value.', 'danger')
        return redirect(url_for('marks.index'))

    # Fetch subject to check max_marks
    subject = query_db("SELECT subject_code, subject_name, max_marks, passing_marks FROM subjects WHERE subject_id = %s", (subject_id,), one=True)
    if not subject:
        flash('Selected subject does not exist.', 'danger')
        return redirect(url_for('marks.index'))

    max_marks = float(subject['max_marks'])

    # Validation Rule 1: Marks cannot be negative
    if marks_obtained < 0:
        flash(f"Validation Error: Marks cannot be negative ({marks_obtained}).", 'danger')
        return redirect(url_for('marks.index'))

    # Validation Rule 2: Marks cannot exceed maximum marks
    if marks_obtained > max_marks:
        flash(f"Validation Error: Obtained marks ({marks_obtained}) cannot exceed Maximum Marks ({max_marks}) for {subject['subject_name']}.", 'danger')
        return redirect(url_for('marks.index'))

    # Validation Rule 3: Prevent duplicate marks entries for same student, subject, and exam
    duplicate = query_db(
        "SELECT mark_id FROM marks WHERE student_id = %s AND subject_id = %s AND exam_id = %s",
        (student_id, subject_id, exam_id),
        one=True
    )
    if duplicate:
        flash(f"Duplicate Entry Error: Marks for this student in '{subject['subject_name']}' are already recorded. Use the Edit function to update existing marks.", 'warning')
        return redirect(url_for('marks.index'))

    try:
        execute_db(
            "INSERT INTO marks (student_id, subject_id, exam_id, marks_obtained) VALUES (%s, %s, %s, %s)",
            (student_id, subject_id, exam_id, marks_obtained)
        )
        flash(f"Marks ({marks_obtained}/{max_marks}) saved successfully!", 'success')
    except Exception as e:
        flash(f"Database error while saving marks: {str(e)}", 'danger')

    return redirect(url_for('marks.index'))

@marks_bp.route('/marks/edit/<int:mark_id>', methods=['POST'])
@login_required
def edit(mark_id):
    """Update existing marks with validation."""
    marks_obtained_str = request.form.get('marks_obtained', '').strip()

    try:
        marks_obtained = float(marks_obtained_str)
    except ValueError:
        flash('Marks must be a valid number.', 'danger')
        return redirect(url_for('marks.index'))

    # Fetch mark record and subject
    mark_rec = query_db(
        """
        SELECT m.mark_id, s.max_marks, s.subject_name
        FROM marks m
        JOIN subjects s ON m.subject_id = s.subject_id
        WHERE m.mark_id = %s
        """,
        (mark_id,),
        one=True
    )
    if not mark_rec:
        flash('Marks record not found.', 'danger')
        return redirect(url_for('marks.index'))

    max_marks = float(mark_rec['max_marks'])

    if marks_obtained < 0:
        flash('Marks cannot be negative.', 'danger')
        return redirect(url_for('marks.index'))

    if marks_obtained > max_marks:
        flash(f"Marks ({marks_obtained}) cannot exceed Maximum Marks ({max_marks}) for {mark_rec['subject_name']}.", 'danger')
        return redirect(url_for('marks.index'))

    execute_db("UPDATE marks SET marks_obtained = %s WHERE mark_id = %s", (marks_obtained, mark_id))
    flash('Marks updated successfully!', 'success')
    return redirect(url_for('marks.index'))

@marks_bp.route('/marks/delete/<int:mark_id>', methods=['POST'])
@login_required
def delete(mark_id):
    """Delete a marks record."""
    mark = query_db("SELECT mark_id FROM marks WHERE mark_id = %s", (mark_id,), one=True)
    if mark:
        execute_db("DELETE FROM marks WHERE mark_id = %s", (mark_id,))
        flash('Marks record deleted successfully.', 'success')
    else:
        flash('Marks record not found.', 'danger')
    return redirect(url_for('marks.index'))
