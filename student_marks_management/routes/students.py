import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, current_app
from database import query_db, execute_db
from utils import login_required, admin_required

students_bp = Blueprint('students', __name__)

@students_bp.route('/students')
@login_required
def index():
    """List students with search, filters (class & semester), and pagination."""
    search = request.args.get('search', '').strip()
    class_filter = request.args.get('class_name', '').strip()
    sem_filter = request.args.get('semester', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('STUDENTS_PER_PAGE', 8)
    offset = (page - 1) * per_page

    # Construct dynamic WHERE clauses
    conditions = []
    params = []

    if search:
        conditions.append("(roll_number LIKE %s OR student_name LIKE %s OR email LIKE %s)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    if class_filter:
        conditions.append("class_name = %s")
        params.append(class_filter)

    if sem_filter:
        conditions.append("semester = %s")
        params.append(sem_filter)

    where_sql = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    # Count total matching records for pagination
    count_sql = f"SELECT COUNT(*) AS total FROM students {where_sql}"
    total_row = query_db(count_sql, tuple(params), one=True)
    total_students = total_row['total'] if total_row else 0
    total_pages = max(1, (total_students + per_page - 1) // per_page)

    # Fetch paginated rows
    fetch_sql = f"SELECT * FROM students {where_sql} ORDER BY roll_number ASC LIMIT %s OFFSET %s"
    fetch_params = list(params) + [per_page, offset]
    students = query_db(fetch_sql, tuple(fetch_params))

    # Distinct classes and semesters for filter dropdowns
    available_classes = query_db("SELECT DISTINCT class_name FROM students ORDER BY class_name ASC")
    available_semesters = query_db("SELECT DISTINCT semester FROM students ORDER BY semester ASC")

    return render_template(
        'students.html',
        students=students,
        search=search,
        selected_class=class_filter,
        selected_sem=sem_filter,
        available_classes=[c['class_name'] for c in available_classes if c['class_name']],
        available_semesters=[s['semester'] for s in available_semesters if s['semester']],
        page=page,
        total_pages=total_pages,
        total_students=total_students
    )

@students_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    """Add a new student profile with duplicate validation."""
    if request.method == 'POST':
        roll_number = request.form.get('roll_number', '').strip().upper()
        student_name = request.form.get('student_name', '').strip()
        father_name = request.form.get('father_name', '').strip()
        dob = request.form.get('dob', '').strip()
        gender = request.form.get('gender', '').strip()
        class_name = request.form.get('class_name', '').strip().upper()
        semester = request.form.get('semester', '').strip()
        email = request.form.get('email', '').strip().lower()
        contact_no = request.form.get('contact_no', '').strip()
        address = request.form.get('address', '').strip()

        # Validation
        if not all([roll_number, student_name, father_name, dob, gender, class_name, semester, email, contact_no, address]):
            flash('All fields are mandatory. Please fill in the entire form.', 'danger')
            return render_template('add_student.html', form=request.form)

        # Check duplicate roll number
        dup_roll = query_db("SELECT student_id FROM students WHERE roll_number = %s", (roll_number,), one=True)
        if dup_roll:
            flash(f"Error: Roll number '{roll_number}' already exists in the system.", 'danger')
            return render_template('add_student.html', form=request.form)

        # Check duplicate email
        dup_email = query_db("SELECT student_id FROM students WHERE email = %s", (email,), one=True)
        if dup_email:
            flash(f"Error: Email '{email}' is already registered with another student.", 'danger')
            return render_template('add_student.html', form=request.form)

        try:
            execute_db(
                """
                INSERT INTO students 
                (roll_number, student_name, father_name, dob, gender, class_name, semester, email, contact_no, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (roll_number, student_name, father_name, dob, gender, class_name, int(semester), email, contact_no, address)
            )
            flash(f"Student '{student_name}' (Roll: {roll_number}) enrolled successfully!", 'success')
            return redirect(url_for('students.index'))
        except Exception as e:
            flash(f"Database error while saving student: {str(e)}", 'danger')
            return render_template('add_student.html', form=request.form)

    return render_template('add_student.html', form={})

@students_bp.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(student_id):
    """Update existing student details."""
    student = query_db("SELECT * FROM students WHERE student_id = %s", (student_id,), one=True)
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('students.index'))

    if request.method == 'POST':
        roll_number = request.form.get('roll_number', '').strip().upper()
        student_name = request.form.get('student_name', '').strip()
        father_name = request.form.get('father_name', '').strip()
        dob = request.form.get('dob', '').strip()
        gender = request.form.get('gender', '').strip()
        class_name = request.form.get('class_name', '').strip().upper()
        semester = request.form.get('semester', '').strip()
        email = request.form.get('email', '').strip().lower()
        contact_no = request.form.get('contact_no', '').strip()
        address = request.form.get('address', '').strip()

        # Check duplicate roll number for other students
        dup_roll = query_db(
            "SELECT student_id FROM students WHERE roll_number = %s AND student_id != %s",
            (roll_number, student_id),
            one=True
        )
        if dup_roll:
            flash(f"Error: Roll number '{roll_number}' belongs to another student.", 'danger')
            return render_template('edit_student.html', student=request.form, student_id=student_id)

        # Check duplicate email
        dup_email = query_db(
            "SELECT student_id FROM students WHERE email = %s AND student_id != %s",
            (email, student_id),
            one=True
        )
        if dup_email:
            flash(f"Error: Email '{email}' belongs to another student.", 'danger')
            return render_template('edit_student.html', student=request.form, student_id=student_id)

        try:
            execute_db(
                """
                UPDATE students SET
                roll_number = %s, student_name = %s, father_name = %s, dob = %s, gender = %s,
                class_name = %s, semester = %s, email = %s, contact_no = %s, address = %s
                WHERE student_id = %s
                """,
                (roll_number, student_name, father_name, dob, gender, class_name, int(semester), email, contact_no, address, student_id)
            )
            flash(f"Student '{student_name}' updated successfully!", 'success')
            return redirect(url_for('students.index'))
        except Exception as e:
            flash(f"Failed to update student: {str(e)}", 'danger')

    return render_template('edit_student.html', student=student, student_id=student_id)

@students_bp.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
@admin_required
def delete(student_id):
    """Delete a student and cascading related marks."""
    student = query_db("SELECT roll_number, student_name FROM students WHERE student_id = %s", (student_id,), one=True)
    if student:
        execute_db("DELETE FROM students WHERE student_id = %s", (student_id,))
        flash(f"Student '{student['student_name']}' (Roll: {student['roll_number']}) was deleted successfully.", 'success')
    else:
        flash('Student record not found.', 'danger')
    return redirect(url_for('students.index'))

@students_bp.route('/students/export-csv')
@login_required
def export_csv():
    """Export all student records to a downloadable CSV file."""
    students = query_db("SELECT * FROM students ORDER BY roll_number ASC")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        'Student ID', 'Roll Number', 'Student Name', 'Father Name',
        'Date of Birth', 'Gender', 'Class', 'Semester', 'Email', 'Contact No', 'Address'
    ])
    
    for s in students:
        writer.writerow([
            s['student_id'],
            s['roll_number'],
            s['student_name'],
            s['father_name'],
            str(s['dob']),
            s['gender'],
            s['class_name'],
            s['semester'],
            s['email'],
            s['contact_no'],
            s['address']
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=students_directory.csv"}
    )
