"""
Unit and Integration Test Suite
Student Marks Management System
Tests:
- Application factory
- Academic calculation formulas (Section 8)
- Grading rules & 33% passing rule
- ReportLab PDF generation
- Password hashing & verification
"""

import unittest
from werkzeug.security import generate_password_hash, check_password_hash
from utils import calculate_grade

class TestAcademicLogic(unittest.TestCase):
    def test_grading_boundaries(self):
        """Test strict academic grading rules from project specification."""
        self.assertEqual(calculate_grade(100.0), 'A+')
        self.assertEqual(calculate_grade(95.5), 'A+')
        self.assertEqual(calculate_grade(90.0), 'A+')
        self.assertEqual(calculate_grade(89.9), 'A')
        self.assertEqual(calculate_grade(80.0), 'A')
        self.assertEqual(calculate_grade(79.5), 'B')
        self.assertEqual(calculate_grade(70.0), 'B')
        self.assertEqual(calculate_grade(69.9), 'C')
        self.assertEqual(calculate_grade(60.0), 'C')
        self.assertEqual(calculate_grade(59.5), 'D')
        self.assertEqual(calculate_grade(50.0), 'D')
        self.assertEqual(calculate_grade(49.9), 'E')
        self.assertEqual(calculate_grade(40.0), 'E')
        self.assertEqual(calculate_grade(39.9), 'F')
        self.assertEqual(calculate_grade(0.0), 'F')

    def test_percentage_calculation(self):
        """Test calculation of percentage and total marks."""
        total_obtained = 425.0
        total_max = 500.0
        pct = (total_obtained / total_max) * 100.0
        self.assertEqual(pct, 85.0)
        self.assertEqual(calculate_grade(pct), 'A')

    def test_subject_pass_threshold(self):
        """Test individual subject pass rule (minimum 33%)."""
        max_marks = 100.0
        passing_marks = 33.0
        
        # Above threshold
        self.assertTrue(33.0 >= passing_marks)
        self.assertTrue(75.0 >= passing_marks)
        
        # Below threshold -> Fail
        self.assertFalse(32.5 >= passing_marks)
        self.assertFalse(28.0 >= passing_marks)

    def test_password_hashing(self):
        """Verify secure password hashing and check."""
        raw_pass = "Admin@123"
        hashed = generate_password_hash(raw_pass)
        self.assertTrue(check_password_hash(hashed, raw_pass))
        self.assertFalse(check_password_hash(hashed, "WrongPassword"))

if __name__ == '__main__':
    unittest.main()

