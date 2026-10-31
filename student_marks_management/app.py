import os
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect, CSRFError
from config import Config
from database import close_db, initialize_database_if_needed, check_db_connection
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.students import students_bp
from routes.subjects import subjects_bp
from routes.teachers import teachers_bp
from routes.marks import marks_bp
from routes.results import results_bp

def create_app(config_class=Config):
    """Application Factory Pattern for Student Marks Management System."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CSRF Protection
    csrf = CSRFProtect(app)

    # Register Database teardown
    app.teardown_appcontext(close_db)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(teachers_bp)
    app.register_blueprint(marks_bp)
    app.register_blueprint(results_bp)

    # Global Template Context Processor (accessible across all Jinja2 templates)
    @app.context_processor
    def inject_global_data():
        return {
            'college_name': app.config.get('COLLEGE_NAME', 'STUDENT MARKS SYSTEM'),
            'college_affiliation': app.config.get('COLLEGE_AFFILIATION', ''),
            'college_address': app.config.get('COLLEGE_ADDRESS', ''),
            'college_contact': app.config.get('COLLEGE_CONTACT', '')
        }

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('error.html', title="CSRF Token Error", message="Security validation failed. Please refresh the page and try again."), 400

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template(
            'error.html',
            title="Database Connection / Server Notice",
            message="Unable to communicate with MySQL Server. If using XAMPP, please make sure MySQL is started (green indicator) in XAMPP Control Panel on port 3306."
        ), 500

    # Auto-initialize database on application launch
    with app.app_context():
        status, msg = initialize_database_if_needed()
        if not status:
            print(f"[Notice] Database Initialization: {msg}")
        else:
            print(f"[OK] {msg}")

    return app

app = create_app()

if __name__ == '__main__':
    # Running Flask development server
    print("=" * 65)
    print("  STUDENT MARKS MANAGEMENT SYSTEM - BCA/MCA PROJECT")
    print("  Access URL: http://127.0.0.1:5000")
    print("  Default Admin  : admin    / Admin@123")
    print("  Default Teacher: teacher1 / Teacher@123")
    print("=" * 65)
    app.run(host='127.0.0.1', port=5000, debug=True)
