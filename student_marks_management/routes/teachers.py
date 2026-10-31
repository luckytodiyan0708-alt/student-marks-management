from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from database import query_db, execute_db
from utils import login_required, admin_required

teachers_bp = Blueprint('teachers', __name__)

@teachers_bp.route('/teachers')
@login_required
@admin_required
def index():
    """List all teachers with department and user account linkage."""
    teachers = query_db(
        """
        SELECT t.*, u.username, u.role
        FROM teachers t
        LEFT JOIN users u ON t.user_id = u.user_id
        ORDER BY t.teacher_name ASC
        """
    )
    return render_template('teachers.html', teachers=teachers)

@teachers_bp.route('/teachers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    """Add a new teacher and optionally create login account."""
    if request.method == 'POST':
        teacher_code = request.form.get('teacher_code', '').strip().upper()
        teacher_name = request.form.get('teacher_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        contact_no = request.form.get('contact_no', '').strip()
        designation = request.form.get('designation', '').strip()
        department = request.form.get('department', '').strip()
        create_account = request.form.get('create_account') == '1'
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not all([teacher_code, teacher_name, email, contact_no, designation, department]):
            flash('All teacher details are required.', 'danger')
            return redirect(url_for('teachers.index'))

        # Check duplicate code
        dup_code = query_db("SELECT teacher_id FROM teachers WHERE teacher_code = %s", (teacher_code,), one=True)
        if dup_code:
            flash(f"Error: Teacher code '{teacher_code}' already exists.", 'danger')
            return redirect(url_for('teachers.index'))

        # Check duplicate email
        dup_email = query_db("SELECT teacher_id FROM teachers WHERE email = %s", (email,), one=True)
        if dup_email:
            flash(f"Error: Email '{email}' is already registered with another teacher.", 'danger')
            return redirect(url_for('teachers.index'))

        user_id = None
        if create_account:
            if not username or not password:
                flash('Username and Password are required to create a login account.', 'danger')
                return redirect(url_for('teachers.index'))

            dup_user = query_db("SELECT user_id FROM users WHERE username = %s OR email = %s", (username, email), one=True)
            if dup_user:
                flash(f"Username '{username}' or email '{email}' already has a user account.", 'danger')
                return redirect(url_for('teachers.index'))

            pwd_hash = generate_password_hash(password)
            user_id = execute_db(
                "INSERT INTO users (username, password_hash, full_name, email, role) VALUES (%s, %s, %s, %s, 'teacher')",
                (username, pwd_hash, teacher_name, email)
            )

        execute_db(
            """
            INSERT INTO teachers (teacher_code, teacher_name, email, contact_no, designation, department, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (teacher_code, teacher_name, email, contact_no, designation, department, user_id)
        )
        flash(f"Faculty member '{teacher_name}' ({teacher_code}) added successfully!", 'success')
        return redirect(url_for('teachers.index'))

    return redirect(url_for('teachers.index'))

@teachers_bp.route('/teachers/edit/<int:teacher_id>', methods=['POST'])
@login_required
@admin_required
def edit(teacher_id):
    """Edit existing teacher record."""
    teacher_code = request.form.get('teacher_code', '').strip().upper()
    teacher_name = request.form.get('teacher_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    contact_no = request.form.get('contact_no', '').strip()
    designation = request.form.get('designation', '').strip()
    department = request.form.get('department', '').strip()

    # Check duplicate code
    dup = query_db("SELECT teacher_id FROM teachers WHERE teacher_code = %s AND teacher_id != %s", (teacher_code, teacher_id), one=True)
    if dup:
        flash(f"Error: Teacher code '{teacher_code}' already exists.", 'danger')
        return redirect(url_for('teachers.index'))

    execute_db(
        """
        UPDATE teachers SET
        teacher_code = %s, teacher_name = %s, email = %s,
        contact_no = %s, designation = %s, department = %s
        WHERE teacher_id = %s
        """,
        (teacher_code, teacher_name, email, contact_no, designation, department, teacher_id)
    )
    flash('Teacher details updated successfully!', 'success')
    return redirect(url_for('teachers.index'))

@teachers_bp.route('/teachers/delete/<int:teacher_id>', methods=['POST'])
@login_required
@admin_required
def delete(teacher_id):
    """Delete a teacher and optionally associated user account."""
    teacher = query_db("SELECT teacher_name, user_id FROM teachers WHERE teacher_id = %s", (teacher_id,), one=True)
    if teacher:
        if teacher['user_id']:
            execute_db("DELETE FROM users WHERE user_id = %s", (teacher['user_id'],))
        execute_db("DELETE FROM teachers WHERE teacher_id = %s", (teacher_id,))
        flash(f"Teacher '{teacher['teacher_name']}' removed successfully.", 'success')
    else:
        flash('Teacher not found.', 'danger')
    return redirect(url_for('teachers.index'))
