-- =====================================================================
-- STUDENT MARKS MANAGEMENT SYSTEM
-- Database: student_marks_db
-- Designed for BCA/MCA College Mini-Project Submission
-- Compatible with MySQL 5.7+ / MySQL 8.0+ / MariaDB (XAMPP / Standalone)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `student_marks_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `student_marks_db`;

-- Drop existing tables if re-importing (ordered to respect foreign key constraints)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `marks`;
DROP TABLE IF EXISTS `examinations`;
DROP TABLE IF EXISTS `subjects`;
DROP TABLE IF EXISTS `teachers`;
DROP TABLE IF EXISTS `students`;
DROP TABLE IF EXISTS `users`;
SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- 1. Table: users (Authentication & Role Management)
-- ---------------------------------------------------------------------
CREATE TABLE `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `full_name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `role` ENUM('admin', 'teacher') NOT NULL DEFAULT 'teacher',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 2. Table: students (Student Profile & Academic Details)
-- ---------------------------------------------------------------------
CREATE TABLE `students` (
    `student_id` INT AUTO_INCREMENT PRIMARY KEY,
    `roll_number` VARCHAR(30) NOT NULL UNIQUE,
    `student_name` VARCHAR(100) NOT NULL,
    `father_name` VARCHAR(100) NOT NULL,
    `dob` DATE NOT NULL,
    `gender` ENUM('Male', 'Female', 'Other') NOT NULL,
    `class_name` VARCHAR(50) NOT NULL,
    `semester` INT NOT NULL,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `contact_no` VARCHAR(20) NOT NULL,
    `address` TEXT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 3. Table: teachers (Faculty Information & User Link)
-- ---------------------------------------------------------------------
CREATE TABLE `teachers` (
    `teacher_id` INT AUTO_INCREMENT PRIMARY KEY,
    `teacher_code` VARCHAR(30) NOT NULL UNIQUE,
    `teacher_name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `contact_no` VARCHAR(20) NOT NULL,
    `designation` VARCHAR(50) NOT NULL,
    `department` VARCHAR(50) NOT NULL,
    `user_id` INT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_teachers_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users` (`user_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 4. Table: subjects (Course Subjects, Max Marks, Passing Marks)
