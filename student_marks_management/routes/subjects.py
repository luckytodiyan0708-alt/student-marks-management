from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import query_db, execute_db
from utils import login_required, admin_required

subjects_bp = Blueprint('subjects', __name__)

@subjects_bp.route('/subjects')
@login_required
def index():
    """List all subjects with class and semester filtering."""
    class_filter = request.args.get('class_name', '').strip()
    sem_filter = request.args.get('semester', '').strip()

    conditions = []
    params = []

    if class_filter:
        conditions.append("class_name = %s")
        params.append(class_filter)
    if sem_filter:
        conditions.append("semester = %s")
        params.append(sem_filter)

    where_sql = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT * FROM subjects {where_sql} ORDER BY class_name ASC, semester ASC, subject_code ASC"
    subjects = query_db(sql, tuple(params))

    # Distinct values for dropdown filters
    available_classes = query_db("SELECT DISTINCT class_name FROM subjects ORDER BY class_name ASC")
    available_semesters = query_db("SELECT DISTINCT semester FROM subjects ORDER BY semester ASC")

    return render_template(
        'subjects.html',
        subjects=subjects,
        selected_class=class_filter,
        selected_sem=sem_filter,
        available_classes=[c['class_name'] for c in available_classes if c['class_name']],
        available_semesters=[s['semester'] for s in available_semesters if s['semester']]
    )

@subjects_bp.route('/subjects/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    """Add a new subject."""
    if request.method == 'POST':
        subject_code = request.form.get('subject_code', '').strip().upper()
        subject_name = request.form.get('subject_name', '').strip()
        class_name = request.form.get('class_name', '').strip().upper()
        semester = request.form.get('semester', '').strip()
        max_marks = request.form.get('max_marks', '100').strip()
        passing_marks = request.form.get('passing_marks', '33').strip()

        if not all([subject_code, subject_name, class_name, semester, max_marks, passing_marks]):
            flash('All subject fields are required.', 'danger')
            return redirect(url_for('subjects.index'))

        try:
            max_m = int(max_marks)
            pass_m = int(passing_marks)
            if pass_m > max_m or max_m <= 0 or pass_m < 0:
                flash('Passing marks cannot exceed maximum marks or be negative.', 'danger')
                return redirect(url_for('subjects.index'))
        except ValueError:
            flash('Marks must be valid numbers.', 'danger')
            return redirect(url_for('subjects.index'))

        # Check duplicate code
        dup = query_db("SELECT subject_id FROM subjects WHERE subject_code = %s", (subject_code,), one=True)
        if dup:
            flash(f"Error: Subject code '{subject_code}' already exists.", 'danger')
            return redirect(url_for('subjects.index'))

        execute_db(
            """
            INSERT INTO subjects (subject_code, subject_name, class_name, semester, max_marks, passing_marks)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (subject_code, subject_name, class_name, int(semester), max_m, pass_m)
        )
        flash(f"Subject '{subject_name}' ({subject_code}) added successfully!", 'success')
        return redirect(url_for('subjects.index'))

    return redirect(url_for('subjects.index'))

@subjects_bp.route('/subjects/edit/<int:subject_id>', methods=['POST'])
@login_required
@admin_required
def edit(subject_id):
    """Edit existing subject."""
    subject_code = request.form.get('subject_code', '').strip().upper()
    subject_name = request.form.get('subject_name', '').strip()
    class_name = request.form.get('class_name', '').strip().upper()
    semester = request.form.get('semester', '').strip()
    max_marks = request.form.get('max_marks', '').strip()
    passing_marks = request.form.get('passing_marks', '').strip()

    # Check duplicate code for other subjects
    dup = query_db(
        "SELECT subject_id FROM subjects WHERE subject_code = %s AND subject_id != %s",
        (subject_code, subject_id),
        one=True
    )
    if dup:
        flash(f"Error: Subject code '{subject_code}' is already used by another subject.", 'danger')
        return redirect(url_for('subjects.index'))

    try:
        max_m = int(max_marks)
        pass_m = int(passing_marks)
        if pass_m > max_m:
            flash('Passing marks cannot exceed maximum marks.', 'danger')
            return redirect(url_for('subjects.index'))

        execute_db(
            """
            UPDATE subjects SET
            subject_code = %s, subject_name = %s, class_name = %s,
            semester = %s, max_marks = %s, passing_marks = %s
            WHERE subject_id = %s
            """,
            (subject_code, subject_name, class_name, int(semester), max_m, pass_m, subject_id)
        )
        flash('Subject updated successfully!', 'success')
    except Exception as e:
        flash(f"Failed to update subject: {str(e)}", 'danger')

    return redirect(url_for('subjects.index'))

@subjects_bp.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required
@admin_required
def delete(subject_id):
    """Delete a subject and its associated marks."""
    sub = query_db("SELECT subject_code, subject_name FROM subjects WHERE subject_id = %s", (subject_id,), one=True)
    if sub:
        execute_db("DELETE FROM subjects WHERE subject_id = %s", (subject_id,))
        flash(f"Subject '{sub['subject_name']}' ({sub['subject_code']}) deleted successfully.", 'success')
    else:
        flash('Subject not found.', 'danger')
    return redirect(url_for('subjects.index'))
