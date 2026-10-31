# STUDENT MARKS MANAGEMENT SYSTEM
**A Professional Web-Based College Mini-Project for BCA & MCA Students**

---

## 📌 Project Overview
The **Student Marks Management System** is a robust, full-stack web application developed using **Python Flask** and **MySQL**. It is engineered to streamline academic administration, student demographic records, course subjects, examination assessment, automatic grading, and official marksheet generation.

---

## 🚀 Key Features

1. **Role-Based Authentication**:
   - **Admin Portal**: Full CRUD privileges across students, faculty, subjects, examination events, and mark entries.
   - **Faculty Portal**: Record exam scores, modify marks, view class scorecards, and monitor pass/fail statistics.
   - **Security**: Passwords hashed using PBKDF2 / Scrypt (`werkzeug.security`); CSRF protection via `Flask-WTF`.

2. **Automated Academic Grading & Evaluation**:
   - Instant calculation: $\text{Total Marks} = \sum \text{Obtained Marks}$, $\text{Max Marks} = \sum \text{Maximum Marks}$.
   - Percentage formula: $\text{Percentage} = \left(\frac{\text{Total Obtained}}{\text{Total Maximum}}\right) \times 100$.
   - **Academic Grade Hierarchy**:
     - `90% - 100%`: **A+**
     - `80% - 89%` : **A**
     - `70% - 79%` : **B**
     - `60% - 69%` : **C**
     - `50% - 59%` : **D**
     - `40% - 49%` : **E**
     - `Below 40%` : **F (Fail)**
   - **Subject Passing Criteria**: Students must secure at least 33% (or individual subject threshold) in **every** subject. Failure in any single subject results in an overall status of **FAIL**.
   - **Incomplete Protection**: Final results are withheld until all curriculum subjects have marks recorded.

3. **Analytics & Performance Dashboard**:
   - 6 Quick-statistic metric cards (Total Students, Teachers, Subjects, Passed, Failed, Class Average).
   - **Interactive Chart.js visual graphs**:
     - Grade Distribution (A+ to F bar chart).
     - Pass vs Fail Doughnut ratio.
     - Subject-wise average score comparison.

4. **Official Marksheets & PDF Reports**:
   - Authentic institutional marksheet design with college branding and signature blocks.
   - One-click native browser printing (`@media print` optimized).
   - Direct high-resolution PDF download powered by **ReportLab**.
   - Export full student directory to **CSV format**.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, FontAwesome 6, Chart.js |
| **Backend** | Python 3.11+, Flask 3.1, Flask-WTF, Werkzeug |
| **Database** | MySQL Server / MariaDB (via PyMySQL & mysql-connector-python) |
| **PDF Engine** | ReportLab 5.1 |
| **Dev Tools** | Visual Studio Code, XAMPP, Web Browser |

---

## 📂 Project Directory Structure

```text
student_marks_management/
│
├── app.py                      # Flask Application Factory & Core Server
├── config.py                   # Centralized Configuration & DB Settings
├── database.py                 # MySQL Connection Pool & Query Handlers
├── utils.py                    # Academic Grading, Result Formulas & Auth Decorators
├── requirements.txt            # Python Dependencies
├── test_app.py                 # Automated Unit & Academic Rule Test Suite
├── README.md                   # Setup Guide & Documentation
│
├── database/
│   └── student_marks_db.sql    # Complete SQL Schema, Relationships & Sample Records
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                 # Login, Logout, Profile & Password Management
│   ├── dashboard.py            # Academic Metrics, Statistics & Chart.js Data
│   ├── students.py             # Student CRUD, CSV Export & Pagination
│   ├── subjects.py             # Course Curriculum & Marks Thresholds
│   ├── teachers.py             # Faculty Directory & Account Linking
│   ├── marks.py                # Marks Assessment & Validation Engine
│   └── results.py              # Results Search, Marksheets & PDF Generation
│
├── templates/
│   ├── base.html               # Responsive Master Layout & Sidebar
│   ├── login.html              # Modern Authentication Portal
│   ├── dashboard.html          # Performance Dashboard & Graphical Analytics
│   ├── students.html           # Student Roster with Filters & Pagination
│   ├── add_student.html        # Student Enrollment Form
│   ├── edit_student.html       # Student Profile Update Form
│   ├── subjects.html           # Curriculum & Subject Management
│   ├── teachers.html           # Faculty Management
│   ├── marks.html              # Marks Recording Interface
│   ├── results.html            # Scorecard Search & Class-wise Roster
│   ├── marksheet.html          # Official Printable Marksheet
│   ├── profile.html            # User Profile & Security Settings
│   ├── 404.html                # Page Not Found Error Page
│   └── error.html              # General Error Notice
│
└── static/
    ├── css/
    │   └── style.css           # Custom CSS, Themes & Responsive Rules
    └── js/
        └── script.js           # UI Interactivity, Validations & Dynamic Dropdowns
```

---

## ⚙️ Installation & Setup Guide

### 1. Start MySQL Server (via XAMPP)
1. Launch **XAMPP Control Panel**.
2. Click **Start** next to **MySQL** (and Apache if using phpMyAdmin).
3. Ensure MySQL is running on port `3306`.

### 2. Import the Database
*Option A: Automatic Initialization*
The Flask application includes an auto-importer! When you start the application for the first time, it automatically creates `student_marks_db` and loads all tables and sample records.

*Option B: Manual Import via phpMyAdmin / MySQL CLI*
```bash
mysql -u root -p < database/student_marks_db.sql
```

### 3. Install Python Dependencies
Open your terminal inside the project directory and run:
```bash
pip install -r requirements.txt
```

### 4. Launch the Web Application
```bash
python app.py
```
Or run from the project root:
```bash
python run.py
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🔐 Default Login Credentials

| Role | Username | Password | Privileges |
|---|---|---|---|
| **Administrator** | `admin` | `Admin@123` | Full access (Students, Teachers, Subjects, Marks, Results) |
| **Faculty / Teacher** | `teacher1` | `Teacher@123` | View students, Enter & Update Marks, View Results |

*(Note: The login page includes convenient 1-click credential buttons for evaluation).*

---

## 🧪 Running Automated Tests
To verify all academic calculations, grading scale cutoffs, and security logic:
```bash
python test_app.py
```

---

## 📜 License & Academic Usage
Developed for educational evaluation, viva examination, and college mini-project submissions for Bachelor of Computer Applications (BCA) and Master of Computer Applications (MCA) programs.

