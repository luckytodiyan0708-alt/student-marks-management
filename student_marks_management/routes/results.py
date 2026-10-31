import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, current_app
from database import query_db
from utils import login_required, compute_student_result
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

results_bp = Blueprint('results', __name__)

@results_bp.route('/results')
@login_required
def index():
    """
    Result Search and Class/Semester Result Explorer.
    Features search by Roll Number and filter by Exam, Class, and Semester.
    """
    roll_number = request.args.get('roll_number', '').strip().upper()
    exam_id = request.args.get('exam_id', type=int)
    class_filter = request.args.get('class_name', '').strip()
    sem_filter = request.args.get('semester', type=int)

    examinations = query_db("SELECT * FROM examinations ORDER BY exam_id DESC")
    classes = query_db("SELECT DISTINCT class_name FROM students ORDER BY class_name ASC")
    
    # Default to first exam if none selected
    if not exam_id and examinations:
        exam_id = examinations[0]['exam_id']

    searched_result = None
    if roll_number and exam_id:
        student = query_db("SELECT student_id FROM students WHERE roll_number = %s", (roll_number,), one=True)
        if student:
            searched_result = compute_student_result(student['student_id'], exam_id)
            if not searched_result:
                flash('Unable to calculate result for the specified student and exam.', 'warning')
        else:
            flash(f"No student found with Roll Number '{roll_number}'.", 'danger')

    # Query class-wise results if filters or default view active
    class_results = []
    if exam_id:
        conditions = []
        params = []

        if class_filter:
            conditions.append("class_name = %s")
            params.append(class_filter)
        if sem_filter:
            conditions.append("semester = %s")
            params.append(sem_filter)

        where_sql = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        students_in_scope = query_db(f"SELECT student_id FROM students {where_sql} ORDER BY roll_number ASC", tuple(params))

        for st in students_in_scope:
            res = compute_student_result(st['student_id'], exam_id)
            if res:
                class_results.append(res)

    return render_template(
        'results.html',
        examinations=examinations,
        classes=[c['class_name'] for c in classes if c['class_name']],
        selected_exam_id=exam_id,
        selected_class=class_filter,
        selected_sem=sem_filter,
        searched_roll=roll_number,
        searched_result=searched_result,
        class_results=class_results
    )

@results_bp.route('/results/student/<int:student_id>/exam/<int:exam_id>')
@login_required
def student_result(student_id, exam_id):
    """View individual student result page."""
    result = compute_student_result(student_id, exam_id)
    if not result:
        flash('Result record could not be found.', 'danger')
        return redirect(url_for('results.index'))

    return render_template('results.html', searched_result=result, selected_exam_id=exam_id)

@results_bp.route('/results/marksheet/<int:student_id>/exam/<int:exam_id>')
@login_required
def marksheet(student_id, exam_id):
    """Render a dedicated, printable official Marksheet."""
    result = compute_student_result(student_id, exam_id)
    if not result:
        flash('Result data not available.', 'danger')
        return redirect(url_for('results.index'))

    college = {
        'name': current_app.config.get('COLLEGE_NAME'),
        'affiliation': current_app.config.get('COLLEGE_AFFILIATION'),
        'address': current_app.config.get('COLLEGE_ADDRESS'),
        'contact': current_app.config.get('COLLEGE_CONTACT')
    }

    return render_template('marksheet.html', result=result, college=college)

