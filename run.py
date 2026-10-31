import os
import sys

# Add student_marks_management to python path
project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'student_marks_management')
sys.path.insert(0, project_dir)
os.chdir(project_dir)

from app import app

if __name__ == '__main__':
    print("=" * 68)
    print("  STUDENT MARKS MANAGEMENT SYSTEM")
    print("  BCA / MCA College Mini-Project Submission")
    print("  Access Web Application at: http://127.0.0.1:5000")
    print("  Default Admin  : admin    / Admin@123")
    print("  Default Teacher: teacher1 / Teacher@123")
    print("=" * 68)
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)

