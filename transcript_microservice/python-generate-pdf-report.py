import pyodbc
from fpdf import FPDF

# Database Path
DATABASE_PATH = r"C:\Users\deosh\OneDrive\Desktop\Python_pdf\efb773658fe13955b7f661239183f0d8-e9d28046cca868fbb98a7420f4f33f61dd33d6df\Academic.accdb"

# Connect to Microsoft Access Database
conn = pyodbc.connect(r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + DATABASE_PATH)
cursor = conn.cursor()

class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, 'C')

def fetch_data(query, params=None):
    cursor.execute(query, params) if params else cursor.execute(query)
    return cursor.fetchall()

def main():
    student_id = input("Enter Student ID: ").strip()  # Ask user for StudentID input

    pdf = PDF()
    pdf.add_page()

    # **Header: Logo**
    pdf.image('USP_logo.jpg', x=(pdf.w - 50) / 2, y=5, w=50)  # Adjust logo placement
    pdf.ln(35)  # Space for the logo

    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, "Academic Transcript", 0, 1, 'C')  # Print title
    pdf.ln(10)  # Add spacing before student details

    # **Fetch Student Details**
    student_info = fetch_data("""
        SELECT StudentID, Name, DateOfBirth 
        FROM StudentDetails 
        WHERE StudentID = ?
    """, (student_id,))

    if student_info:
        student_id, student_name, dob = student_info[0]
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"Student ID    : {student_id}", 0, 1, 'L')
        pdf.cell(0, 10, f"Student Name  : {student_name}", 0, 1, 'L')
        pdf.cell(0, 10, f"Date of Birth : {dob}", 0, 1, 'L')

    pdf.ln(5)  # Space before table

    # **Table Headers**
    pdf.set_font('Arial', 'B', 10)
    headers = ["Term", "CourseID", "Course Name", "Grade"]
    column_widths = [25, 25, 100, 30]

    for i, header in enumerate(headers):
        pdf.cell(column_widths[i], 10, header, 1, 0, 'C')
    pdf.ln()

    # **Fetch Student Course Details**
    enrollment_records = fetch_data("""
        SELECT EnrollmentDetails.Term, EnrollmentDetails.CourseID, CourseDetails.Title, GradeDetails.Grade
        FROM ((EnrollmentDetails 
        INNER JOIN CourseDetails ON EnrollmentDetails.CourseID = CourseDetails.CourseID)
        INNER JOIN GradeDetails ON EnrollmentDetails.EnrollmentID = GradeDetails.EnrollmentID)
        WHERE EnrollmentDetails.StudentID = ?
    """, (student_id,))

    total_points, total_courses = 0, 0
    grade_points = {'A+': 4.3, 'A': 4.0, 'A-': 3.7,
                    'B+': 3.3, 'B': 3.0, 'B-': 2.7,
                    'C+': 2.3, 'C': 2.0, 'C-': 1.7,
                    'D+': 1.3, 'D': 1.0, 'D-': 0.7,
                    'F': 0.0}

    if not enrollment_records:
        pdf.cell(0, 10, f"No records found for Student ID {student_id}.", 1, 1, 'C')
    else:
        pdf.set_font('Arial', '', 10)
        for row in enrollment_records:
            term, course_id, course_name, grade = row
            pdf.cell(column_widths[0], 10, term, 1, 0, 'C')
            pdf.cell(column_widths[1], 10, course_id, 1, 0, 'C')
            pdf.cell(column_widths[2], 10, course_name, 1, 0, 'C')
            pdf.cell(column_widths[3], 10, grade, 1, 0, 'C')
            pdf.ln()

            if grade not in ["IP"]:  # Exclude "IP" grades from GPA calculation
                total_points += grade_points.get(grade, 0)
                total_courses += 1

    # **Calculate & Print GPA**
    gpa = total_points / total_courses if total_courses > 0 else 0.0
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Overall GPA: {gpa:.2f}", 0, 1, 'C')  # Display GPA at the end

    # Output the final PDF
    pdf.output(f'Student_{student_id}_Transcript.pdf', 'F')
    conn.close()

if __name__ == '__main__':
    main()