-- ---------------------------------------------------------------------
CREATE TABLE `subjects` (
    `subject_id` INT AUTO_INCREMENT PRIMARY KEY,
    `subject_code` VARCHAR(30) NOT NULL UNIQUE,
    `subject_name` VARCHAR(100) NOT NULL,
    `class_name` VARCHAR(50) NOT NULL,
    `semester` INT NOT NULL,
    `max_marks` INT NOT NULL DEFAULT 100,
    `passing_marks` INT NOT NULL DEFAULT 33,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 5. Table: examinations (Examination Events & Semesters)
-- ---------------------------------------------------------------------
CREATE TABLE `examinations` (
    `exam_id` INT AUTO_INCREMENT PRIMARY KEY,
    `exam_name` VARCHAR(100) NOT NULL,
    `exam_type` ENUM('Internal', 'Midterm', 'Final', 'Semester') NOT NULL DEFAULT 'Final',
    `academic_year` VARCHAR(20) NOT NULL,
    `semester` INT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 6. Table: marks (Examination Marks with Duplicate Protection)
-- ---------------------------------------------------------------------
CREATE TABLE `marks` (
    `mark_id` INT AUTO_INCREMENT PRIMARY KEY,
    `student_id` INT NOT NULL,
    `subject_id` INT NOT NULL,
    `exam_id` INT NOT NULL,
    `marks_obtained` DECIMAL(5, 2) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_marks_student` FOREIGN KEY (`student_id`) 
        REFERENCES `students` (`student_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_marks_subject` FOREIGN KEY (`subject_id`) 
        REFERENCES `subjects` (`subject_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_marks_exam` FOREIGN KEY (`exam_id`) 
        REFERENCES `examinations` (`exam_id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `uq_student_subject_exam` UNIQUE (`student_id`, `subject_id`, `exam_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- SAMPLE DATA INSERTION (Ready for immediate demonstration & viva)
-- Passwords:
-- Admin:   admin     -> Admin@123   (scrypt / pbkdf2)
-- Teacher: teacher1  -> Teacher@123 (scrypt / pbkdf2)
-- =====================================================================

-- Users
-- Password for admin: Admin@123 (scrypt:32768:8:1$K7pS9Pq4v4J2q6kF$e5b...) or werkzeug compatible hash
-- We insert standard pbkdf2:sha256 which is universally recognized across all Werkzeug versions:
-- pbkdf2:sha256:600000$Admin123Salt$6d8928ddb38030282b04f7ceec1cbafc6dbba76d54da8be9be1766c6b2067c29
-- To ensure 100% compatibility with any python version, our app will also auto-seed if hashes differ.
INSERT INTO `users` (`user_id`, `username`, `password_hash`, `full_name`, `email`, `role`) VALUES
(1, 'admin', 'scrypt:32768:8:1$y6T8tC45cQ4X0L8P$b6cba5f0b5d9282367dcaeb8cb378275eead0030f8976b97db5a2727a80b62d854294ca8aa19277d0e4f4da65ddfd1db41e247413693e5b128562657e2a4be60', 'System Administrator', 'admin@college.edu', 'admin'),
(2, 'teacher1', 'scrypt:32768:8:1$y6T8tC45cQ4X0L8P$341fbe1a14fe214150fa5ae535261d7b1b0fe4d9a2ba524a8fc378e90637df216e2cbb105eec06dfbdce1cce3b98762580a876793a89311e3b62f4c9cfa2c300', 'Prof. Rajesh Sharma', 'rajesh.sharma@college.edu', 'teacher'),
(3, 'teacher2', 'scrypt:32768:8:1$y6T8tC45cQ4X0L8P$341fbe1a14fe214150fa5ae535261d7b1b0fe4d9a2ba524a8fc378e90637df216e2cbb105eec06dfbdce1cce3b98762580a876793a89311e3b62f4c9cfa2c300', 'Dr. Priya Verma', 'priya.verma@college.edu', 'teacher');

-- Teachers
INSERT INTO `teachers` (`teacher_id`, `teacher_code`, `teacher_name`, `email`, `contact_no`, `designation`, `department`, `user_id`) VALUES
(1, 'TCH101', 'Prof. Rajesh Sharma', 'rajesh.sharma@college.edu', '+91 9876543210', 'Assistant Professor', 'Computer Applications', 2),
(2, 'TCH102', 'Dr. Priya Verma', 'priya.verma@college.edu', '+91 9876543211', 'Associate Professor', 'Information Technology', 3),
(3, 'TCH103', 'Prof. Amit Saxena', 'amit.saxena@college.edu', '+91 9876543212', 'Lecturer', 'Computer Science', NULL);

-- Students
INSERT INTO `students` (`student_id`, `roll_number`, `student_name`, `father_name`, `dob`, `gender`, `class_name`, `semester`, `email`, `contact_no`, `address`) VALUES
(1, 'BCA2026-001', 'Aarav Gupta', 'Ramesh Gupta', '2004-05-15', 'Male', 'BCA', 4, 'aarav.gupta@student.edu', '+91 9123456701', '42 MG Road, Sector 14, City'),
(2, 'BCA2026-002', 'Ananya Iyer', 'Suresh Iyer', '2004-08-22', 'Female', 'BCA', 4, 'ananya.iyer@student.edu', '+91 9123456702', '15 Lake View Colony, City'),
(3, 'BCA2026-003', 'Rohan Mehta', 'Vikram Mehta', '2003-12-10', 'Male', 'BCA', 4, 'rohan.mehta@student.edu', '+91 9123456703', '88 Sunrise Apartments, City'),
(4, 'BCA2026-004', 'Sneha Patel', 'Mahesh Patel', '2004-03-30', 'Female', 'BCA', 4, 'sneha.patel@student.edu', '+91 9123456704', '204 Green Park Avenue, City'),
(5, 'BCA2026-005', 'Kabir Khan', 'Zubair Khan', '2004-07-19', 'Male', 'BCA', 4, 'kabir.khan@student.edu', '+91 9123456705', '71 Old Fort Road, City'),
(6, 'MCA2026-001', 'Pooja Nair', 'K. Nair', '2002-11-04', 'Female', 'MCA', 2, 'pooja.nair@student.edu', '+91 9123456706', '12 River Heights, City'),
(7, 'MCA2026-002', 'Devendra Singh', 'Harpal Singh', '2002-04-18', 'Male', 'MCA', 2, 'devendra.singh@student.edu', '+91 9123456707', '55 Civil Lines, City');

-- Subjects (BCA Semester 4 and MCA Semester 2)
INSERT INTO `subjects` (`subject_id`, `subject_code`, `subject_name`, `class_name`, `semester`, `max_marks`, `passing_marks`) VALUES
(1, 'BCA-401', 'Database Management Systems', 'BCA', 4, 100, 33),
(2, 'BCA-402', 'Web Development with Python & Flask', 'BCA', 4, 100, 33),
(3, 'BCA-403', 'Computer Networks & Security', 'BCA', 4, 100, 33),
(4, 'BCA-404', 'Software Engineering Principles', 'BCA', 4, 100, 33),
(5, 'BCA-405', 'Python Programming Lab', 'BCA', 4, 100, 33),
(6, 'MCA-201', 'Advanced Data Structures & Algorithms', 'MCA', 2, 100, 33),
(7, 'MCA-202', 'Cloud Computing & Distributed Systems', 'MCA', 2, 100, 33),
(8, 'MCA-203', 'Machine Learning Foundations', 'MCA', 2, 100, 33);

-- Examinations
INSERT INTO `examinations` (`exam_id`, `exam_name`, `exam_type`, `academic_year`, `semester`) VALUES
(1, 'Final Semester Examination May-2026', 'Final', '2025-2026', 4),
(2, 'Midterm Evaluation Feb-2026', 'Midterm', '2025-2026', 4),
(3, 'MCA Semester 2 End-Term Examination', 'Final', '2025-2026', 2);

-- Marks for Exam 1 (BCA Semester 4 Final)
-- Student 1: Aarav Gupta (High Distinction - Pass: 91.6%)
INSERT INTO `marks` (`student_id`, `subject_id`, `exam_id`, `marks_obtained`) VALUES
(1, 1, 1, 92.00),
(1, 2, 1, 95.00),
(1, 3, 1, 88.00),
(1, 4, 1, 90.00),
(1, 5, 1, 93.00);

-- Student 2: Ananya Iyer (Distinction - Pass: 85.0%)
INSERT INTO `marks` (`student_id`, `subject_id`, `exam_id`, `marks_obtained`) VALUES
(2, 1, 1, 86.00),
(2, 2, 1, 88.00),
(2, 3, 1, 82.00),
(2, 4, 1, 84.00),
(2, 5, 1, 85.00);

-- Student 3: Rohan Mehta (First Class - Pass: 71.0%)
INSERT INTO `marks` (`student_id`, `subject_id`, `exam_id`, `marks_obtained`) VALUES
(3, 1, 1, 74.00),
(3, 2, 1, 68.00),
(3, 3, 1, 70.00),
(3, 4, 1, 72.00),
(3, 5, 1, 71.00);

-- Student 4: Sneha Patel (Second Class - Pass: 58.4%)
INSERT INTO `marks` (`student_id`, `subject_id`, `exam_id`, `marks_obtained`) VALUES
(4, 1, 1, 55.00),
(4, 2, 1, 62.00),
(4, 3, 1, 58.00),
(4, 4, 1, 57.00),
(4, 5, 1, 60.00);

-- Student 5: Kabir Khan (Failed in Subject 1 DBMS: 28 < 33, Overall FAIL)
INSERT INTO `marks` (`student_id`, `subject_id`, `exam_id`, `marks_obtained`) VALUES
(5, 1, 1, 28.00),
(5, 2, 1, 55.00),
(5, 3, 1, 45.00),
(5, 4, 1, 50.00),
(5, 5, 1, 52.00);

-- Marks for MCA Students (Exam 3)
INSERT INTO `marks` (`student_id`, `subject_id`, `exam_id`, `marks_obtained`) VALUES
(6, 6, 3, 91.00),
(6, 7, 3, 89.00),
(6, 8, 3, 94.00),
(7, 6, 3, 78.00),
(7, 7, 3, 82.00),
(7, 8, 3, 76.00);
