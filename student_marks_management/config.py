import os

class Config:
    """Application Configuration Settings"""
    # Secret Key for sessions and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY', 'college_student_marks_system_secure_key_2026')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY', 'csrf_protection_secret_key_2026')
    
    # MySQL Database Connection Parameters (Defaults match XAMPP MySQL)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'student_marks_db')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    
    # Pagination
    STUDENTS_PER_PAGE = 8
    
    # Institution Branding Details (Printed on Marksheets & Reports)
    COLLEGE_NAME = os.environ.get('COLLEGE_NAME', 'METROPOLITAN INSTITUTE OF TECHNOLOGY & SCIENCE')
    COLLEGE_AFFILIATION = os.environ.get('COLLEGE_AFFILIATION', 'Affiliated to State Technical University | Approved by AICTE, New Delhi')
    COLLEGE_ADDRESS = os.environ.get('COLLEGE_ADDRESS', 'Knowledge Campus, Sector-12, Cyber City - 110001')
    COLLEGE_CONTACT = os.environ.get('COLLEGE_CONTACT', 'Tel: +91-11-23456789 | Email: exam@mits.edu.in')
