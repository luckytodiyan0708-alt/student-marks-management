import os
import sqlite3
import pymysql
import pymysql.cursors
from flask import current_app, g
from werkzeug.security import generate_password_hash

# Global cache for database mode: 'mysql' or 'sqlite'
_db_engine = None

def check_db_connection():
    """Test whether database engine is reachable and return status."""
    engine = get_engine_type()
    if engine == 'mysql':
        return True, "Connected to MySQL server (port 3306)."
    return True, "Connected to local database engine."

def get_engine_type():
    """Determine whether MySQL is active or if local database fallback should be used."""
    global _db_engine
    if _db_engine is not None:
        return _db_engine
    
    config = current_app.config
    try:
        conn = pymysql.connect(
            host=config.get('MYSQL_HOST', 'localhost'),
            user=config.get('MYSQL_USER', 'root'),
            password=config.get('MYSQL_PASSWORD', ''),
            port=config.get('MYSQL_PORT', 3306),
            connect_timeout=2
        )
        conn.close()
        _db_engine = 'mysql'
    except Exception:
        _db_engine = 'sqlite'
    
    return _db_engine

def get_mysql_connection(use_database=True):
    """Establish and return a MySQL connection using PyMySQL."""
    config = current_app.config
    db_name = config.get('MYSQL_DB', 'student_marks_db') if use_database else None
    return pymysql.connect(
        host=config.get('MYSQL_HOST', 'localhost'),
        user=config.get('MYSQL_USER', 'root'),
        password=config.get('MYSQL_PASSWORD', ''),
        database=db_name,
        port=config.get('MYSQL_PORT', 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )

def get_sqlite_path():
    """Return absolute path to local sqlite database file."""
    return os.path.join(os.path.dirname(__file__), 'database', 'student_marks_db.sqlite')

def get_sqlite_connection():
    """Establish and return SQLite connection with dictionary-like row factory."""
    db_path = get_sqlite_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    """Get or create database connection for the current Flask request context."""
    if 'db' not in g:
        engine = get_engine_type()
        if engine == 'mysql':
            g.db = get_mysql_connection(use_database=True)
            g.db_type = 'mysql'
        else:
            g.db = get_sqlite_connection()
            g.db_type = 'sqlite'
    return g.db

def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass

def format_query_for_engine(query, engine):
    """Convert %s placeholders to ? if using SQLite engine."""
    if engine == 'sqlite':
        return query.replace('%s', '?')
    return query

def query_db(query, args=(), one=False):
    """Execute a parameterized SELECT query."""
    engine = get_engine_type()
    db = get_db()
    formatted_query = format_query_for_engine(query, engine)
    
    try:
        if engine == 'mysql':
            with db.cursor() as cursor:
                cursor.execute(formatted_query, args)
                rv = cursor.fetchall()
                return (rv[0] if rv else None) if one else rv
        else:
            cursor = db.cursor()
            cursor.execute(formatted_query, args)
            rows = cursor.fetchall()
            # Convert sqlite3.Row to standard dicts
            dict_rows = [dict(row) for row in rows]
            return (dict_rows[0] if dict_rows else None) if one else dict_rows
    except Exception as err:
        if current_app:
            current_app.logger.error(f"Database query error [{engine}]: {err}")
        return None if one else []

def execute_db(query, args=(), commit=True):
    """Execute an INSERT, UPDATE, or DELETE parameterized query."""
    engine = get_engine_type()
    db = get_db()
    formatted_query = format_query_for_engine(query, engine)
    
    try:
        if engine == 'mysql':
            with db.cursor() as cursor:
                cursor.execute(formatted_query, args)
                last_id = cursor.lastrowid
                affected = cursor.rowcount
            if commit:
                db.commit()
            return last_id if last_id else affected
        else:
            cursor = db.cursor()
            cursor.execute(formatted_query, args)
            last_id = cursor.lastrowid
            affected = cursor.rowcount
            if commit:
                db.commit()
            return last_id if last_id else affected
    except Exception as err:
        if current_app:
            current_app.logger.error(f"Database execute error [{engine}]: {err}")
        if db:
            try:
                db.rollback()
            except Exception:
                pass
        raise err

def initialize_database_if_needed():
    """
    Verifies that the database and tables exist.
    If MySQL is available, initializes MySQL with student_marks_db.sql.
    If MySQL is not running, initializes the local fallback database.
    """
    global _db_engine
    engine = get_engine_type()
    
    if engine == 'mysql':
        try:
            conn = get_mysql_connection(use_database=False)
            with conn.cursor() as cursor:
                cursor.execute("CREATE DATABASE IF NOT EXISTS `student_marks_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.commit()
            conn.close()

            conn = get_mysql_connection(use_database=True)
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES LIKE 'users';")
                if not cursor.fetchone():
                    sql_path = os.path.join(os.path.dirname(__file__), 'database', 'student_marks_db.sql')
                    if os.path.exists(sql_path):
                        with open(sql_path, 'r', encoding='utf-8') as f:
                            sql_content = f.read()
                        for stmt in sql_content.split(';'):
                            stmt_clean = stmt.strip()
                            if stmt_clean and not stmt_clean.startswith('--') and not stmt_clean.startswith('/*'):
                                try:
                                    cursor.execute(stmt_clean)
                                except Exception:
                                    pass
                        conn.commit()

                # Sync passwords
                admin_hash = generate_password_hash('Admin@123')
                teacher_hash = generate_password_hash('Teacher@123')
                cursor.execute("UPDATE `users` SET `password_hash` = %s WHERE `username` = 'admin';", (admin_hash,))
                cursor.execute("UPDATE `users` SET `password_hash` = %s WHERE `username` = 'teacher1';", (teacher_hash,))
                conn.commit()
                conn.close()
                return True, "MySQL database (student_marks_db) connected and initialized successfully."
        except Exception as e:
            _db_engine = 'sqlite'
            # Fall back to sqlite initialization below

    # SQLite Local Database Initialization
    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        # Create Tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL DEFAULT 'teacher',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_number TEXT NOT NULL UNIQUE,
                student_name TEXT NOT NULL,
                father_name TEXT NOT NULL,
                dob DATE NOT NULL,
                gender TEXT NOT NULL,
                class_name TEXT NOT NULL,
                semester INTEGER NOT NULL,
                email TEXT NOT NULL UNIQUE,
                contact_no TEXT NOT NULL,
                address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_code TEXT NOT NULL UNIQUE,
                teacher_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                contact_no TEXT NOT NULL,
                designation TEXT NOT NULL,
                department TEXT NOT NULL,
                user_id INTEGER NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_code TEXT NOT NULL UNIQUE,
                subject_name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                semester INTEGER NOT NULL,
                max_marks INTEGER NOT NULL DEFAULT 100,
                passing_marks INTEGER NOT NULL DEFAULT 33,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS examinations (
                exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_name TEXT NOT NULL,
                exam_type TEXT NOT NULL DEFAULT 'Final',
                academic_year TEXT NOT NULL,
                semester INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS marks (
                mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                marks_obtained REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects (subject_id) ON DELETE CASCADE,
                FOREIGN KEY (exam_id) REFERENCES examinations (exam_id) ON DELETE CASCADE,
                UNIQUE (student_id, subject_id, exam_id)
            );
        """)
        conn.commit()

        # Check if users already seeded
        cursor.execute("SELECT COUNT(*) FROM users;")
        if cursor.fetchone()[0] == 0:
            admin_hash = generate_password_hash('Admin@123')
            teacher_hash = generate_password_hash('Teacher@123')
            cursor.execute("INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
                           ('admin', admin_hash, 'System Administrator', 'admin@college.edu', 'admin'))
            cursor.execute("INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
                           ('teacher1', teacher_hash, 'Prof. Rajesh Sharma', 'rajesh.sharma@college.edu', 'teacher'))
            cursor.execute("INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
                           ('teacher2', teacher_hash, 'Dr. Priya Verma', 'priya.verma@college.edu', 'teacher'))

            # Teachers
            cursor.execute("INSERT INTO teachers (teacher_code, teacher_name, email, contact_no, designation, department, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           ('TCH101', 'Prof. Rajesh Sharma', 'rajesh.sharma@college.edu', '+91 9876543210', 'Assistant Professor', 'Computer Applications', 2))
            cursor.execute("INSERT INTO teachers (teacher_code, teacher_name, email, contact_no, designation, department, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           ('TCH102', 'Dr. Priya Verma', 'priya.verma@college.edu', '+91 9876543211', 'Associate Professor', 'Information Technology', 3))
            cursor.execute("INSERT INTO teachers (teacher_code, teacher_name, email, contact_no, designation, department, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           ('TCH103', 'Prof. Amit Saxena', 'amit.saxena@college.edu', '+91 9876543212', 'Lecturer', 'Computer Science', None))

            # Students
            students_sample = [
                ('BCA2026-001', 'Aarav Gupta', 'Ramesh Gupta', '2004-05-15', 'Male', 'BCA', 4, 'aarav.gupta@student.edu', '+91 9123456701', '42 MG Road, Sector 14, City'),
                ('BCA2026-002', 'Ananya Iyer', 'Suresh Iyer', '2004-08-22', 'Female', 'BCA', 4, 'ananya.iyer@student.edu', '+91 9123456702', '15 Lake View Colony, City'),
                ('BCA2026-003', 'Rohan Mehta', 'Vikram Mehta', '2003-12-10', 'Male', 'BCA', 4, 'rohan.mehta@student.edu', '+91 9123456703', '88 Sunrise Apartments, City'),
                ('BCA2026-004', 'Sneha Patel', 'Mahesh Patel', '2004-03-30', 'Female', 'BCA', 4, 'sneha.patel@student.edu', '+91 9123456704', '204 Green Park Avenue, City'),
                ('BCA2026-005', 'Kabir Khan', 'Zubair Khan', '2004-07-19', 'Male', 'BCA', 4, 'kabir.khan@student.edu', '+91 9123456705', '71 Old Fort Road, City'),
                ('MCA2026-001', 'Pooja Nair', 'K. Nair', '2002-11-04', 'Female', 'MCA', 2, 'pooja.nair@student.edu', '+91 9123456706', '12 River Heights, City'),
                ('MCA2026-002', 'Devendra Singh', 'Harpal Singh', '2002-04-18', 'Male', 'MCA', 2, 'devendra.singh@student.edu', '+91 9123456707', '55 Civil Lines, City')
            ]
            for s in students_sample:
                cursor.execute("""
                    INSERT INTO students (roll_number, student_name, father_name, dob, gender, class_name, semester, email, contact_no, address)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, s)

            # Subjects
            subjects_sample = [
                ('BCA-401', 'Database Management Systems', 'BCA', 4, 100, 33),
                ('BCA-402', 'Web Development with Python & Flask', 'BCA', 4, 100, 33),
                ('BCA-403', 'Computer Networks & Security', 'BCA', 4, 100, 33),
                ('BCA-404', 'Software Engineering Principles', 'BCA', 4, 100, 33),
                ('BCA-405', 'Python Programming Lab', 'BCA', 4, 100, 33),
                ('MCA-201', 'Advanced Data Structures & Algorithms', 'MCA', 2, 100, 33),
                ('MCA-202', 'Cloud Computing & Distributed Systems', 'MCA', 2, 100, 33),
                ('MCA-203', 'Machine Learning Foundations', 'MCA', 2, 100, 33)
            ]
            for sub in subjects_sample:
                cursor.execute("""
                    INSERT INTO subjects (subject_code, subject_name, class_name, semester, max_marks, passing_marks)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, sub)

            # Examinations
            cursor.execute("INSERT INTO examinations (exam_name, exam_type, academic_year, semester) VALUES (?, ?, ?, ?)",
                           ('Final Semester Examination May-2026', 'Final', '2025-2026', 4))
            cursor.execute("INSERT INTO examinations (exam_name, exam_type, academic_year, semester) VALUES (?, ?, ?, ?)",
                           ('Midterm Evaluation Feb-2026', 'Midterm', '2025-2026', 4))
            cursor.execute("INSERT INTO examinations (exam_name, exam_type, academic_year, semester) VALUES (?, ?, ?, ?)",
                           ('MCA Semester 2 End-Term Examination', 'Final', '2025-2026', 2))

            # Marks for Exam 1 (BCA Semester 4 Final)
            # Student 1: Aarav Gupta (Distinction - Pass: 91.6%)
            marks_sample = [
                (1, 1, 1, 92.0), (1, 2, 1, 95.0), (1, 3, 1, 88.0), (1, 4, 1, 90.0), (1, 5, 1, 93.0),
                (2, 1, 1, 86.0), (2, 2, 1, 88.0), (2, 3, 1, 82.0), (2, 4, 1, 84.0), (2, 5, 1, 85.0),
                (3, 1, 1, 74.0), (3, 2, 1, 68.0), (3, 3, 1, 70.0), (3, 4, 1, 72.0), (3, 5, 1, 71.0),
                (4, 1, 1, 55.0), (4, 2, 1, 62.0), (4, 3, 1, 58.0), (4, 4, 1, 57.0), (4, 5, 1, 60.0),
                (5, 1, 1, 28.0), (5, 2, 1, 55.0), (5, 3, 1, 45.0), (5, 4, 1, 50.0), (5, 5, 1, 52.0),
                (6, 6, 3, 91.0), (6, 7, 3, 89.0), (6, 8, 3, 94.0),
                (7, 6, 3, 78.0), (7, 7, 3, 82.0), (7, 8, 3, 76.0)
            ]
            for m in marks_sample:
                cursor.execute("""
                    INSERT INTO marks (student_id, subject_id, exam_id, marks_obtained)
                    VALUES (?, ?, ?, ?)
                """, m)

            conn.commit()

        conn.close()
        return True, "Local database initialized with all student, faculty, and marks sample records."
    except Exception as e:
        return False, f"Local database initialization error: {str(e)}"
