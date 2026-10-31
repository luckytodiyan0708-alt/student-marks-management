from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from database import query_db, execute_db
from utils import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle Admin and Teacher Login."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter both username and password.', 'warning')
            return render_template('login.html', username=username)
        
        # Parameterized query to prevent SQL Injection
        user = query_db(
            "SELECT * FROM users WHERE username = %s OR email = %s",
            (username, username),
            one=True
        )
        
        if user and check_password_hash(user['password_hash'], password):
            # Establish session
            session.clear()
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['email'] = user['email']
            session['role'] = user['role']
            session.permanent = True
            
            flash(f"Welcome back, {user['full_name']}! Logged in as {user['role'].capitalize()}.", 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('login.html', username=username)
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Log out current user and clear session."""
    user_name = session.get('full_name', 'User')
    session.clear()
    flash(f"Goodbye {user_name}! You have been safely logged out.", 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View user profile and change password."""
    user = query_db("SELECT * FROM users WHERE user_id = %s", (session['user_id'],), one=True)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            
            if not full_name or not email:
                flash('Full Name and Email are required.', 'danger')
            else:
                # Check email collision
                existing = query_db(
                    "SELECT user_id FROM users WHERE email = %s AND user_id != %s",
                    (email, session['user_id']),
                    one=True
                )
                if existing:
                    flash('This email address is already in use by another account.', 'danger')
                else:
                    execute_db(
                        "UPDATE users SET full_name = %s, email = %s WHERE user_id = %s",
                        (full_name, email, session['user_id'])
                    )
                    session['full_name'] = full_name
                    session['email'] = email
                    flash('Profile details updated successfully!', 'success')
                    return redirect(url_for('auth.profile'))
                    
        elif action == 'change_password':
            current_pass = request.form.get('current_password', '')
            new_pass = request.form.get('new_password', '')
            confirm_pass = request.form.get('confirm_password', '')
            
            if not check_password_hash(user['password_hash'], current_pass):
                flash('Current password is incorrect.', 'danger')
            elif len(new_pass) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
            elif new_pass != confirm_pass:
                flash('New passwords do not match.', 'danger')
            else:
                new_hash = generate_password_hash(new_pass)
                execute_db("UPDATE users SET password_hash = %s WHERE user_id = %s", (new_hash, session['user_id']))
                flash('Password changed successfully!', 'success')
                return redirect(url_for('auth.profile'))
                
    return render_template('profile.html', user=user)