@results_bp.route('/results/pdf/<int:student_id>/exam/<int:exam_id>')
@login_required
def download_pdf(student_id, exam_id):
    """Generate and download a genuine PDF marksheet using ReportLab."""
    result = compute_student_result(student_id, exam_id)
    if not result:
        flash('Result data not available for PDF generation.', 'danger')
        return redirect(url_for('results.index'))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CollegeTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        alignment=1, # Center
        textColor=colors.HexColor('#0d47a1')
    )
    sub_title_style = ParagraphStyle(
        'CollegeSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor('#455a64')
    )
    doc_heading = ParagraphStyle(
        'DocHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        alignment=1,
        textColor=colors.HexColor('#1b5e20')
    )
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11
    )

    elements = []

    # 1. College Header
    elements.append(Paragraph(current_app.config.get('COLLEGE_NAME', 'COLLEGE NAME'), title_style))
    elements.append(Paragraph(current_app.config.get('COLLEGE_AFFILIATION', ''), sub_title_style))
    elements.append(Paragraph(current_app.config.get('COLLEGE_ADDRESS', '') + " | " + current_app.config.get('COLLEGE_CONTACT', ''), sub_title_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0d47a1'), spaceAfter=12))

    # 2. Document Title
    elements.append(Paragraph("OFFICIAL STATEMENT OF MARKS", doc_heading))
    elements.append(Paragraph(f"<b>Examination:</b> {result['exam']['exam_name']} (Academic Year: {result['exam']['academic_year']})", sub_title_style))
    elements.append(Spacer(1, 12))

    # 3. Student Information Table
    st = result['student']
    student_info_data = [
        [
            Paragraph("<b>Roll Number:</b>", cell_bold), Paragraph(st['roll_number'], cell_style),
            Paragraph("<b>Date of Birth:</b>", cell_bold), Paragraph(str(st['dob']), cell_style)
        ],
        [
            Paragraph("<b>Student Name:</b>", cell_bold), Paragraph(st['student_name'], cell_style),
            Paragraph("<b>Gender:</b>", cell_bold), Paragraph(st['gender'], cell_style)
        ],
        [
            Paragraph("<b>Father's Name:</b>", cell_bold), Paragraph(st['father_name'], cell_style),
            Paragraph("<b>Class & Sem:</b>", cell_bold), Paragraph(f"{st['class_name']} - Semester {st['semester']}", cell_style)
        ]
    ]

    t_info = Table(student_info_data, colWidths=[90, 170, 90, 170])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cfd8dc')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#eceff1')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 15))

    # 4. Subject Marks Table
    marks_data = [
        [
            Paragraph("<b>Subject Code</b>", cell_bold),
            Paragraph("<b>Subject Name</b>", cell_bold),
            Paragraph("<b>Max Marks</b>", cell_bold),
            Paragraph("<b>Passing Marks</b>", cell_bold),
            Paragraph("<b>Obtained</b>", cell_bold),
            Paragraph("<b>Grade</b>", cell_bold),
            Paragraph("<b>Status</b>", cell_bold)
        ]
    ]

    for sub in result['subjects']:
        status_color = '#2e7d32' if sub['status'] == 'PASS' else ('#c62828' if sub['status'] == 'FAIL' else '#f57f17')
        marks_data.append([
            Paragraph(sub['subject_code'], cell_style),
            Paragraph(sub['subject_name'], cell_style),
            Paragraph(str(int(sub['max_marks'])), cell_style),
            Paragraph(str(int(sub['passing_marks'])), cell_style),
            Paragraph(str(sub['marks_obtained']) if sub['marks_obtained'] is not None else '-', cell_style),
            Paragraph(sub['grade'], cell_style),
            Paragraph(f"<font color='{status_color}'><b>{sub['status']}</b></font>", cell_style)
        ])

    t_marks = Table(marks_data, colWidths=[80, 180, 55, 60, 55, 45, 45])
    t_marks.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d47a1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b0bec5')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fbfbfb')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_marks)
    elements.append(Spacer(1, 15))

    # 5. Grand Summary Box
    summary_bg = colors.HexColor('#e8f5e9') if result['status'] == 'PASS' else colors.HexColor('#ffebee')
    status_font_color = '#1b5e20' if result['status'] == 'PASS' else '#b71c1c'
    
    summary_data = [
        [
            Paragraph("<b>Total Maximum Marks:</b>", cell_bold),
            Paragraph(str(int(result['total_max'])), cell_style),
            Paragraph("<b>Percentage:</b>", cell_bold),
            Paragraph(f"<b>{result['percentage']}%</b>", cell_style)
        ],
        [
            Paragraph("<b>Total Obtained Marks:</b>", cell_bold),
            Paragraph(f"<b>{result['total_obtained']}</b>", cell_style),
            Paragraph("<b>Overall Grade:</b>", cell_bold),
            Paragraph(f"<b>{result['grade']}</b>", cell_style)
        ],
        [
            Paragraph("<b>Final Academic Result:</b>", cell_bold),
            Paragraph(f"<font size='11' color='{status_font_color}'><b>{result['status']}</b></font>", cell_bold),
            Paragraph("<b>Remarks:</b>", cell_bold),
            Paragraph("PASSED IN ALL SUBJECTS" if result['status'] == 'PASS' else "FAILED IN ONE OR MORE SUBJECTS", cell_style)
        ]
    ]

    t_summary = Table(summary_data, colWidths=[120, 140, 120, 140])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), summary_bg),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#90caf9')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cfd8dc')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 40))

    # 6. Signatures Footer
    sig_data = [
        [
            Paragraph("________________________<br/><b>Prepared By (Staff)</b>", cell_style),
            Paragraph("________________________<br/><b>Verified By (HOD)</b>", cell_style),
            Paragraph("________________________<br/><b>Controller of Examinations</b>", cell_style)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[170, 170, 180])
    t_sig.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_sig)

    doc.build(elements)
    buffer.seek(0)

    filename = f"Marksheet_{st['roll_number']}_{result['exam']['academic_year']}.pdf"
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
