import pyodbc
from fpdf import FPDF
from flask import Flask, Response, request, abort
import os

app = Flask(__name__)

# --- Configuration ---
# Get database path from environment variable for flexibility
# This path will be INSIDE the Docker container.
DATABASE_PATH = os.environ.get("ACCESS_DB_PATH", "/app/data/Academic.accdb")

# Global connection (for simplicity, but consider connection pooling in production)
conn = None
cursor = None

def get_db_connection():
    global conn, cursor
    if conn is None:
        try:
            # Ensure the driver is installed in the environment where the microservice runs
            # Note: The driver name might vary slightly based on your ODBC setup on Linux
            # 'Microsoft Access Driver (*.mdb, *.accdb)' is typically for Windows.
            # On Linux, with unixodbc and mdbtools, it might be 'MDBTools ODBC Driver'
            # or similar. You might need to adjust this driver name.
            conn = pyodbc.connect(f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DATABASE_PATH}")
            cursor = conn.cursor()
        except pyodbc.Error as ex:
            sqlstate = ex.args[0]
            print(f"Database connection error: {sqlstate}")
            # Log the full exception for debugging in production
            abort(500, description="Could not connect to the database. Check database path and ODBC driver setup.")
    return conn, cursor

class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, 'C')

def fetch_data(query, params=None):
    conn, cursor = get_db_connection()
    cursor.execute(query, params) if params else cursor.execute(query)
    return cursor.fetchall()

# --- API Endpoint ---
@app.route('/transcript/<string:student_id>', methods=['GET'])
def generate_transcript(student_id):
    pdf = PDF()
    pdf.add_page()

    # **Header: Logo**
    # USP_logo.jpg will be copied into the /app directory in the Docker container
    try:
        pdf.image('USP_logo.jpg', x=(pdf.w - 50) / 2, y=5, w=50)
    except RuntimeError:
        print("Warning: USP_logo.jpg not found. Skipping logo.")
    pdf.ln(35)

    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, "Academic Transcript", 0, 1, 'C')
    pdf.ln(10)

    # **Fetch Student Details**
    student_info = fetch_data("""
        SELECT StudentID, Name, DateOfBirth
        FROM StudentDetails
        WHERE StudentID = ?
    """, (student_id,))

    if not student_info:
        abort(404, description=f"Student ID {student_id} not found.")

    student_id_retrieved, student_name, dob = student_info[0]
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Student ID      : {student_id_retrieved}", 0, 1, 'L')
    pdf.cell(0, 10, f"Student Name    : {student_name}", 0, 1, 'L')
    pdf.cell(0, 10, f"Date of Birth : {dob}", 0, 1, 'L')
    pdf.ln(5)

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
            pdf.cell(column_widths[0], 10, str(term), 1, 0, 'C')
            pdf.cell(column_widths[1], 10, str(course_id), 1, 0, 'C')
            pdf.cell(column_widths[2], 10, str(course_name), 1, 0, 'C')
            pdf.cell(column_widths[3], 10, str(grade), 1, 0, 'C')
            pdf.ln()

            if grade not in ["IP"]:
                total_points += grade_points.get(grade, 0)
                total_courses += 1

    # **Calculate & Print GPA**
    gpa = total_points / total_courses if total_courses > 0 else 0.0
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Overall GPA: {gpa:.2f}", 0, 1, 'C')

    pdf_output_bytes = pdf.output(dest='S').encode('latin1') # 'S' returns as string, then encode

    # Close the connection and cursor after processing the request
    # For production, consider connection pooling instead of global connection
    if conn:
        conn.close()
        global conn, cursor
        conn = None
        cursor = None

    return Response(pdf_output_bytes, mimetype='application/pdf')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)