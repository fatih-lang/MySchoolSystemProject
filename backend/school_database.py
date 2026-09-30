import sqlite3
import hashlib
import secrets
import os
import shutil
from datetime import datetime, date


DATABASE_NAME = "python_school.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME, timeout=10)

    # Allows us to access columns by name:
    # row["student_name"]
    connection.row_factory = sqlite3.Row

    # SQLite does not enforce foreign keys unless we enable them.
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    # ==========================================================
    # 1. ADMINS
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            email_address TEXT,
            status TEXT NOT NULL DEFAULT 'Active',
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL
        )
    """)
    
    # ----------------------------------------------------------
    # Add category to the admins table if it does not already
    # exist. This upgrades older databases safely.
    # ----------------------------------------------------------
    
    cursor.execute("PRAGMA table_info(admins)")
    admin_columns = cursor.fetchall()
    
    # Get the names of all columns currently in the admins table.
    column_names = [column[1] for column in admin_columns]
    
    # Only add category if the database does not already have it.
    if "category" not in column_names:
        cursor.execute("""
            ALTER TABLE admins
            ADD COLUMN category TEXT NOT NULL DEFAULT 'Reception'
        """)
    
    
    # ----------------------------------------------------------
    # Add missing administrator login columns to older databases.
    # ----------------------------------------------------------
    
    cursor.execute("PRAGMA table_info(admins)")
    admin_columns = cursor.fetchall()
    
    # Get all existing column names.
    column_names = [column[1] for column in admin_columns]
    
    # Add failed_attempts if it does not exist.
    if "failed_attempts" not in column_names:
        cursor.execute("""
            ALTER TABLE admins
            ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0
        """)
    
    # Add email_address if it does not exist.
    if "email_address" not in column_names:
        cursor.execute("""
            ALTER TABLE admins
            ADD COLUMN email_address TEXT
        """)
    
    # Add status if it does not exist.
    if "status" not in column_names:
        cursor.execute("""
            ALTER TABLE admins
            ADD COLUMN status TEXT NOT NULL DEFAULT 'Active'
        """)
    
    
    
    # Admin audit log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs(

            log_id INTEGER PRIMARY KEY AUTOINCREMENT,

            admin_name TEXT NOT NULL,
            
            category TEXT NOT NULL,
            
            action TEXT NOT NULL,

            teacher_number INTEGER,
            
            student_number INTEGER,
            
            admin_id INTEGER,

            action_time DATETIME DEFAULT CURRENT_TIMESTAMP

        )
    """)


    # ==========================================================
    # 2. GRADES
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade_name TEXT NOT NULL UNIQUE
        )
    """)


    # ==========================================================
    # 3. STUDENTS
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_number INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            id_number TEXT NOT NULL UNIQUE,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            nationality TEXT NOT NULL,
            classroom TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active',
            login_locked TEXT,

            grade_id INTEGER NOT NULL,

            fees_balance REAL NOT NULL DEFAULT 0,

            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            failed_attempts INTEGER NOT NULL DEFAULT 0,

            FOREIGN KEY (grade_id)
             REFERENCES grades(grade_id)
        )
    """)
    
    # I had forgot to add a surname so IAM adding it to the table since we alrdy had students in the table without surname we won't use null.
    
    # ----------------------------------------------------------
    # Add student_surname to the existing students table
    # if the column does not already exist.
    # ----------------------------------------------------------
    
    # Check the columns that currently exist in the students table.
    cursor.execute("PRAGMA table_info(students)")
    
    # Get all existing columns.
    student_columns = cursor.fetchall()
    
    # Create a list containing the names of the existing columns.
    column_names = [column[1] for column in student_columns]
    
    # Add the surname column only if it does not already exist.
    if "student_surname" not in column_names:
    
        cursor.execute("""
            ALTER TABLE students
            ADD COLUMN student_surname TEXT
        """)


    # ==========================================================
    # 4. GUARDIANS
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guardians (
            guardian_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            email TEXT,
            address TEXT NOT NULL,

            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            
            failed_attempts INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Active'
        )
    """)


    # ==========================================================
    # 5. GUARDIAN-STUDENT RELATIONSHIP
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guardian_students (
            guardian_id INTEGER NOT NULL,
            student_number INTEGER NOT NULL,
            relationship TEXT NOT NULL,

            PRIMARY KEY (guardian_id, student_number),

            FOREIGN KEY (guardian_id)
                REFERENCES guardians(guardian_id)
                ON DELETE CASCADE,

            FOREIGN KEY (student_number)
                REFERENCES students(student_number)
                ON DELETE CASCADE
        )
    """)


    # ==========================================================
    # 6. TEACHERS
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_number INTEGER PRIMARY KEY AUTOINCREMENT,
    
            teacher_name TEXT NOT NULL,
            id_number TEXT NOT NULL UNIQUE,
    
            gender TEXT NOT NULL,
            nationality TEXT NOT NULL,
    
            email_address TEXT NOT NULL,
    
            failed_attempts INTEGER NOT NULL DEFAULT 0,
    
            status TEXT NOT NULL DEFAULT 'Active',
    
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL
        )
    """)


    # ==========================================================
    # 7. SUBJECTS
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL UNIQUE,
            phase_name TEXT
        )
    """)


    # ==========================================================
    # 8. TEACHER-SUBJECT ASSIGNMENTS
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_subjects (
            teacher_subject_id INTEGER PRIMARY KEY AUTOINCREMENT,

            teacher_number INTEGER NOT NULL,
            subject_name INTEGER NOT NULL,
            grade_name INTEGER NOT NULL,

            FOREIGN KEY (teacher_number)
                REFERENCES teachers(teacher_number)
                ON DELETE CASCADE,

            FOREIGN KEY (subject_name)
                REFERENCES subjects(subject_name)
                ON DELETE CASCADE,

            FOREIGN KEY (grade_name)
                REFERENCES grades(grade_name)
                ON DELETE CASCADE,

            UNIQUE (teacher_number, subject_name, grade_name)
        )
    """)


    # ==========================================================
    # 9. MARKS
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            mark_id INTEGER PRIMARY KEY AUTOINCREMENT,

            mark_value REAL NOT NULL,
            total_possible REAL NOT NULL,
            exam_date TEXT NOT NULL,

            student_number INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            teacher_number INTEGER NOT NULL,

            FOREIGN KEY (student_number)
                REFERENCES students(student_number)
                ON DELETE CASCADE,

            FOREIGN KEY (subject_id)
                REFERENCES subjects(subject_id)
                ON DELETE CASCADE,

            FOREIGN KEY (teacher_number)
                REFERENCES teachers(teacher_number)
                ON DELETE CASCADE
        )
    """)


    # ==========================================================
    # 10. ATTENDANCE
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,

            attendance_date TEXT NOT NULL,
            status TEXT NOT NULL,

            student_number INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            teacher_number INTEGER NOT NULL,

            FOREIGN KEY (student_number)
                REFERENCES students(student_number)
                ON DELETE CASCADE,

            FOREIGN KEY (subject_id)
                REFERENCES subjects(subject_id)
                ON DELETE CASCADE,

            FOREIGN KEY (teacher_number)
                REFERENCES teachers(teacher_number)
                ON DELETE CASCADE,

            UNIQUE (
                attendance_date,
                student_number,
                subject_id
            )
        )
    """)


    # ==========================================================
    # 11. HOMEWORK
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS homework (
            homework_id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,
            description TEXT,

            due_date TEXT NOT NULL,
            date_posted TEXT NOT NULL,

            grade_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            teacher_number INTEGER NOT NULL,

            FOREIGN KEY (grade_id)
                REFERENCES grades(grade_id)
                ON DELETE CASCADE,

            FOREIGN KEY (subject_id)
                REFERENCES subjects(subject_id)
                ON DELETE CASCADE,

            FOREIGN KEY (teacher_number)
                REFERENCES teachers(teacher_number)
                ON DELETE CASCADE
        )
    """)


    # ==========================================================
    # 12. HOMEWORK SUBMISSIONS
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS homework_submissions (
            submission_id INTEGER PRIMARY KEY AUTOINCREMENT,

            homework_id INTEGER NOT NULL,
            student_number INTEGER NOT NULL,

            submission_text TEXT,
            file_path TEXT,

            submitted_date TEXT,

            status TEXT NOT NULL DEFAULT 'Not Submitted',

            marked_date TEXT,

            teacher_number INTEGER,
            
            mark REAL,
            
            total_possible REAL,

            FOREIGN KEY (homework_id)
                REFERENCES homework(homework_id)
                ON DELETE CASCADE,

            FOREIGN KEY (student_number)
                REFERENCES students(student_number)
                ON DELETE CASCADE,

            FOREIGN KEY (teacher_number)
                REFERENCES teachers(teacher_number)
                ON DELETE SET NULL,

            UNIQUE (homework_id, student_number)
        )
    """)


    # ==========================================================
    # 13. TEACHER ACTIVITY
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_activity (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,

            teacher_number INTEGER NOT NULL,

            activity_type TEXT NOT NULL,
            activity_description TEXT NOT NULL,
            activity_date TEXT NOT NULL,

            FOREIGN KEY (teacher_number)
                REFERENCES teachers(teacher_number)
                ON DELETE CASCADE
        )
    """)


    # ==========================================================
    # 14. SCHOOL NEWS
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS school_news (
            news_id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,
            content TEXT NOT NULL,

            date_posted TEXT NOT NULL,

            category TEXT NOT NULL DEFAULT 'General',

            admin_id INTEGER NOT NULL,

            grade_id INTEGER,

            FOREIGN KEY (admin_id)
                REFERENCES admins(admin_id)
                ON DELETE CASCADE,

            FOREIGN KEY (grade_id)
                REFERENCES grades(grade_id)
                ON DELETE CASCADE
        )
    """)


    # ==========================================================
    # 15. TIMETABLE
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            timetable_id INTEGER PRIMARY KEY AUTOINCREMENT,

            grade_id INTEGER NOT NULL,
            classroom TEXT NOT NULL,

            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,

            subject_id INTEGER NOT NULL,
            teacher_number INTEGER NOT NULL,

            FOREIGN KEY (grade_id)
                REFERENCES grades(grade_id)
                ON DELETE CASCADE,

            FOREIGN KEY (subject_id)
                REFERENCES subjects(subject_id)
                ON DELETE CASCADE,

            FOREIGN KEY (teacher_number)
                REFERENCES teachers(teacher_number)
                ON DELETE CASCADE
        )
    """)


    # ==========================================================
    # 16. FEES STRUCTURE
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fees_structure (
            fees_id INTEGER PRIMARY KEY AUTOINCREMENT,

            grade_id INTEGER NOT NULL,
            
            amount REAL NOT NULL,

            FOREIGN KEY (grade_id)
                REFERENCES grades(grade_id)
                ON DELETE CASCADE,

            UNIQUE (grade_id)
        )
    """)


    # ==========================================================
    # 17. FEE PAYMENTS
    # ==========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fee_payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_number INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            term_number INTEGER DEFAULT 1,
            school_year INTEGER DEFAULT 2026,

            FOREIGN KEY (student_number)
                REFERENCES students(student_number)
                ON DELETE CASCADE
        )
    """)

    
    # ----------------------------------------------------------
    # STUDENT SUBJECTS TABLE
    # ----------------------------------------------------------
    # This table stores which subjects each student takes.
    #
    # Example:
    #
    # 1000053 | ECONOMICS
    # 1000053 | HISTORY
    #
    # This means Muhammad takes Economics and History.
    # ----------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_subjects (
            student_subject_id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- The student who takes the subject.
            student_number INTEGER NOT NULL,

            -- The name of the subject the student takes.
            subject_name TEXT NOT NULL,

            -- Connect the student to the students table.
            FOREIGN KEY (student_number)
                REFERENCES students(student_number)
                ON DELETE CASCADE,

            -- Connect the subject name to the subjects table.
            FOREIGN KEY (subject_name)
                REFERENCES subjects(subject_name)
                ON DELETE CASCADE,

            -- Prevent the same student from being
            -- registered for the same subject twice.
            UNIQUE (student_number, subject_name)
        )
    """)
    
    
    
    
    # ----------------------------------------------------------
    # PHASE SUBJECTS TABLE
    # ----------------------------------------------------------
    # This table connects school phases to subjects.
    #
    # The school has four main phases:
    #
    # Foundation Phase:
    #     Grade R - Grade 3
    #
    # Intermediate Phase:
    #     Grade 4 - Grade 6
    #
    # Senior Phase:
    #     Grade 7 - Grade 9
    #
    # FET Phase:
    #     Grade 10 - Grade 12
    #
    # Grade 12RW (rewriting) is also treated as part of the
    # FET Phase.
    #
    # ----------------------------------------------------------
    # WHY DO WE NEED THIS TABLE?
    # ----------------------------------------------------------
    #
    # The subjects table stores the subjects themselves.
    #
    # For example:
    #
    #     subject_id = 1
    #     subject_name = MATHEMATICS
    #
    # A subject can be used in more than one school phase.
    #
    # For example, Mathematics may be offered in:
    #
    #     Foundation Phase
    #     Intermediate Phase
    #     Senior Phase
    #     FET Phase
    #
    # Therefore, we should NOT put the phase directly into the
    # subjects table.
    #
    # Instead, this table creates a relationship between a phase
    # and a subject.
    #
    # ----------------------------------------------------------
    # EXAMPLE
    # ----------------------------------------------------------
    #
    # The table could contain:
    #
    #     Foundation Phase  -> Mathematics
    #     Intermediate Phase -> Mathematics
    #     Senior Phase       -> Mathematics
    #     FET Phase          -> Mathematics
    #
    # All of these can point to the same:
    #
    #     subject_id = 1
    #
    # ----------------------------------------------------------
    # PHASE NAME
    # ----------------------------------------------------------
    #
    # The phase_name column stores the school phase.
    #
    # Examples:
    #
    #     Foundation Phase
    #     Intermediate Phase
    #     Senior Phase
    #     FET Phase
    #
    # ----------------------------------------------------------
    # SUBJECT ID
    # ----------------------------------------------------------
    #
    # The subject_id column connects this table to the
    # subjects table.
    #
    # For example:
    #
    #     subject_id = 1
    #
    # refers to:
    #
    #     MATHEMATICS
    #
    # And:
    #
    #     subject_id = 13
    #
    # refers to:
    #
    #     AFRIKAANS
    #
    # ----------------------------------------------------------
    # UNIQUE CONSTRAINT
    # ----------------------------------------------------------
    #
    # The UNIQUE constraint prevents the same subject from being
    # added to the same phase more than once.
    #
    # For example, this combination:
    #
    #     FET Phase + Mathematics
    #
    # can only appear once.
    #
    # ----------------------------------------------------------
    # FOREIGN KEY
    # ----------------------------------------------------------
    #
    # The subject_id is a foreign key connected to the
    # subjects table.
    #
    # This helps ensure that a phase cannot be connected to a
    # subject that does not exist in the subjects table.
    #
    # ----------------------------------------------------------
    # PHASE-SUBJECT RELATIONSHIP
    # ----------------------------------------------------------
    #
    # This is a many-to-many relationship:
    #
    #     One phase can have MANY subjects.
    #
    #     One subject can belong to MANY phases.
    #
    # This table sits between the phases and subjects to manage
    # that relationship.
    # ----------------------------------------------------------
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phase_subjects (
            phase_subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
            phase_name TEXT NOT NULL,
    
            subject_id INTEGER NOT NULL,
    
            FOREIGN KEY (subject_id)
                REFERENCES subjects(subject_id)
                ON DELETE CASCADE,
    
            UNIQUE (phase_name, subject_id)
        )
    """)
    
    
    
    
    
    # ----------------------------------------------------------
    # SCHOOL TERMS TABLE
    # ----------------------------------------------------------
    # The school year has 4 terms.
    #
    # Each term represents 3 months.
    #
    # The fees_structure table stores the FULL YEAR fee.
    # This table stores the individual school terms so that
    # we can control report-card access based on term payments.
    # ----------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS school_terms (

            term_id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- School year, for example 2026.
            school_year INTEGER NOT NULL,

            -- Term number: 1, 2, 3 or 4.
            term_number INTEGER NOT NULL,

            -- Date the term starts.
            start_date TEXT NOT NULL,

            -- Date the term ends.
            end_date TEXT NOT NULL,

            -- Amount that must be paid for this term.
            required_amount REAL NOT NULL,

            -- Only one record for each term in a school year.
            UNIQUE (school_year, term_number)
        )
    """)  
    
    
    # ---------------------------------------------------------
    # INSERT 2026 SCHOOL TERMS
    # ---------------------------------------------------------
    # These dates are only inserted if they don't already exist.
    # Therefore, running the program again will NOT create
    # duplicate terms.

    school_terms = [
        (2026, 1, "2026-01-01", "2026-03-31"),
        (2026, 2, "2026-04-01", "2026-06-30"),
        (2026, 3, "2026-07-01", "2026-09-30"),
        (2026, 4, "2026-10-01", "2026-12-31")
    ]

    for school_year, term_number, start_date, end_date in school_terms:

        # Check whether this school year and term already exist.
        cursor.execute("""
            SELECT term_id
            FROM school_terms
            WHERE school_year = ?
            AND term_number = ?
        """, (school_year, term_number))

        existing_term = cursor.fetchone()

        # Insert the term only if it doesn't already exist.
        if existing_term is None:

            cursor.execute("""
                INSERT INTO school_terms (
                    school_year,
                    term_number,
                    start_date,
                    end_date,
                    required_amount
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                school_year,
                term_number,
                start_date,
                end_date,
                0
            ))
            
            
            
            
    # ----------------------------------------------------------
    # STUDENT DOCUMENTS TABLE
    # ----------------------------------------------------------
    # This table stores official PDF documents uploaded by the
    # school for individual students.
    #
    # Examples of documents that can be uploaded:
    # - Student report
    # - Progress report
    # - School circular
    # - Academic notice
    # - Other official school documents
    #
    # One student can have MANY documents.
    #
    # Therefore, we do NOT store the PDF directly inside the
    # students table. Instead, every uploaded document gets
    # its own row in this table.
    #
    # The file_path column stores the location of the PDF file.
    #
    # The student_number connects the document to the student.
    #
    # The admin_id records which administrator uploaded the
    # document.
    #
    # Fee access will NOT be stored in this table.
    # When a student tries to view/download a document, the
    # system will check the student's current fee balance.
    #
    # If the student has a balance greater than R0.00:
    #     Document access = BLOCKED
    #
    # If the student has fully paid:
    #     Document access = ALLOWED
    # ----------------------------------------------------------        
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_documents (
            document_id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_number INTEGER NOT NULL,

            document_title TEXT NOT NULL,

            document_type TEXT NOT NULL,

            file_path TEXT NOT NULL,

            uploaded_date TEXT NOT NULL,

            admin_id INTEGER,
            
            term_number INTEGER,

            FOREIGN KEY (student_number)
                REFERENCES students(student_number)
                ON DELETE CASCADE,

            FOREIGN KEY (admin_id)
                REFERENCES admins(admin_id)
        )
    """)        


    connection.commit()
    connection.close()
    

def register_student_db(
    student_name,
    student_surname,
    id_number,
    age,
    gender,
    nationality,
    classroom,
    grade_id,
    fees_balance,
    password_hash,
    password_salt
):
    # Open a connection to our SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    # ----------------------------------------------------------
    # Find the highest student number currently in the database.
    # ----------------------------------------------------------
    #
    # MAX() finds the largest student number.
    #
    # If there are no students yet, MAX() will return None.
    cursor.execute("""
        SELECT MAX(student_number)
        FROM students
    """)

    # Get the result of our SELECT query.
    result = cursor.fetchone()

    # The result contains the highest student number.
    last_student = result[0]

    # ----------------------------------------------------------
    # Create the new student number.
    # ----------------------------------------------------------

    if last_student is None:
        # There are no students in the database yet.
        # We will start with your existing numbering system.
        student_number = 1000045

    else:
        # If students already exist, increase the highest
        # student number by 1.
        student_number = last_student + 1

    # ----------------------------------------------------------
    # Insert the new student.
    # ----------------------------------------------------------

    cursor.execute("""
        INSERT INTO students (
            student_number,
            student_name,
            student_surname,
            id_number,
            age,
            gender,
            nationality,
            classroom,
            grade_id,
            fees_balance,
            password_hash,
            password_salt
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_number,
        student_name,
        student_surname,
        id_number,
        age,
        gender,
        nationality,
        classroom,
        grade_id,
        fees_balance,
        password_hash,
        password_salt
    ))

    # Save the INSERT operation permanently.
    connection.commit()

    # Close the database connection.
    connection.close()

    # Return the newly created student number.
    return student_number
    


# Keep register_student_db() exactly as it is
# Don't replace it.
# We're going to add a separate function that retrieves all subjects so the admin can choose them.
def get_all_subjects_db():
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    # ----------------------------------------------------------
    # Get every subject from the subjects table.
    #
    # We order them alphabetically so the admin gets
    # a consistent numbered list.
    # ----------------------------------------------------------
    cursor.execute("""
        SELECT subject_id, subject_name
        FROM subjects
        ORDER BY subject_name
    """)

    # Get all subjects from the database.
    subjects = cursor.fetchall()

    # Close the database connection.
    connection.close()

    # Return the subjects to the registration menu.
    return subjects  
    




def get_phase_for_grade(grade_name):
    """
    Determine which school phase a grade belongs to.

    The phase is used during student registration to decide
    which subjects are available for that learner.

    Phase structure:

        Foundation Phase:
            Grade R - Grade 3

        Intermediate Phase:
            Grade 4 - Grade 6

        Senior Phase:
            Grade 7 - Grade 9

        FET Phase:
            Grade 10 - Grade 12
            Grade 12RW is also treated as FET.

        Old Curriculum:
            This is kept in the database, but it is not
            automatically assigned to a modern phase.
    """

    # Remove spaces from the beginning and end.
    grade_name = str(grade_name).strip()

    # ----------------------------------------------------------
    # Foundation Phase
    # ----------------------------------------------------------
    if grade_name in ("R", "1", "2", "3"):
        return "Foundation Phase"

    # ----------------------------------------------------------
    # Intermediate Phase
    # ----------------------------------------------------------
    elif grade_name in ("4", "5", "6"):
        return "Intermediate Phase"

    # ----------------------------------------------------------
    # Senior Phase
    # ----------------------------------------------------------
    elif grade_name in ("7", "8", "9"):
        return "Senior Phase"

    # ----------------------------------------------------------
    # FET Phase
    #
    # Grade 12RW is included because re-writing Grade 12
    # follows the FET subject structure in this system.
    # ----------------------------------------------------------
    elif grade_name in ("10", "11", "12", "12RW"):
        return "FET Phase"

    # ----------------------------------------------------------
    # Old Curriculum
    #
    # We deliberately do not assign this to a modern phase.
    # ----------------------------------------------------------
    elif grade_name == "Old Curriculum":
        return None

    # ----------------------------------------------------------
    # Unknown grade
    # ----------------------------------------------------------
    return None
    
    
    


def get_subjects_for_phase_db(phase_name):
    """
    Get all subjects belonging to a particular school phase.

    The phase_subjects table is the source of truth.

    This means we do not hard-code the subject list in Python.
    If the school changes which subjects are offered in a phase,
    the database mapping can be updated.
    """

    # Open the SQLite database.
    connection = get_connection()

    # Create a cursor for running SQL commands.
    cursor = connection.cursor()

    try:
        # ------------------------------------------------------
        # Get the subjects connected to this phase.
        #
        # We join phase_subjects with subjects so that we get
        # the subject ID and the subject name.
        # ------------------------------------------------------
        cursor.execute("""
            SELECT
                subjects.subject_id,
                subjects.subject_name
            FROM phase_subjects
            INNER JOIN subjects
                ON phase_subjects.subject_id = subjects.subject_id
            WHERE phase_subjects.phase_name = ?
            ORDER BY subjects.subject_id
        """, (phase_name,))

        # Convert the database rows into dictionaries.
        subjects = [dict(row) for row in cursor.fetchall()]

        return subjects

    finally:
        # Always close the database connection.
        connection.close()




    
# Create the multiple-selection function    
def select_multiple_student_subjects(grade_name):
    """
    Allow the administrator to select subjects for a student.

    The subjects displayed depend on the student's grade.

    The system first determines the student's phase and then
    gets the available subjects from the phase_subjects table.

    Important:
        FET and Grade 12RW do NOT have a hard-coded subject
        combination rule.

        The administrator selects the subjects according to
        the school's own subject-combination rules.
    """

    # ----------------------------------------------------------
    # Determine the phase for this student's grade.
    # ----------------------------------------------------------
    phase_name = get_phase_for_grade(grade_name)

    # ----------------------------------------------------------
    # Old Curriculum does not have a modern phase mapping.
    # ----------------------------------------------------------
    if phase_name is None:

        if grade_name == "Old Curriculum":
            raise ValueError(
                "Old Curriculum does not have a phase mapping. "
                "Please configure its subjects separately."
            )

        raise ValueError(
            f"Unable to determine the phase for grade {grade_name}."
        )

    # ----------------------------------------------------------
    # Get only the subjects belonging to this phase.
    # ----------------------------------------------------------
    subjects = get_subjects_for_phase_db(phase_name)

    # Make sure the phase actually has subjects configured.
    if not subjects:
        raise ValueError(
            f"No subjects have been configured for {phase_name}."
        )

    # ----------------------------------------------------------
    # Display the phase being used.
    # ----------------------------------------------------------
    print("\n===== SUBJECT SELECTION =====")
    print(f"Grade: {grade_name}")
    print(f"Phase: {phase_name}")

    # ----------------------------------------------------------
    # Display the subjects available for this phase.
    #
    # The numbers shown here are selection numbers.
    # They are NOT the database subject IDs.
    # ----------------------------------------------------------
    print("\nAvailable subjects:")

    for number, subject in enumerate(subjects, start=1):
        print(
            f"{number}. {subject['subject_name']}"
        )

    # ----------------------------------------------------------
    # Ask the administrator to select multiple subjects.
    #
    # Example:
    #
    # 1,4,7,8
    #
    # The administrator can choose the combination required
    # by the school.
    # ----------------------------------------------------------
    selection = input(
        "\nEnter subject numbers separated by commas: "
    ).strip()

    # Stop if nothing was entered.
    if not selection:
        raise ValueError(
            "You must select at least one subject."
        )

    # This list will contain the selected subject names.
    selected_subject_names = []

    # Split the input at each comma.
    selected_numbers = selection.split(",")

    # ----------------------------------------------------------
    # Process every selected subject number.
    # ----------------------------------------------------------
    for number in selected_numbers:

        # Remove spaces around the number.
        number = number.strip()

        # Make sure the value is numeric.
        if not number.isdigit():
            raise ValueError(
                f"Invalid subject number: {number}"
            )

        # Convert the number to an integer.
        number = int(number)

        # Make sure the selection number exists.
        if number < 1 or number > len(subjects):
            raise ValueError(
                f"Subject number {number} does not exist."
            )

        # Get the selected subject.
        selected_subject = subjects[number - 1]

        # Get the subject name.
        subject_name = selected_subject["subject_name"]

        # ------------------------------------------------------
        # Prevent the same subject from being selected twice.
        # ------------------------------------------------------
        if subject_name not in selected_subject_names:
            selected_subject_names.append(subject_name)

    # ----------------------------------------------------------
    # Display the final selection.
    # ----------------------------------------------------------
    print("\n===== SELECTED SUBJECTS =====")

    for subject_name in selected_subject_names:
        print(f"- {subject_name}")

    # Return the selected subjects to register_student().
    return selected_subject_names     
    
    
    
def log_in(student_number):

    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so we can execute SQL commands.
    cursor = connection.cursor()

    # ----------------------------------------------------------
    # Find the student and also get the student's grade name.
    #
    # The students table stores grade_id.
    # The grades table stores the actual grade name,
    # for example "12", "12RW", or "Old Curriculum".
    # ----------------------------------------------------------
    cursor.execute("""
        SELECT
            s.student_number,
            s.student_name,
            s.id_number,
            s.age,
            s.gender,
            s.nationality,
            s.classroom,
            s.grade_id,
            g.grade_name,
            s.fees_balance,
            s.password_hash,
            s.password_salt,
            s.status

        FROM students s

        JOIN grades g
            ON g.grade_id = s.grade_id

        WHERE s.student_number = ?
    """, (student_number,))

    # Get the student record.
    student = cursor.fetchone()

    # ----------------------------------------------------------
    # Check whether the student exists.
    # ----------------------------------------------------------
    if student is None:

        connection.close()

        return None, "Student not found."

    # ----------------------------------------------------------
    # Check whether the student's account is locked.
    # ----------------------------------------------------------
    if student["status"] == "locked":

        connection.close()

        return None, "Your account is locked. Contact the reception."

    # Close the database connection.
    connection.close()

    # Return the student's database row.
    return student, None
    
    

def login_3timespassword_block(student_number, password):

    connection = get_connection()
    # 🌟 FIX 1: This allows you to use text keys like student["password_salt"]
    connection.row_factory = sqlite3.Row 
    cursor = connection.cursor()

    # 🌟 FIX 2: We select all needed columns at once so nothing gets overwritten
    cursor.execute("""
        SELECT status, password_salt, password_hash, failed_attempts
        FROM students
        WHERE student_number = ?
    """, (student_number,))

    student = cursor.fetchone()

    # If no student matches that number
    if student is None:
        connection.close()
        return False, "Student not found."

    # Check if the account is already locked
    if student["status"] == "locked":
        connection.close()
        return False, "Your account is Blocked. Contact reception."

    # Verify the password
    salt = bytes.fromhex(student["password_salt"])
    password_hash = hashlib.sha256(password.encode() + salt).hexdigest()

    if password_hash == student["password_hash"]:
        # Reset failed attempts back to 0 on success
        cursor.execute("""
            UPDATE students
            SET failed_attempts = 0
            WHERE student_number = ?
        """, (student_number,))

        connection.commit()
        connection.close()
        return True, "Login successful."

    else:
        # Increase failed attempts count by 1
        cursor.execute("""
            UPDATE students
            SET failed_attempts = failed_attempts + 1
            WHERE student_number = ?
        """, (student_number,))
        connection.commit()

        # Check if they have reached 3 or more attempts
        if student["failed_attempts"] + 1 >= 3:
            cursor.execute("""
                UPDATE students
                SET status = 'locked'
                WHERE student_number = ?
            """, (student_number,))
            connection.commit()
            connection.close()
            return False, "Account locked after 3 failed attempts."

        connection.close()
        return False, "Incorrect password."
        


def assign_student_subject_db(student_number, subject_name):
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    try:
        # ----------------------------------------------------------
        # Check that the student exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT student_number, student_name
            FROM students
            WHERE student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

        # Stop if the student does not exist.
        if student is None:
            raise ValueError("Student not found.")

        # ----------------------------------------------------------
        # Check that the subject exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT subject_name
            FROM subjects
            WHERE subject_name = ?
        """, (subject_name,))

        subject = cursor.fetchone()

        # Stop if the subject does not exist.
        if subject is None:
            raise ValueError("Subject not found.")

        # ----------------------------------------------------------
        # Add the subject to this student.
        # ----------------------------------------------------------
        cursor.execute("""
            INSERT INTO student_subjects (
                student_number,
                subject_name
            )
            VALUES (?, ?)
        """, (
            student_number,
            subject_name
        ))

        # Save the changes permanently.
        connection.commit()

        print(
            f"{student['student_name']} assigned to "
            f"{subject['subject_name']}."
        )

    except sqlite3.IntegrityError:
        # The UNIQUE constraint prevents the same student
        # from being assigned the same subject twice.
        connection.rollback()

        raise ValueError(
            "This student is already assigned to this subject."
        )

    except Exception:
        # Undo any changes if another error occurs.
        connection.rollback()

        # Send the error back to the calling function.
        raise

    finally:
        # Always close the database connection.
        connection.close()
        
        

def assign_multiple_student_subjects_db(student_number, subject_names):
    """
    Assign multiple subjects to a student.

    The subjects are checked against the student's school phase.

    Phase rules:
        Foundation Phase: Grade R - 3
        Intermediate Phase: Grade 4 - 6
        Senior Phase: Grade 7 - 9
        FET Phase: Grade 10 - 12 and Grade 12RW

    Important:
        FET students are NOT given a hard-coded subject combination.
        The school administrator chooses subjects according to
        the school's own subject-combination rules.

        Grade 12RW is also treated as FET.

        Old Curriculum has no automatic phase mapping.
    """

    # ----------------------------------------------------------
    # Open a connection to the SQLite database.
    # ----------------------------------------------------------
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    try:
        # ----------------------------------------------------------
        # 1. Check that the student exists.
        #
        # We also get the student's grade because we need the
        # grade to determine the student's school phase.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT
                students.student_number,
                students.student_name,
                grades.grade_name
            FROM students
            INNER JOIN grades
                ON students.grade_id = grades.grade_id
            WHERE students.student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

        # Stop if the student does not exist.
        if student is None:
            raise ValueError("Student not found.")

        # Store the student's grade.
        grade_name = student["grade_name"]

        # ----------------------------------------------------------
        # 2. Determine the student's school phase.
        #
        # Example:
        # Grade 7  -> Senior Phase
        # Grade 10 -> FET Phase
        # Grade 12 -> FET Phase
        # Grade 12RW -> FET Phase
        # ----------------------------------------------------------
        phase_name = get_phase_for_grade(grade_name)

        # Old Curriculum does not currently have a phase mapping.
        if phase_name is None:

            if grade_name == "Old Curriculum":
                raise ValueError(
                    "Old Curriculum does not have a phase mapping. "
                    "Please configure its subjects separately."
                )

            raise ValueError(
                f"Unable to determine the phase for grade {grade_name}."
            )

        # ----------------------------------------------------------
        # 3. Clean the selected subject names.
        #
        # This removes accidental spaces.
        #
        # Example:
        # " HISTORY " becomes "HISTORY"
        # ----------------------------------------------------------
        cleaned_subjects = []

        for subject_name in subject_names:

            subject_name = subject_name.strip()

            # Only keep non-empty subject names.
            if subject_name:
                cleaned_subjects.append(subject_name)

        # Make sure the administrator selected at least one subject.
        if not cleaned_subjects:
            raise ValueError("No subjects were selected.")

        # ----------------------------------------------------------
        # 4. Get the subjects allowed for this student's phase.
        #
        # phase_subjects is the source of truth for which subjects
        # belong to each phase.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT
                subjects.subject_name
            FROM phase_subjects
            INNER JOIN subjects
                ON phase_subjects.subject_id = subjects.subject_id
            WHERE phase_subjects.phase_name = ?
        """, (phase_name,))

        phase_subject_rows = cursor.fetchall()

        # Convert the database rows into a simple list of names.
        allowed_subjects = []

        for row in phase_subject_rows:
            allowed_subjects.append(row["subject_name"])

        # Stop if no subjects have been configured for this phase.
        if not allowed_subjects:
            raise ValueError(
                f"No subjects have been configured for {phase_name}."
            )

        # ----------------------------------------------------------
        # 5. Check every selected subject.
        #
        # A subject must:
        #
        #   a) Exist in the subjects table.
        #   b) Belong to the student's phase.
        #
        # We perform all checks BEFORE inserting anything.
        # This prevents a situation where some subjects are saved
        # and another subject fails.
        # ----------------------------------------------------------
        for subject_name in cleaned_subjects:

            # Check that the subject exists in the subjects table.
            cursor.execute("""
                SELECT subject_name
                FROM subjects
                WHERE subject_name = ?
            """, (subject_name,))

            subject = cursor.fetchone()

            if subject is None:
                raise ValueError(
                    f"Subject not found: {subject_name}"
                )

            # ------------------------------------------------------
            # Check that this subject belongs to the student's phase.
            # ------------------------------------------------------
            if subject_name not in allowed_subjects:
                raise ValueError(
                    f"{subject_name} is not configured for "
                    f"{grade_name} ({phase_name})."
                )

        # ----------------------------------------------------------
        # 6. Remove duplicate selections.
        #
        # If the administrator enters:
        #
        # 1,2,2,3
        #
        # we only assign:
        #
        # 1,2,3
        # ----------------------------------------------------------
        unique_subjects = []

        for subject_name in cleaned_subjects:

            if subject_name not in unique_subjects:
                unique_subjects.append(subject_name)

        # ----------------------------------------------------------
        # 7. Insert all selected subjects.
        #
        # We only reach this section after ALL subjects have passed
        # the validation checks above.
        # ----------------------------------------------------------
        for subject_name in unique_subjects:

            cursor.execute("""
                INSERT INTO student_subjects (
                    student_number,
                    subject_name
                )
                VALUES (?, ?)
            """, (
                student_number,
                subject_name
            ))

        # ----------------------------------------------------------
        # 8. Save all subjects permanently.
        # ----------------------------------------------------------
        connection.commit()

        # Tell the administrator how many subjects were assigned.
        print(
            f"{student['student_name']} assigned to "
            f"{len(unique_subjects)} subject(s)."
        )

    except sqlite3.IntegrityError:
        # ----------------------------------------------------------
        # Undo all changes if there is a duplicate subject or
        # another database integrity problem.
        # ----------------------------------------------------------
        connection.rollback()

        raise ValueError(
            "One or more subjects are already assigned "
            "to this student."
        )

    except Exception:
        # ----------------------------------------------------------
        # Undo any database changes if another error occurs.
        # ----------------------------------------------------------
        connection.rollback()

        # Send the error back to the calling code.
        raise

    finally:
        # ----------------------------------------------------------
        # Always close the database connection.
        # ----------------------------------------------------------
        connection.close()           



def get_student_homework_db(student_number):
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    # ----------------------------------------------------------
    # Get homework for subjects that this student actually takes.
    #
    # We connect:
    #
    # students
    #     ↓
    # student_subjects
    #     ↓
    # subjects
    #     ↓
    # homework
    #
    # This means a student will only receive homework for
    # subjects assigned to that student.
    # ----------------------------------------------------------
    cursor.execute("""
        SELECT
            h.homework_id,
            h.title,
            h.description,
            h.due_date,
            h.date_posted,

            s.subject_name,

            t.teacher_name,

            g.grade_name

        FROM homework h

        JOIN students st
            ON st.student_number = ?

        JOIN student_subjects ss
            ON ss.student_number = st.student_number

        JOIN subjects s
            ON s.subject_name = ss.subject_name
            AND s.subject_id = h.subject_id

        JOIN grades g
            ON g.grade_id = h.grade_id
            AND g.grade_id = st.grade_id

        JOIN teachers t
            ON t.teacher_number = h.teacher_number

        ORDER BY h.due_date
    """, (student_number,))

    # Get all matching homework records.
    homework = cursor.fetchall()

    # Close the database connection.
    connection.close()

    # Return the homework to the student menu.
    return homework
    
    


def get_student_attendance_db(student_number):
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    # ----------------------------------------------------------
    # Get attendance records for this student.
    #
    # We also join with the subjects table so that we can
    # display the subject name instead of only the subject ID.
    #
    # The student_subjects table makes sure we only return
    # subjects that belong to this student.
    # ----------------------------------------------------------
    cursor.execute("""
        SELECT
            a.attendance_id,
            a.attendance_date,
            a.status,
            s.subject_name,
            t.teacher_name

        FROM attendance a

        JOIN student_subjects ss
            ON ss.student_number = a.student_number

        JOIN subjects s
            ON s.subject_id = a.subject_id
            AND s.subject_name = ss.subject_name

        JOIN teachers t
            ON t.teacher_number = a.teacher_number

        WHERE a.student_number = ?

        ORDER BY a.attendance_date DESC
    """, (student_number,))

    # Get all matching attendance records.
    attendance = cursor.fetchall()

    # Close the database connection.
    connection.close()

    # Return the attendance records.
    return attendance   



def get_student_results_db(student_number):
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    # ----------------------------------------------------------
    # Get marks belonging to this student.
    #
    # We also connect the result to student_subjects.
    #
    # This means the student will only see results for
    # subjects that the student is registered for.
    # ----------------------------------------------------------
    cursor.execute("""
        SELECT
            m.mark_id,
            m.mark_value,
            m.total_possible,
            m.exam_date,
            s.subject_name,
            t.teacher_name

        FROM marks m

        JOIN student_subjects ss
            ON ss.student_number = m.student_number

        JOIN subjects s
            ON s.subject_id = m.subject_id
            AND s.subject_name = ss.subject_name

        JOIN teachers t
            ON t.teacher_number = m.teacher_number

        WHERE m.student_number = ?

        ORDER BY m.exam_date DESC
    """, (student_number,))

    # Get all matching results.
    results = cursor.fetchall()

    # Close the database connection.
    connection.close()

    # Return the results to the student menu.
    return results    
     


def get_student_report_card_db(student_number):
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so we can run SQL commands.
    cursor = connection.cursor()

    # ----------------------------------------------------------
    # Get this student's marks from the database.
    #
    # We connect:
    # marks -> subjects -> teachers
    #
    # student_subjects makes sure we only show subjects
    # that belong to this student.
    # ----------------------------------------------------------
    cursor.execute("""
        SELECT
            m.mark_id,
            m.mark_value,
            m.total_possible,
            m.exam_date,
            s.subject_name,
            t.teacher_name

        FROM marks m

        JOIN student_subjects ss
            ON ss.student_number = m.student_number

        JOIN subjects s
            ON s.subject_id = m.subject_id
            AND s.subject_name = ss.subject_name

        JOIN teachers t
            ON t.teacher_number = m.teacher_number

        WHERE m.student_number = ?

        ORDER BY s.subject_name
    """, (student_number,))

    # Get all matching results.
    results = cursor.fetchall()

    # Close the database connection.
    connection.close()

    # Return the results.
    return results



def get_student_report_card_by_term_db(
    student_number,
    school_year,
    term_number
):
    """
    Get a student's report-card marks for one specific school term.

    The marks table does not store term_number directly.

    Instead, each mark has an exam_date.

    We therefore:
    1. Find the selected term's start and end dates
       from the school_terms table.
    2. Find marks where exam_date falls between
       those dates.
    3. Return the student's subject, mark, teacher,
       and exam date.

    This function is used when a student or guardian
    wants to view/print a report card for a specific term.
    """

    # Open a connection to the SQLite database.
    connection = get_connection()

    # Use sqlite3.Row so we can access columns by name.
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    try:
        # ---------------------------------------------------------
        # STEP 1:
        # Find the selected school's term dates.
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                start_date,
                end_date
            FROM school_terms
            WHERE school_year = ?
              AND term_number = ?
        """, (
            school_year,
            term_number
        ))

        term = cursor.fetchone()

        # If the requested term does not exist,
        # return an empty list.
        if term is None:
            return []

        start_date = term["start_date"]
        end_date = term["end_date"]

        # ---------------------------------------------------------
        # STEP 2:
        # Get the student's marks that fall inside
        # the selected term.
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                m.mark_id,
                m.mark_value,
                m.total_possible,
                m.exam_date,
                s.subject_name,
                t.teacher_name
            FROM marks m

            JOIN student_subjects ss
                ON ss.student_number = m.student_number

            JOIN subjects s
                ON s.subject_id = m.subject_id
                AND s.subject_name = ss.subject_name

            JOIN teachers t
                ON t.teacher_number = m.teacher_number

            WHERE m.student_number = ?
              AND m.exam_date BETWEEN ? AND ?

            ORDER BY s.subject_name
        """, (
            student_number,
            start_date,
            end_date
        ))

        results = cursor.fetchall()

        # Convert SQLite Row objects into dictionaries.
        return [dict(result) for result in results]

    except Exception as error:
        print(
            f"\nError getting report card by term: {error}"
        )
        return []

    finally:
        # Always close the database connection.
        connection.close()



        
     
def unlock_student_account(student_number):

    # Connect to the database
    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Check whether the account exists
        cursor.execute("""
            SELECT student_number
            FROM students
            WHERE student_number = ?
        """,
        (student_number,))

        student_account = cursor.fetchone()

        if student_account is None:
            connection.close()
            return False, "Student account not found."

        # Unlock online banking
        cursor.execute("""
            UPDATE students

            SET status = "Active"

            WHERE student_number = ?
        """,
        (student_number,))

        # Reset failed password attempts
        cursor.execute("""
            UPDATE students

            SET failed_attempts = 0

            WHERE student_number = (

                SELECT student_number

                FROM students 

                WHERE student_number = ?

            )
        """,
        (student_number,))

        connection.commit()

        return True, "Student account unlocked successfully."

    except Exception as error:

        connection.rollback()

        return False, f"Error: {error}"

    finally:

        connection.close()          
    

def get_grade_by_name(grade_name):
    # Open a connection to the database.
    connection = get_connection()

    # Create a cursor for executing SQL commands.
    cursor = connection.cursor()

    # Search for the grade using its name.
    cursor.execute("""
        SELECT grade_id, grade_name
        FROM grades
        WHERE grade_name = ?
    """, (grade_name,))

    # Get the matching grade.
    # If it doesn't exist, fetchone() returns None.
    grade = cursor.fetchone()

    # Close the connection.
    connection.close()

    # Return the grade.
    return grade
    
    

def get_fee_for_grade(grade_id):
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so we can execute SQL commands.
    cursor = connection.cursor()

    # Find the fee structure belonging to this grade.
    cursor.execute("""
        SELECT fees_id, grade_id, amount
        FROM fees_structure
        WHERE grade_id = ?
    """, (grade_id,))

    # Get the matching fee record.
    fee = cursor.fetchone()

    # Close the database connection.
    connection.close()

    # Return the fee record to the program.
    return fee    
    

# record_fee_payment() will automatically determine the school year and term from payment_date using your school_terms table.
# This function records the payment under the current term, just as your system already does.
# The carry-forward calculation then determines that the payment should be applied to the oldest outstanding balance first.
def record_fee_payment(student_number, amount, payment_date):
    # ---------------------------------------------------------
    # OPEN DATABASE CONNECTION
    # ---------------------------------------------------------
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # -----------------------------------------------------
        # FIND THE SCHOOL TERM FOR THE PAYMENT DATE
        # -----------------------------------------------------
        cursor.execute("""
            SELECT
                school_year,
                term_number
            FROM school_terms
            WHERE start_date <= ?
            AND end_date >= ?
            LIMIT 1
        """, (
            payment_date,
            payment_date
        ))

        school_term = cursor.fetchone()

        # Make sure the payment date belongs to a school term.
        if school_term is None:
            raise ValueError(
                "The payment date does not fall within "
                "an active school term."
            )

        school_year = school_term["school_year"]
        term_number = school_term["term_number"]

        # -----------------------------------------------------
        # CHECK THE PAYMENT AMOUNT
        # -----------------------------------------------------
        if amount <= 0:
            raise ValueError(
                "Payment amount must be greater than zero."
            )

        # -----------------------------------------------------
        # GET THE STUDENT'S CURRENT FEE INFORMATION
        # -----------------------------------------------------
        fee_status = get_student_total_fee_due_db(
            student_number,
            school_year,
            term_number
        )

        # -----------------------------------------------------
        # CHECK WHETHER THE STUDENT EXISTS
        # -----------------------------------------------------
        if fee_status is None:
            raise ValueError("Student fee information not found.")

        # -----------------------------------------------------
        # CHECK AGAINST THE TOTAL AMOUNT CURRENTLY DUE
        # -----------------------------------------------------
        #
        # This includes:
        #
        # Previous outstanding balances
        # +
        # Current term fee
        #
        if amount > fee_status["remaining_balance"]:
            raise ValueError(
                "Payment cannot be greater than "
                "the outstanding balance."
            )

        # -----------------------------------------------------
        # SAVE THE PAYMENT
        # -----------------------------------------------------
        cursor.execute("""
            INSERT INTO fee_payments (
                student_number,
                amount,
                payment_date,
                term_number,
                school_year
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            student_number,
            amount,
            payment_date,
            term_number,
            school_year
        ))

        # -----------------------------------------------------
        # UPDATE THE OLD fees_balance COLUMN
        # -----------------------------------------------------
        #
        # We keep this column updated because the database
        # already contains it.
        #
        # The actual term/carry-forward calculations come
        # from fee_payments.
        #
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total_paid
            FROM fee_payments
            WHERE student_number = ?
        """, (student_number,))

        total_paid = cursor.fetchone()["total_paid"]

        cursor.execute("""
            SELECT amount
            FROM fees_structure
            WHERE grade_id = (
                SELECT grade_id
                FROM students
                WHERE student_number = ?
            )
        """, (student_number,))

        annual_fee_row = cursor.fetchone()

        if annual_fee_row is not None:

            annual_fee = annual_fee_row["amount"]

            overall_balance = annual_fee - total_paid

            if overall_balance < 0:
                overall_balance = 0

            cursor.execute("""
                UPDATE students
                SET fees_balance = ?
                WHERE student_number = ?
            """, (
                overall_balance,
                student_number
            ))

        # -----------------------------------------------------
        # SAVE EVERYTHING
        # -----------------------------------------------------
        connection.commit()

        # Return the new overall balance.
        return overall_balance

    except Exception:
        # If anything goes wrong, undo the database changes.
        connection.rollback()
        raise

    finally:
        # Always close the database connection.
        connection.close()
        
        


def get_student_term_fee_db(student_number):
    # Open the SQLite database.
    connection = get_connection()

    cursor = connection.cursor()

    # Get the student's annual fee.
    cursor.execute("""
        SELECT
            s.student_number,
            s.student_name,
            g.grade_name,
            f.amount AS annual_fee
        FROM students s
        JOIN grades g
            ON g.grade_id = s.grade_id
        JOIN fees_structure f
            ON f.grade_id = s.grade_id
        WHERE s.student_number = ?
    """, (student_number,))

    student = cursor.fetchone()

    connection.close()

    if student is None:
        raise ValueError("Student or fee structure not found.")

    # The school has 4 terms.
    annual_fee = student["annual_fee"]

    # Each term is 25% of the annual fee.
    term_fee = annual_fee / 4

    return {
        "student_number": student["student_number"],
        "student_name": student["student_name"],
        "grade_name": student["grade_name"],
        "annual_fee": annual_fee,
        "term_fee": term_fee
    }



# ---------------------------------------------------------
# GET STUDENT TERM PAYMENT STATUS
# ---------------------------------------------------------
# This function checks how much a student has paid for
# ONE specific school year and ONE specific term.
#
# Example:
# 2026 Term 1 payments are kept separate from
# 2027 Term 1 payments.
# ---------------------------------------------------------

def get_student_term_payment_status_db(
    student_number,
    school_year,
    term_number
):

    # Open the database.
    connection = get_connection()
    cursor = connection.cursor()

    # -----------------------------------------------------
    # GET STUDENT AND ANNUAL FEE
    # -----------------------------------------------------
    # We get the student's grade and then find the annual
    # fee for that grade from fees_structure.

    cursor.execute("""
        SELECT
            s.student_number,
            s.student_name,
            g.grade_name,
            f.amount AS annual_fee
        FROM students s

        JOIN grades g
            ON g.grade_id = s.grade_id

        JOIN fees_structure f
            ON f.grade_id = s.grade_id

        WHERE s.student_number = ?
    """, (student_number,))

    student = cursor.fetchone()

    # If the student or fee structure doesn't exist,
    # stop the function with an error.
    if student is None:
        connection.close()
        raise ValueError("Student or fee structure not found.")

    # -----------------------------------------------------
    # CALCULATE TERM FEE
    # -----------------------------------------------------
    # The annual fee is divided equally between 4 terms.

    annual_fee = student["annual_fee"]

    term_fee = annual_fee / 4

    # -----------------------------------------------------
    # GET PAYMENTS FOR THIS YEAR AND THIS TERM
    # -----------------------------------------------------
    # This is very important.
    #
    # We check BOTH:
    #     school_year
    #     term_number
    #
    # Therefore, a payment made in 2026 Term 1 will NOT
    # be counted toward 2027 Term 1 or 2026 Term 2.

    cursor.execute("""
        SELECT
            COALESCE(SUM(amount), 0) AS amount_paid

        FROM fee_payments

        WHERE student_number = ?
        AND school_year = ?
        AND term_number = ?
    """, (
        student_number,
        school_year,
        term_number
    ))

    payment = cursor.fetchone()

    amount_paid = payment["amount_paid"]

    # -----------------------------------------------------
    # CALCULATE REMAINING AMOUNT
    # -----------------------------------------------------

    amount_remaining = term_fee - amount_paid

    # Don't allow the remaining amount to become negative
    # if the student accidentally pays more than required.

    if amount_remaining < 0:
        amount_remaining = 0

    # -----------------------------------------------------
    # CHECK REPORT CARD ACCESS
    # -----------------------------------------------------
    # The student gets report-card access only when the
    # complete term fee has been paid.

    if amount_paid >= term_fee:
        report_card_access = True
    else:
        report_card_access = False

    # Close the database connection.
    connection.close()

    # Return all the information we calculated.
    return {
        "student_number": student["student_number"],
        "student_name": student["student_name"],
        "grade_name": student["grade_name"],
        "annual_fee": annual_fee,
        "school_year": school_year,
        "term_number": term_number,
        "term_fee": term_fee,
        "amount_paid": amount_paid,
        "amount_remaining": amount_remaining,
        "report_card_access": report_card_access
    }



def show_fees_statement(student_number):
    # Get the student's current fee information from SQLite.
    connection = get_connection()
    cursor = connection.cursor()

    # Get the student's name, grade, and current balance.
    cursor.execute("""
        SELECT
            s.student_number,
            s.student_name,
            s.grade_id,
            s.fees_balance,
            g.grade_name
        FROM students s
        JOIN grades g
            ON s.grade_id = g.grade_id
        WHERE s.student_number = ?
    """, (student_number,))

    student = cursor.fetchone()

    # Close this database connection.
    connection.close()

    # Check whether the student exists.
    if student is None:
        print("\nStudent account not found.")
        return

    # Get all payments made by this student.
    payments = get_payment_history(student_number)

    # Start the total paid at zero.
    total_paid = 0

    # Add every payment together.
    for payment in payments:
        total_paid += payment["amount"]

    # Calculate the original fee.
    # Current balance + everything already paid = original fee.
    original_fee = student["fees_balance"] + total_paid

    # Display the student's fee statement.
    print("\n===== FEES STATEMENT =====")
    print(f"Student Number : {student['student_number']}")
    print(f"Student Name   : {student['student_name']}")
    print(f"Grade          : {student['grade_name']}")

    print("\n----- FEE SUMMARY -----")
    print(f"Original Fee   : R{original_fee:,.2f}")
    print(f"Total Paid     : R{total_paid:,.2f}")
    print(f"Balance Due    : R{student['fees_balance']:,.2f}")

    print("\n----- PAYMENT HISTORY -----")

    # Check whether any payments exist.
    if not payments:
        print("No payments have been made.")
        return

    # Display the headings.
    print(f"{'ID':<8}{'DATE':<15}{'AMOUNT':>15}")
    print("-" * 38)

    # Display every payment.
    for payment in payments:
        print(
            f"{payment['payment_id']:<8}"
            f"{payment['payment_date']:<15}"
            f"R{payment['amount']:>13,.2f}"
        )

    print("-" * 38)



def show_student_fees_statement(student_number):
    # ---------------------------------------------------------
    # GET THE CURRENT SCHOOL TERM
    # ---------------------------------------------------------
    #
    # We use the school_terms table to determine the
    # current school year and term.
    #
    current_term = get_current_school_term_db()

    if current_term is None:
        print("\nNo active school term found.")
        return

    school_year = current_term["school_year"]
    term_number = current_term["term_number"]

    # ---------------------------------------------------------
    # GET THE STUDENT'S FEE INFORMATION
    # ---------------------------------------------------------
    #
    # This function comes from school_database.py.
    #
    # It calculates:
    # - previous term balances
    # - current term fee
    # - current term payments
    # - remaining balance
    #
    try:
        fee = get_student_total_fee_due_db(
            student_number,
            school_year,
            term_number
        )
    except ValueError as error:
        print(f"\nError: {error}")
        return

    # ---------------------------------------------------------
    # DISPLAY BASIC STUDENT INFORMATION
    # ---------------------------------------------------------
    print("\n===== FEES STATEMENT =====")

    print(f"Student       : {fee['student_name']}")
    print(f"Grade         : {fee['grade_name']}")
    print(f"School Year   : {fee['school_year']}")
    print(f"Current Term  : {fee['current_term']}")

    print(f"\nAnnual Fee    : R{fee['annual_fee']:.2f}")
    print(f"Term Fee      : R{fee['term_fee']:.2f}")

    # ---------------------------------------------------------
    # DISPLAY PREVIOUS TERM BALANCES
    # ---------------------------------------------------------
    print("\n===== PREVIOUS TERM BALANCES =====")

    previous_terms = fee["previous_term_balances"]

    if not previous_terms:
        print("No previous term balances.")
    else:
        for term in previous_terms:
            print(
                f"Term {term['term_number']}: "
                f"Fee R{term['term_fee']:.2f} | "
                f"Paid R{term['amount_paid']:.2f} | "
                f"Outstanding "
                f"R{term['balance']:.2f}"
            )

    # ---------------------------------------------------------
    # DISPLAY PREVIOUS BALANCE
    # ---------------------------------------------------------
    print(
        f"\nPrevious Balance : "
        f"R{fee['previous_balance']:.2f}"
    )

    # ---------------------------------------------------------
    # DISPLAY CURRENT TERM INFORMATION
    # ---------------------------------------------------------
    print("\n===== CURRENT TERM =====")

    print(
        f"Term {fee['current_term']} Fee : "
        f"R{fee['term_fee']:.2f}"
    )

    print(
        f"Current Term Paid : "
        f"R{fee['current_term_paid']:.2f}"
    )

    print(
        f"Payment Used for Previous : "
        f"R{fee['payment_used_for_previous']:.2f}"
    )

    print(
        f"Previous Balance Left : "
        f"R{fee['remaining_previous_balance']:.2f}"
    )

    print(
        f"Current Term Balance : "
        f"R{fee['current_term_balance']:.2f}"
    )

    # ---------------------------------------------------------
    # DISPLAY TOTALS
    # ---------------------------------------------------------
    print("\n===== TOTAL =====")

    print(
        f"Total Amount Due : "
        f"R{fee['total_required']:.2f}"
    )

    print(
        f"Total Remaining  : "
        f"R{fee['remaining_balance']:.2f}"
    )

    # ---------------------------------------------------------
    # PAYMENT WARNING
    # ---------------------------------------------------------
    #
    # If there is still an old balance, tell the student
    # that it must be cleared first.
    #
    if fee["remaining_previous_balance"] > 0:

        print("\n⚠ PAYMENT PRIORITY")
        print(
            "Please clear the previous outstanding "
            "balance first."
        )

    elif fee["current_term_balance"] > 0:

        print("\nCurrent term fee is still outstanding.")

    else:

        print("\n✓ Fees are fully paid for the current term.")



    


def get_payment_history_db(student_number):
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor for executing SQL commands.
    cursor = connection.cursor()

    # Find all payments belonging to this student.
    #
    # We now also retrieve:
    # - school_year → tells us which school year the payment belongs to
    # - term_number → tells us which term the payment belongs to
    #
    # We order the payments from oldest to newest.
    cursor.execute("""
        SELECT
            payment_id,
            student_number,
            amount,
            payment_date,
            school_year,
            term_number
        FROM fee_payments
        WHERE student_number = ?
        ORDER BY payment_date ASC, payment_id ASC
    """, (student_number,))

    # Get all payment records.
    payments = cursor.fetchall()

    # Close the database connection.
    connection.close()

    # Return the payment records to the school program.
    return payments
    
    

def show_payment_history(student_number):
    # Get this student's payments from SQLite.
    payments = get_payment_history_db(student_number)

    # Display the heading.
    print("\n===== PAYMENT HISTORY =====")

    # Check whether the student has made any payments.
    if not payments:
        print("No payments have been made.\n")
        return

    # Start the total paid at zero.
    total_paid = 0

    # Display the column headings.
    #
    # We now show:
    # ID    = payment ID
    # DATE  = date the payment was made
    # YEAR  = school year
    # TERM  = school term
    # AMOUNT = amount paid
    print(
        f"{'ID':<6}"
        f"{'DATE':<15}"
        f"{'YEAR':<8}"
        f"{'TERM':<8}"
        f"{'AMOUNT':>8}"
    )

    print("-" * 52)

    # Go through each payment.
    for payment in payments:

        # Add this payment to the total.
        total_paid += payment["amount"]

        # Display the payment information.
        print(
            f"{payment['payment_id']:<6}"
            f"{payment['payment_date']:<15}"
            f"{payment['school_year']:<8}"
            f"{payment['term_number']:<8}"
            f"R{payment['amount']:>3.2f}"
        )

    # Display the total amount paid.
    print("-" * 52)

    # Display the total of all payments.
    print(f"Total Paid: R{total_paid:.2f}")
    
    
    
# As of this term, how much does the student owe from previous terms, how much is the current term fee, and what is the total amount they must clear?"    
def get_student_total_fee_due_db(
    student_number,
    school_year,
    current_term
):
    # ---------------------------------------------------------
    # OPEN DATABASE CONNECTION
    # ---------------------------------------------------------
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # -----------------------------------------------------
        # FIND THE STUDENT'S ANNUAL FEE
        # -----------------------------------------------------
        cursor.execute("""
            SELECT
                s.student_number,
                s.student_name,
                g.grade_name,
                f.amount AS annual_fee
            FROM students s
            JOIN grades g
                ON g.grade_id = s.grade_id
            JOIN fees_structure f
                ON f.grade_id = s.grade_id
            WHERE s.student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

        # Make sure the student exists and has a fee structure.
        if student is None:
            raise ValueError(
                "Student or fee structure not found."
            )

        # -----------------------------------------------------
        # CALCULATE THE TERM FEE
        # -----------------------------------------------------
        #
        # Annual fee ÷ 4 terms = term fee
        #
        annual_fee = student["annual_fee"]
        term_fee = annual_fee / 4

        # -----------------------------------------------------
        # CREATE A LIST FOR PREVIOUS TERM BALANCES
        # -----------------------------------------------------
        #
        # This will allow us to show:
        #
        # Term 1 Outstanding : R1,000
        # Term 2 Outstanding : R12,500
        #
        previous_term_balances = []

        # This keeps track of the total previous balance.
        previous_balance = 0

        # -----------------------------------------------------
        # CHECK EACH PREVIOUS TERM INDIVIDUALLY
        # -----------------------------------------------------
        for term_number in range(1, current_term):

            # -------------------------------------------------
            # FIND PAYMENTS MADE FOR THIS TERM
            # -------------------------------------------------
            cursor.execute("""
                SELECT
                    COALESCE(SUM(amount), 0) AS amount_paid
                FROM fee_payments
                WHERE student_number = ?
                AND school_year = ?
                AND term_number = ?
            """, (
                student_number,
                school_year,
                term_number
            ))

            payment = cursor.fetchone()

            amount_paid = payment["amount_paid"]

            # -------------------------------------------------
            # CALCULATE THIS TERM'S OUTSTANDING BALANCE
            # -------------------------------------------------
            term_balance = term_fee - amount_paid

            # A balance cannot be negative.
            if term_balance < 0:
                term_balance = 0

            # Add this term's balance to the total
            # previous balance.
            previous_balance += term_balance

            # Store the individual term information.
            previous_term_balances.append({
                "term_number": term_number,
                "term_fee": term_fee,
                "amount_paid": amount_paid,
                "balance": term_balance
            })

        # -----------------------------------------------------
        # FIND PAYMENTS MADE IN THE CURRENT TERM
        # -----------------------------------------------------
        cursor.execute("""
            SELECT
                COALESCE(SUM(amount), 0) AS current_term_paid
            FROM fee_payments
            WHERE student_number = ?
            AND school_year = ?
            AND term_number = ?
        """, (
            student_number,
            school_year,
            current_term
        ))

        current_payment = cursor.fetchone()

        current_term_paid = current_payment["current_term_paid"]

        # -----------------------------------------------------
        # CURRENT TERM PAYMENTS CLEAR OLD BALANCES FIRST
        # -----------------------------------------------------
        #
        # Example:
        #
        # Previous balance = R13,500
        # Current payment  = R12,500
        #
        # R12,500 is used to reduce the previous balance.
        #
        payment_used_for_previous = min(
            current_term_paid,
            previous_balance
        )

        # Calculate the previous balance after applying
        # the current-term payment.
        remaining_previous_balance = (
            previous_balance
            - payment_used_for_previous
        )

        # -----------------------------------------------------
        # CALCULATE PAYMENT LEFT FOR CURRENT TERM
        # -----------------------------------------------------
        payment_left_for_current_term = (
            current_term_paid
            - payment_used_for_previous
        )

        # -----------------------------------------------------
        # CALCULATE CURRENT TERM BALANCE
        # -----------------------------------------------------
        current_term_balance = (
            term_fee
            - payment_left_for_current_term
        )

        # Balance cannot be negative.
        if current_term_balance < 0:
            current_term_balance = 0

        # -----------------------------------------------------
        # TOTAL AMOUNT REQUIRED
        # -----------------------------------------------------
        total_required = (
            previous_balance
            + term_fee
        )

        # -----------------------------------------------------
        # TOTAL REMAINING BALANCE
        # -----------------------------------------------------
        remaining_balance = (
            remaining_previous_balance
            + current_term_balance
        )

        # -----------------------------------------------------
        # RETURN ALL INFORMATION
        # -----------------------------------------------------
        return {
            "student_number": student["student_number"],
            "student_name": student["student_name"],
            "grade_name": student["grade_name"],
            "annual_fee": annual_fee,

            "school_year": school_year,
            "current_term": current_term,

            "term_fee": term_fee,

            # Individual previous-term information.
            "previous_term_balances":
                previous_term_balances,

            # Combined previous-term balance.
            "previous_balance": previous_balance,

            # Current-term payment.
            "current_term_paid": current_term_paid,

            # Amount of current payment used to clear
            # previous balances.
            "payment_used_for_previous":
                payment_used_for_previous,

            # Previous balance after current payment.
            "remaining_previous_balance":
                remaining_previous_balance,

            # Payment remaining after previous balances
            # have been cleared.
            "payment_left_for_current_term":
                payment_left_for_current_term,

            # Current term still outstanding.
            "current_term_balance":
                current_term_balance,

            # Previous balance + current term fee.
            "total_required": total_required,

            # Final amount still outstanding.
            "remaining_balance": remaining_balance
        }

    finally:
        # Always close the database connection.
        connection.close()
    
    


def register_admin_db(
    admin_name,
    password_hash,
    password_salt,
    category,
    email_address
):
    # Open a connection to our SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    # ----------------------------------------------------------
    # Find the highest student number currently in the database.
    # ----------------------------------------------------------
    #
    # MAX() finds the largest student number.
    #
    # If there are no students yet, MAX() will return None.
    cursor.execute("""
        SELECT MAX(admin_id)
        FROM admins
    """)

    # Get the result of our SELECT query.
    result = cursor.fetchone()

    # The result contains the highest student number.
    last_admin = result[0]

    # ----------------------------------------------------------
    # Create the new student number.
    # ----------------------------------------------------------

    if last_admin is None:
        # There are no students in the database yet.
        # We will start with your existing numbering system.
        admin_id = 2000055

    else:
        # If students already exist, increase the highest
        # student number by 1.
        admin_id = last_admin + 1

    # ----------------------------------------------------------
    # Insert the new student.
    # ----------------------------------------------------------

    cursor.execute("""
        INSERT INTO admins (
            admin_id,
            admin_name,
            password_hash,
            password_salt,
            category,
            email_address,
            status 
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
       admin_id,
       admin_name,
       password_hash,
       password_salt,
       category,
       email_address,
       'Active'
    ))

    # Save the INSERT operation permanently.
    connection.commit()

    # Close the database connection.
    connection.close()

    # Return the newly created student number.
    return admin_id
    
    
def login_admin(admin_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            a.admin_id,
            a.admin_name,
            a.password_hash,
            a.password_salt,
            a.category,
            a.failed_attempts,
            a.email_address,
            a.status
        FROM admins a
        WHERE a.admin_id = ?
    """, (admin_id,))

    admin = cursor.fetchone()

    if admin is None:
        connection.close()
        return None, "Admin not found."

    if admin["status"] == "locked":
        connection.close()
        return None, "Your account is locked. Contact the Principal."

    connection.close()

    return admin, None
    
    

def login_3timespassword_block_admin(admin_id, password):

    connection = get_connection()
    # 🌟 FIX 1: This allows you to use text keys like student["password_salt"]
    connection.row_factory = sqlite3.Row 
    cursor = connection.cursor()

    # 🌟 FIX 2: We select all needed columns at once so nothing gets overwritten
    cursor.execute("""
        SELECT status, password_salt, password_hash, failed_attempts
        FROM admins
        WHERE admin_id = ?
    """, (admin_id,))

    admin = cursor.fetchone()

    # If no student matches that number
    if admin is None:
        connection.close()
        return False, "Admin not found."

    # Check if the account is already locked
    if admin["status"] == "locked":
        connection.close()
        return False, "Your account is Blocked. Contact the Principal."

    # Verify the password
    salt = bytes.fromhex(admin["password_salt"])
    password_hash = hashlib.sha256(password.encode() + salt).hexdigest()

    if password_hash == admin["password_hash"]:
        # Reset failed attempts back to 0 on success
        cursor.execute("""
            UPDATE admins
            SET failed_attempts = 0
            WHERE admin_id = ?
        """, (admin_id,))

        connection.commit()
        connection.close()
        return True, "Login successful."

    else:
        # Increase failed attempts count by 1
        cursor.execute("""
            UPDATE admins
            SET failed_attempts = failed_attempts + 1
            WHERE admin_id = ?
        """, (admin_id,))
        connection.commit()

        # Check if they have reached 3 or more attempts
        if admin["failed_attempts"] + 1 >= 3:
            cursor.execute("""
                UPDATE admins
                SET status = 'locked'
                WHERE admin_id = ?
            """, (admin_id,))
            connection.commit()
            connection.close()
            return False, "Account locked after 3 failed attempts."

        connection.close()
        return False, "Incorrect password."    




def unlock_admin_account(admin_id):

    # Connect to the database
    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Check whether the account exists
        cursor.execute("""
            SELECT admin_id
            FROM admins
            WHERE admin_id = ?
        """,
        (admin_id,))

        admin_account = cursor.fetchone()

        if admin_account is None:
            connection.close()
            return False, "Admin account not found."

        # Unlock online banking
        cursor.execute("""
            UPDATE admins

            SET status = "Active"

            WHERE admin_id = ?
        """,
        (admin_id,))

        # Reset failed password attempts
        cursor.execute("""
            UPDATE admins

            SET failed_attempts = 0

            WHERE admin_id = (

                SELECT admin_id

                FROM admins

                WHERE admin_id = ?

            )
        """,
        (admin_id,))

        connection.commit()

        return True, "Admin account unlocked successfully."

    except Exception as error:

        connection.rollback()

        return False, f"Error: {error}"

    finally:

        connection.close()     



def save_admin_log(
        admin_name,
        category,
        action,
        teacher_number,
        student_number,
        admin_id
):

    # Connect to database
    connection = get_connection()
    cursor = connection.cursor()
    

    # Save admin activity
    cursor.execute("""
        INSERT INTO admin_logs(

            admin_name,
            category,
            action,
            teacher_number,
            student_number,
            admin_id

        )

        VALUES(?, ?, ?, ?, ?, ?)
    """,
    (
        admin_name,
        category,
        action,
        teacher_number,
        student_number,
        admin_id
    ))

    connection.commit()

    connection.close()    
    
  

    
def view_admin_logs():

    connection = get_connection()
    cursor = connection.cursor()
    
    # This line allows you to look up columns by their names!
    connection.row_factory = sqlite3.Row 

    cursor.execute("""

        SELECT *

        FROM admin_logs
        
        ORDER BY action_time DESC

    """)

    logs = cursor.fetchall()

    connection.close()

    return logs        





def register_guardian_db(
    first_name,
    last_name,
    phone_number,
    email,
    address,
    password_hash,
    password_salt
):
    # Open a connection to our SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    # ----------------------------------------------------------
    # Find the highest guardian number currently in the database.
    # ----------------------------------------------------------
    #
    # MAX() finds the largest guardian number.
    #
    # If there are no guardians yet, MAX() will return None.
    cursor.execute("""
        SELECT MAX(guardian_id)
        FROM guardians
    """)

    # Get the result of our SELECT query.
    result = cursor.fetchone()

    # The result contains the highest guardian number.
    last_guardian = result[0]

    # ----------------------------------------------------------
    # Create the new student number.
    # ----------------------------------------------------------

    if last_guardian is None:
        # There are no guardians in the database yet.
        # We will start with your existing numbering system.
        guardian_id = 4000055

    else:
        # If guardians already exist, increase the highest
        # guardian number by 1.
        guardian_id = last_guardian + 1

    # ----------------------------------------------------------
    # Insert the new guardian.
    # ----------------------------------------------------------

    cursor.execute("""
        INSERT INTO guardians (
            guardian_id,
            first_name,
            last_name,
            phone_number,
            email,
            address,
            password_hash,
            password_salt
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
       guardian_id,
       first_name,
       last_name,
       phone_number,
       email,
       address,
       password_hash,
       password_salt
    ))

    # Save the INSERT operation permanently.
    connection.commit()

    # Close the database connection.
    connection.close()

    # Return the newly created guardian ID.
    return guardian_id
    
    
def login_guardian(guardian_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            g.guardian_id,
            g.first_name,
            g.last_name,
            g.phone_number,
            g.email,
            g.address,
            g.password_hash,
            g.password_salt,
            g.failed_attempts,
            g.status
        FROM guardians g
        WHERE g.guardian_id = ?
    """, (guardian_id,))

    guardian = cursor.fetchone()

    if guardian is None:
        connection.close()
        return None, "Guardian not found."

    if guardian["status"] == "locked":
        connection.close()
        return None, "Your account is locked. Contact the School."

    connection.close()

    return guardian, None
    
    

def login_3timespassword_block_guardian(guardian_id, password):

    connection = get_connection()
    # 🌟 FIX 1: This allows you to use text keys like guardian["password_salt"]
    connection.row_factory = sqlite3.Row 
    cursor = connection.cursor()

    # 🌟 FIX 2: We select all needed columns at once so nothing gets overwritten
    cursor.execute("""
        SELECT status, password_salt, password_hash, failed_attempts
        FROM guardians 
        WHERE guardian_id = ?
    """, (guardian_id,))

    guardian = cursor.fetchone()

    # If no guardian matches that number
    if guardian is None:
        connection.close()
        return False, "Guardian not found."

    # Check if the account is already locked
    if guardian["status"] == "locked":
        connection.close()
        return False, "Your account is Blocked. Contact the School."

    # Verify the password
    salt = bytes.fromhex(guardian["password_salt"])
    password_hash = hashlib.sha256(password.encode() + salt).hexdigest()

    if password_hash == guardian["password_hash"]:
        # Reset failed attempts back to 0 on success
        cursor.execute("""
            UPDATE guardians
            SET failed_attempts = 0
            WHERE guardian_id = ?
        """, (guardian_id,))

        connection.commit()
        connection.close()
        return True, "Login successful."

    else:
        # Increase failed attempts count by 1
        cursor.execute("""
            UPDATE guardians
            SET failed_attempts = failed_attempts + 1
            WHERE guardian_id = ?
        """, (guardian_id,))
        connection.commit()

        # Check if they have reached 3 or more attempts
        if guardian["failed_attempts"] + 1 >= 3:
            cursor.execute("""
                UPDATE guardians
                SET status = 'locked'
                WHERE guardian_id = ?
            """, (guardian_id,))
            connection.commit()
            connection.close()
            return False, "Account locked after 3 failed attempts."

        connection.close()
        return False, "Incorrect password."    




def unlock_guardian_account(guardian_id):

    # Connect to the database
    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Check whether the account exists
        cursor.execute("""
            SELECT guardian_id
            FROM guardians
            WHERE guardian_id = ?
        """,
        (guardian_id,))

        guardian_account = cursor.fetchone()

        if guardian_account is None:
            connection.close()
            return False, "Guardian account not found."

        # Unlock online banking
        cursor.execute("""
            UPDATE gurdians

            SET status = "Active"

            WHERE guardian_id = ?
        """,
        (guardian_id,))

        # Reset failed password attempts
        cursor.execute("""
            UPDATE guardians

            SET failed_attempts = 0

            WHERE guardian_id = (

                SELECT guardian_id

                FROM guardians

                WHERE guardian_id = ?

            )
        """,
        (guardian_id,))

        connection.commit()

        return True, "Guardian account unlocked successfully."

    except Exception as error:

        connection.rollback()

        return False, f"Error: {error}"

    finally:

        connection.close() 





        
        

def add_subject_db(subject_name, phase_name):
    """
    Add a subject to the school database and assign it to a phase.

    The subjects table stores the actual subject.

    The phase_subjects table stores which school phase
    the subject belongs to.

    This allows the same subject to belong to more than
    one phase without creating duplicate subject records.

    Example:

        MATHEMATICS can exist once in subjects.

        phase_subjects can then contain:

            Foundation Phase  -> MATHEMATICS
            Intermediate     -> MATHEMATICS
            Senior Phase     -> MATHEMATICS
            FET Phase        -> MATHEMATICS
    """

    # ----------------------------------------------------------
    # Open a connection to the SQLite database.
    # ----------------------------------------------------------
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    try:
        # ----------------------------------------------------------
        # 1. Clean the subject and phase names.
        # ----------------------------------------------------------
        subject_name = subject_name.strip()
        phase_name = phase_name.strip()

        # Make sure the subject name was entered.
        if not subject_name:
            raise ValueError(
                "Subject name cannot be empty."
            )

        # Make sure a phase was selected.
        if not phase_name:
            raise ValueError(
                "Phase name cannot be empty."
            )

        # ----------------------------------------------------------
        # 2. Check that the phase is one of the school's
        #    configured phases.
        #
        # Old Curriculum is intentionally not included because
        # it does not currently have a phase mapping.
        # ----------------------------------------------------------
        valid_phases = (
            "Foundation Phase",
            "Intermediate Phase",
            "Senior Phase",
            "FET Phase"
        )

        if phase_name not in valid_phases:
            raise ValueError(
                f"Invalid phase: {phase_name}"
            )

        # ----------------------------------------------------------
        # 3. Check whether the subject already exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT subject_id, subject_name
            FROM subjects
            WHERE subject_name = ?
        """, (subject_name,))

        existing_subject = cursor.fetchone()

        # ----------------------------------------------------------
        # 4. If the subject does not exist, create it.
        # ----------------------------------------------------------
        if existing_subject is None:

            cursor.execute("""
                INSERT INTO subjects (
                    subject_name
                )
                VALUES (?)
            """, (subject_name,))

            # Get the ID SQLite created for the new subject.
            subject_id = cursor.lastrowid

        else:
            # ------------------------------------------------------
            # The subject already exists.
            #
            # We reuse the existing subject instead of creating
            # another copy of the same subject.
            # ------------------------------------------------------
            subject_id = existing_subject["subject_id"]

        # ----------------------------------------------------------
        # 5. Check whether this subject is already assigned
        #    to the selected phase.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT phase_subject_id
            FROM phase_subjects
            WHERE phase_name = ?
              AND subject_id = ?
        """, (
            phase_name,
            subject_id
        ))

        existing_mapping = cursor.fetchone()

        # ----------------------------------------------------------
        # 6. Create the phase-to-subject mapping if it does not
        #    already exist.
        # ----------------------------------------------------------
        if existing_mapping is None:

            cursor.execute("""
                INSERT INTO phase_subjects (
                    phase_name,
                    subject_id
                )
                VALUES (?, ?)
            """, (
                phase_name,
                subject_id
            ))

        else:
            # The subject is already available in this phase.
            raise ValueError(
                f"{subject_name} is already assigned "
                f"to {phase_name}."
            )

        # ----------------------------------------------------------
        # 7. Save everything permanently.
        # ----------------------------------------------------------
        connection.commit()

        # Return the subject ID to the calling function.
        return subject_id

    except sqlite3.IntegrityError:
        # ----------------------------------------------------------
        # Undo any changes if a database integrity problem occurs.
        # ----------------------------------------------------------
        connection.rollback()

        raise ValueError(
            "Unable to add the subject because of a "
            "database integrity problem."
        )

    except Exception:
        # ----------------------------------------------------------
        # Undo any changes if another error occurs.
        # ----------------------------------------------------------
        connection.rollback()

        # Send the error back to the calling function.
        raise

    finally:
        # ----------------------------------------------------------
        # Always close the database connection.
        # ----------------------------------------------------------
        connection.close()
    



def delete_subject_db(subject_name, phase_name):
    """
    Remove a subject from a specific school phase.

    IMPORTANT:
        This function does NOT permanently delete the subject
        from the subjects table.

        It only removes the relationship between the subject
        and the selected phase in the phase_subjects table.

    Example:
        If MATHEMATICS belongs to:

            Foundation Phase
            Intermediate Phase
            Senior Phase
            FET Phase

        Removing MATHEMATICS from Senior Phase will only remove:

            Senior Phase -> MATHEMATICS

        MATHEMATICS will remain available in the subjects table
        and in the other phases.
    """

    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    try:
        # Remove the subject-to-phase relationship.
        cursor.execute("""
            DELETE FROM phase_subjects
            WHERE phase_name = ?
              AND subject_id = (
                  SELECT subject_id
                  FROM subjects
                  WHERE subject_name = ?
              )
        """, (phase_name, subject_name))

        # Check whether anything was actually deleted.
        if cursor.rowcount == 0:
            connection.rollback()

            raise ValueError(
                f"{subject_name} is not assigned to "
                f"{phase_name}."
            )

        # Save the change to the database.
        connection.commit()

    except Exception:
        # If something goes wrong, undo the database change.
        connection.rollback()
        raise

    finally:
        # Always close the database connection.
        connection.close()







def register_teacher_db(
    teacher_name,
    id_number,
    gender,
    nationality,
    password_hash,
    password_salt,
    email_address
):
    # Open a connection to our SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    # ----------------------------------------------------------
    # Find the highest student number currently in the database.
    # ----------------------------------------------------------
    #
    # MAX() finds the largest student number.
    #
    # If there are no students yet, MAX() will return None.
    cursor.execute("""
        SELECT MAX(teacher_number)
        FROM teachers
    """)

    # Get the result of our SELECT query.
    result = cursor.fetchone()

    # The result contains the highest student number.
    last_teacher = result[0]

    # ----------------------------------------------------------
    # Create the new student number.
    # ----------------------------------------------------------

    if last_teacher is None:
        # There are no students in the database yet.
        # We will start with your existing numbering system.
        teacher_number = 3000022

    else:
        # If students already exist, increase the highest
        # student number by 1.
        teacher_number = last_teacher + 1

    # ----------------------------------------------------------
    # Insert the new student.
    # ----------------------------------------------------------

    cursor.execute("""
        INSERT INTO teachers (
            teacher_number,
            teacher_name,
            id_number,
            gender,
            nationality,
            password_hash,
            password_salt,
            email_address
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        teacher_number,
        teacher_name,
        id_number,
        gender,
        nationality,
        password_hash,
        password_salt,
        email_address
    ))

    # Save the INSERT operation permanently.
    connection.commit()

    # Close the database connection.
    connection.close()

    # Return the newly created student number.
    return teacher_number
    
    
def login_teacher(teacher_number):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            t.teacher_number,
            t.teacher_name,
            t.id_number,
            t.gender,
            t.nationality,
            t.failed_attempts,
            t.email_address,
            t.status
        FROM teachers t
        WHERE t.teacher_number = ?
    """, (teacher_number,))

    teacher = cursor.fetchone()

    if teacher is None:
        connection.close()
        return None, "teacher not found."

    if teacher["status"] == "locked":
        connection.close()
        return None, "Your account is locked. Contact the Principal."

    connection.close()

    return teacher, None
    
    

def login_3timespassword_block_teacher(teacher_number, password):

    connection = get_connection()
    # 🌟 FIX 1: This allows you to use text keys like student["password_salt"]
    connection.row_factory = sqlite3.Row 
    cursor = connection.cursor()

    # 🌟 FIX 2: We select all needed columns at once so nothing gets overwritten
    cursor.execute("""
        SELECT status, password_salt, password_hash, failed_attempts
        FROM teachers
        WHERE teacher_number = ?
    """, (teacher_number,))

    teacher = cursor.fetchone()

    # If no student matches that number
    if teacher is None:
        connection.close()
        return False, "teacher not found."

    # Check if the account is already locked
    if teacher["status"] == "locked":
        connection.close()
        return False, "Your account is Blocked. Contact the Principal."

    # Verify the password
    salt = bytes.fromhex(teacher["password_salt"])
    password_hash = hashlib.sha256(password.encode() + salt).hexdigest()

    if password_hash == teacher["password_hash"]:
        # Reset failed attempts back to 0 on success
        cursor.execute("""
            UPDATE teachers
            SET failed_attempts = 0
            WHERE teacher_number = ?
        """, (teacher_number,))

        connection.commit()
        connection.close()
        return True, "Login successful."

    else:
        # Increase failed attempts count by 1
        cursor.execute("""
            UPDATE teachers
            SET failed_attempts = failed_attempts + 1
            WHERE teacher_number = ?
        """, (teacher_number,))
        connection.commit()

        # Check if they have reached 3 or more attempts
        if teacher["failed_attempts"] + 1 >= 3:
            cursor.execute("""
                UPDATE teachers
                SET status = 'locked'
                WHERE teacher_number = ?
            """, (teacher_number,))
            connection.commit()
            connection.close()
            return False, "Account locked after 3 failed attempts."

        connection.close()
        return False, "Incorrect password."    
        
        

def unlock_teacher_account(teacher_number):

    # Connect to the database
    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Check whether the account exists
        cursor.execute("""
            SELECT teacher_number
            FROM teachers
            WHERE teacher_number = ?
        """,
        (teacher_number,))

        teacher_account = cursor.fetchone()

        if teacher_account is None:
            connection.close()
            return False, "Teacher account not found."

        # Unlock online banking
        cursor.execute("""
            UPDATE teachers

            SET status = "Active"

            WHERE teacher_number = ?
        """,
        (teacher_number,))

        # Reset failed password attempts
        cursor.execute("""
            UPDATE teachers

            SET failed_attempts = 0

            WHERE teacher_number = (

                SELECT teacher_number

                FROM teachers 

                WHERE teacher_number = ?

            )
        """,
        (teacher_number,))

        connection.commit()

        return True, "Teacher account unlocked successfully."

    except Exception as error:

        connection.rollback()

        return False, f"Error: {error}"

    finally:

        connection.close()     



def assign_teacher_subject_db(
    teacher_number,
    subject_name,
    grade_name
):
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    try:
        # ----------------------------------------------------------
        # Check that the teacher exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT teacher_number, teacher_name
            FROM teachers
            WHERE teacher_number = ?
        """, (teacher_number,))

        teacher = cursor.fetchone()

        # Stop if the teacher does not exist.
        if teacher is None:
            raise ValueError("Teacher not found.")

        # ----------------------------------------------------------
        # Check that the subject exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT subject_id, subject_name
            FROM subjects
            WHERE subject_name = ?
        """, (subject_name,))

        subject = cursor.fetchone()

        # Stop if the subject does not exist.
        if subject is None:
            raise ValueError("Subject not found.")

        # ----------------------------------------------------------
        # Check that the grade exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT grade_id, grade_name
            FROM grades
            WHERE grade_name = ?
        """, (grade_name,))

        grade = cursor.fetchone()

        # Stop if the grade does not exist.
        if grade is None:
            raise ValueError("Grade not found.")

        # ----------------------------------------------------------
        # Assign the teacher to the subject and grade.
        # ----------------------------------------------------------
        cursor.execute("""
            INSERT INTO teacher_subjects (
                teacher_number,
                subject_name,
                grade_name
            )
            VALUES (?, ?, ?)
        """, (
            teacher_number,
            subject_name,
            grade_name
        ))

        # Save the assignment permanently.
        connection.commit()
        
        # Get the ID SQLite created for this subject.
        teacher_subject_id = cursor.lastrowid
        
        # Return the new subject ID AND the clean records we found
        return teacher_subject_id, teacher, subject, grade
        


    except sqlite3.IntegrityError:
        # The UNIQUE constraint prevents the same teacher,
        # subject and grade from being assigned twice.
        connection.rollback()

        raise ValueError(
            "This teacher is already assigned to this subject and grade."
        )

    except Exception:
        # Undo any changes if another error occurs.
        connection.rollback()

        raise

    finally:
        # Always close the database connection.
        connection.close()


def edit_teacher_subject_db(
    teacher_subject_id,
    new_teacher_number,
    new_subject_name,
    new_grade_name
):
    """
    Edit an existing teacher-subject-grade assignment.

    The administrator can change:
        1. Teacher
        2. Subject
        3. Grade

    The function checks that:
        - The current assignment exists.
        - The new teacher exists.
        - The new subject exists.
        - The new grade exists.
        - The subject belongs to the phase of the new grade.
        - The new assignment is not a duplicate.
    """

    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    try:
        # ----------------------------------------------------------
        # 1. Find the existing teacher-subject assignment.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT
                teacher_subject_id,
                teacher_number,
                subject_name,
                grade_name
            FROM teacher_subjects
            WHERE teacher_subject_id = ?
        """, (teacher_subject_id,))

        assignment = cursor.fetchone()

        # Stop if the assignment does not exist.
        if assignment is None:
            raise ValueError(
                "Teacher-subject assignment not found."
            )

        # ----------------------------------------------------------
        # 2. Check that the new teacher exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT
                teacher_number,
                teacher_name
            FROM teachers
            WHERE teacher_number = ?
        """, (new_teacher_number,))

        new_teacher = cursor.fetchone()

        if new_teacher is None:
            raise ValueError(
                "New teacher not found."
            )

        # ----------------------------------------------------------
        # 3. Check that the new subject exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT
                subject_id,
                subject_name
            FROM subjects
            WHERE subject_name = ?
        """, (new_subject_name,))

        new_subject = cursor.fetchone()

        if new_subject is None:
            raise ValueError(
                "New subject not found."
            )

        # ----------------------------------------------------------
        # 4. Check that the new grade exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT
                grade_id,
                grade_name
            FROM grades
            WHERE grade_name = ?
        """, (new_grade_name,))

        new_grade = cursor.fetchone()

        if new_grade is None:
            raise ValueError(
                "New grade not found."
            )

        # ----------------------------------------------------------
        # 5. Determine the phase of the new grade.
        #
        # We use the same phase rules used during student
        # subject selection.
        # ----------------------------------------------------------
        new_phase = get_phase_for_grade(
            new_grade["grade_name"]
        )

        if new_phase is None:
            if new_grade["grade_name"] == "Old Curriculum":
                raise ValueError(
                    "Old Curriculum does not have a phase mapping."
                )

            raise ValueError(
                f"Unable to determine the phase for "
                f"grade {new_grade['grade_name']}."
            )

        # ----------------------------------------------------------
        # 6. Check that the new subject belongs to the phase
        #    of the new grade.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT phase_subject_id
            FROM phase_subjects
            WHERE phase_name = ?
              AND subject_id = ?
        """, (
            new_phase,
            new_subject["subject_id"]
        ))

        phase_subject = cursor.fetchone()

        if phase_subject is None:
            raise ValueError(
                f"{new_subject['subject_name']} is not configured "
                f"for {new_grade['grade_name']} "
                f"({new_phase})."
            )

        # ----------------------------------------------------------
        # 7. Check whether the new combination already exists.
        #
        # We exclude the assignment currently being edited.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT teacher_subject_id
            FROM teacher_subjects
            WHERE teacher_number = ?
              AND subject_name = ?
              AND grade_name = ?
              AND teacher_subject_id != ?
        """, (
            new_teacher_number,
            new_subject["subject_name"],
            new_grade["grade_name"],
            teacher_subject_id
        ))

        duplicate = cursor.fetchone()

        if duplicate is not None:
            raise ValueError(
                "This teacher is already assigned to this "
                "subject and grade."
            )

        # ----------------------------------------------------------
        # 8. Update the assignment.
        # ----------------------------------------------------------
        cursor.execute("""
            UPDATE teacher_subjects
            SET
                teacher_number = ?,
                subject_name = ?,
                grade_name = ?
            WHERE teacher_subject_id = ?
        """, (
            new_teacher_number,
            new_subject["subject_name"],
            new_grade["grade_name"],
            teacher_subject_id
        ))

        # Save the changes permanently.
        connection.commit()

        # Return the old and new assignment information.
        return assignment, new_teacher, new_subject, new_grade

    except sqlite3.IntegrityError:
        # Undo changes if the database reports an integrity problem.
        connection.rollback()

        raise ValueError(
            "Unable to update the teacher-subject assignment."
        )

    except Exception:
        # Undo changes if another error occurs.
        connection.rollback()
        raise

    finally:
        # Always close the database connection.
        connection.close()





# Why do we need this? get_teacher_subjects_for_grade
# Suppose Abdul enters student:
# 1000050
# and that student is Grade 12.
# The function will search:
# teacher_subjects
# for:
# teacher_number = 3000022
# grade_id = 31
# and return:
# HISTORY
# ECONOMICS
# It will not show Mathematics because Abdul isn't assigned Mathematics.
# That's exactly the security/logic we want.

def get_teacher_subjects_for_grade(teacher_number, grade_name):
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    # ----------------------------------------------------------
    # Find subjects this teacher teaches for this specific grade.
    #
    # Your teacher_subjects table stores:
    #   subject_name
    #   grade_name
    #
    # So we compare the names directly.
    # ----------------------------------------------------------
    cursor.execute("""
        SELECT
            ts.teacher_subject_id,
            s.subject_id,
            ts.subject_name,
            ts.grade_name
        FROM teacher_subjects ts

        JOIN subjects s
            ON ts.subject_name = s.subject_name

        WHERE ts.teacher_number = ?
        AND ts.grade_name = ?

        ORDER BY ts.subject_name
    """, (
        teacher_number,
        grade_name
    ))

    # Get all matching subjects.
    subjects = cursor.fetchall()

    # Close the database connection.
    connection.close()

    # Return the subjects to the teacher menu.
    return subjects



    
def record_mark_db(
    student_number,
    subject_id,
    teacher_number,
    mark_value,
    total_possible,
    exam_date
):
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    try:
        # ----------------------------------------------------------
        # Check that the student exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT student_number
            FROM students
            WHERE student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

        # Stop if the student does not exist.
        if student is None:
            raise ValueError("Student not found.")

        # ----------------------------------------------------------
        # Check that the subject exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT subject_id
            FROM subjects
            WHERE subject_id = ?
        """, (subject_id,))

        subject = cursor.fetchone()

        # Stop if the subject does not exist.
        if subject is None:
            raise ValueError("Subject not found.")

        # ----------------------------------------------------------
        # Check that the teacher exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT teacher_number
            FROM teachers
            WHERE teacher_number = ?
        """, (teacher_number,))

        teacher = cursor.fetchone()

        # Stop if the teacher does not exist.
        if teacher is None:
            raise ValueError("Teacher not found.")

        # ----------------------------------------------------------
        # Validate the mark.
        # ----------------------------------------------------------

        # A mark cannot be negative.
        if mark_value < 0:
            raise ValueError("Mark cannot be negative.")

        # The total possible mark must be greater than zero.
        if total_possible <= 0:
            raise ValueError(
                "Total possible mark must be greater than zero."
            )

        # A mark cannot be greater than the total possible mark.
        if mark_value > total_possible:
            raise ValueError(
                "Mark cannot be greater than the total possible mark."
            )

        # ----------------------------------------------------------
        # Save the mark in the marks table.
        # ----------------------------------------------------------
        cursor.execute("""
            INSERT INTO marks (
                mark_value,
                total_possible,
                exam_date,
                student_number,
                subject_id,
                teacher_number
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            mark_value,
            total_possible,
            exam_date,
            student_number,
            subject_id,
            teacher_number
        ))

        # Save the changes permanently.
        connection.commit()

    except Exception:
        # If something goes wrong, undo the database changes.
        connection.rollback()

        # Send the error back to the calling function.
        raise

    finally:
        # Always close the database connection.
        connection.close()


# this fun is to get the teachers assigned subject 
def get_teacher_subjects(teacher_number):
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor for executing SQL commands.
    cursor = connection.cursor()

    # ----------------------------------------------------------
    # Find the subjects and grades assigned to this teacher.
    # ----------------------------------------------------------
    cursor.execute("""
        SELECT
            ts.teacher_subject_id,
            ts.subject_id,
            s.subject_name,
            ts.grade_id,
            g.grade_name
        FROM teacher_subjects ts

        JOIN subjects s
            ON ts.subject_id = s.subject_id

        JOIN grades g
            ON ts.grade_id = g.grade_id

        WHERE ts.teacher_number = ?

        ORDER BY g.grade_id, s.subject_name
    """, (teacher_number,))

    # Get all assignments belonging to this teacher.
    assignments = cursor.fetchall()

    # Close the database connection.
    connection.close()

    # Return the assignments to the teacher menu.
    return assignments


# The important part is that we're storing the subject_id, even though your teacher_subjects table uses subject_name. That's okay because your main attendance table was designed to use subject_id.

def record_attendance_db(
    student_number,
    subject_id,
    teacher_number,
    attendance_status,
    attendance_date
):
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    try:
        # ----------------------------------------------------------
        # Check that the student exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT student_number
            FROM students
            WHERE student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

        # Stop if the student does not exist.
        if student is None:
            raise ValueError("Student not found.")

        # ----------------------------------------------------------
        # Check that the subject exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT subject_id
            FROM subjects
            WHERE subject_id = ?
        """, (subject_id,))

        subject = cursor.fetchone()

        # Stop if the subject does not exist.
        if subject is None:
            raise ValueError("Subject not found.")

        # ----------------------------------------------------------
        # Check that the teacher exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT teacher_number
            FROM teachers
            WHERE teacher_number = ?
        """, (teacher_number,))

        teacher = cursor.fetchone()

        # Stop if the teacher does not exist.
        if teacher is None:
            raise ValueError("Teacher not found.")

        # ----------------------------------------------------------
        # Check that the attendance status is valid.
        # ----------------------------------------------------------

        # Only these two attendance statuses are allowed.
        if attendance_status not in ("Present", "Absent"):
            raise ValueError(
                "Attendance must be Present or Absent."
            )

        # ----------------------------------------------------------
        # Save the attendance record.
        # ----------------------------------------------------------
        cursor.execute("""
            INSERT INTO attendance (
                attendance_date,
                status,
                student_number,
                subject_id,
                teacher_number
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            attendance_date,
            attendance_status,
            student_number,
            subject_id,
            teacher_number
        ))

        # Save the changes permanently.
        connection.commit()

    except sqlite3.IntegrityError:
        # The attendance table has a UNIQUE constraint:
        #
        # attendance_date + student_number + subject_id
        #
        # This prevents recording attendance twice for the
        # same student, subject and date.
        connection.rollback()

        raise ValueError(
            "Attendance has already been recorded for "
            "this student, subject and date."
        )

    except Exception:
        # Undo any changes if another error occurs.
        connection.rollback()

        # Send the error back to the teacher menu.
        raise

    finally:
        # Always close the database connection.
        connection.close()




def assign_homework_db(
    title,
    description,
    due_date,
    date_posted,
    grade_id,
    subject_id,
    teacher_number
):
    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    try:
        # ----------------------------------------------------------
        # Check that the teacher exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT teacher_number
            FROM teachers
            WHERE teacher_number = ?
        """, (teacher_number,))

        teacher = cursor.fetchone()

        # Stop if the teacher does not exist.
        if teacher is None:
            raise ValueError("Teacher not found.")

        # ----------------------------------------------------------
        # Check that the grade exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT grade_id, grade_name
            FROM grades
            WHERE grade_id = ?
        """, (grade_id,))

        grade = cursor.fetchone()

        # Stop if the grade does not exist.
        if grade is None:
            raise ValueError("Grade not found.")

        # ----------------------------------------------------------
        # Check that the subject exists.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT subject_id, subject_name
            FROM subjects
            WHERE subject_id = ?
        """, (subject_id,))

        subject = cursor.fetchone()

        # Stop if the subject does not exist.
        if subject is None:
            raise ValueError("Subject not found.")

        # ----------------------------------------------------------
        # Check that the teacher is assigned to this
        # subject and grade.
        #
        # IMPORTANT:
        # Your teacher_subjects table stores subject_name
        # and grade_name.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT teacher_subject_id
            FROM teacher_subjects
            WHERE teacher_number = ?
            AND subject_name = ?
            AND grade_name = ?
        """, (
            teacher_number,
            subject["subject_name"],
            grade["grade_name"]
        ))

        assignment = cursor.fetchone()

        # Stop if the teacher is not assigned to this
        # subject and grade.
        if assignment is None:
            raise ValueError(
                "You are not assigned to teach this "
                "subject for this grade."
            )

        # ----------------------------------------------------------
        # Check that the homework title is not empty.
        # ----------------------------------------------------------
        if not title.strip():
            raise ValueError(
                "Homework title cannot be empty."
            )

        # ----------------------------------------------------------
        # Save the homework in SQLite.
        # ----------------------------------------------------------
        cursor.execute("""
            INSERT INTO homework (
                title,
                description,
                due_date,
                date_posted,
                grade_id,
                subject_id,
                teacher_number
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            due_date,
            date_posted,
            grade_id,
            subject_id,
            teacher_number
        ))

        # Save the changes permanently.
        connection.commit()

        # Return the new homework ID.
        return cursor.lastrowid

    except sqlite3.IntegrityError:
        # Undo the database changes if SQLite reports
        # an integrity error.
        connection.rollback()

        raise ValueError(
            "Could not save the homework."
        )

    except Exception:
        # Undo any changes if another error occurs.
        connection.rollback()

        # Send the error back to the teacher menu.
        raise

    finally:
        # Always close the database connection.
        connection.close()






# ---------------------------------------------------------
# GET CURRENT SCHOOL YEAR AND TERM
# ---------------------------------------------------------
# This function looks at today's date and searches the
# school_terms table to find which school year and term
# is currently active.
#
# We do NOT hard-code 2026 or Term 1 here.
# The database controls the school calendar.
# ---------------------------------------------------------

def get_current_school_term_db():

    # Get today's date from the computer.
    today = datetime.now().strftime("%Y-%m-%d")

    # Open the database.
    connection = get_connection()
    cursor = connection.cursor()

    # Find the term where today's date is between
    # the term's start date and end date.
    cursor.execute("""
        SELECT
            school_year,
            term_number,
            start_date,
            end_date
        FROM school_terms
        WHERE start_date <= ?
        AND end_date >= ?
        LIMIT 1
    """, (today, today))

    term = cursor.fetchone()

    # Close the database connection.
    connection.close()

    # If today's date isn't inside any term,
    # return None.
    if term is None:
        return None

    # Return the school year and term information.
    return {
        "school_year": term["school_year"],
        "term_number": term["term_number"],
        "start_date": term["start_date"],
        "end_date": term["end_date"]
    }





# ----------------------------------------------------------
# GENERATE STUDENT REPORT CARD PDF
# ----------------------------------------------------------

def generate_report_card_pdf(student_number, school_year, term_number):
    # ReportLab is used to create the PDF document.
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from datetime import datetime

    # Get the student's report-card results from SQLite.
    report_card = get_student_report_card_db(student_number)

    # If the student has no results, there is nothing to put
    # into the report card.
    if not report_card:
        print("\nNo results available for this student.")
        return

    # ------------------------------------------------------
    # GET STUDENT INFORMATION
    # ------------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            s.student_number,
            s.student_name,
            s.classroom,
            g.grade_name
        FROM students s
        JOIN grades g
            ON g.grade_id = s.grade_id
        WHERE s.student_number = ?
    """, (student_number,))

    student = cursor.fetchone()
    connection.close()

    if student is None:
        print("\nStudent not found.")
        return

    # ------------------------------------------------------
    # CREATE PDF FILE NAME
    # ------------------------------------------------------

    filename = (
        f"report_card_"
        f"{student['student_number']}_"
        f"{school_year}_"
        f"term{term_number}.pdf"
    )

    # Create the PDF using A4 paper.
    pdf = canvas.Canvas(filename, pagesize=A4)

    # Get the width and height of an A4 page.
    page_width, page_height = A4

    # ------------------------------------------------------
    # SCHOOL TITLE
    # ------------------------------------------------------

    pdf.setFont("Helvetica-Bold", 18)

    pdf.drawCentredString(
        page_width / 2,
        page_height - 30 * mm,
        "PYTHON SCHOOL"
    )

    pdf.setFont("Helvetica-Bold", 14)

    pdf.drawCentredString(
        page_width / 2,
        page_height - 40 * mm,
        "STUDENT REPORT CARD"
    )

    # ------------------------------------------------------
    # STUDENT INFORMATION
    # ------------------------------------------------------

    pdf.setFont("Helvetica", 11)

    y = page_height - 60 * mm

    # Show the school year of this report card.
    y -= 8 * mm

    pdf.drawString(
        25 * mm,
        y,
        f"School Year : {school_year}"
    )

    # Show the school term of this report card.
    y -= 8 * mm

    pdf.drawString(
        25 * mm,
        y,
        f"Term : {term_number}"
    )

    y -= 15 * mm

    pdf.drawString(
        25 * mm,
        y,
        f"Student Number : {student['student_number']}"
    )

    y -= 8 * mm

    pdf.drawString(
        25 * mm,
        y,
        f"Grade : {student['grade_name']}"
    )

    y -= 8 * mm

    pdf.drawString(
        25 * mm,
        y,
        f"Classroom : {student['classroom']}"
    )

    y -= 15 * mm

    # ------------------------------------------------------
    # RESULTS TABLE HEADER
    # ------------------------------------------------------

    pdf.setFont("Helvetica-Bold", 11)

    pdf.drawString(
        25 * mm,
        y,
        "SUBJECT"
    )

    pdf.drawString(
        125 * mm,
        y,
        "MARK"
    )

    pdf.drawString(
        155 * mm,
        y,
        "PERCENTAGE"
    )

    y -= 5 * mm

    # Draw a line underneath the table heading.
    pdf.line(
        25 * mm,
        y,
        185 * mm,
        y
    )

    y -= 8 * mm

    # ------------------------------------------------------
    # DISPLAY SUBJECT RESULTS
    # ------------------------------------------------------

    pdf.setFont("Helvetica", 10)

    total_percentage = 0
    number_of_subjects = len(report_card)

    for result in report_card:

        mark = result["mark_value"]
        total_possible = result["total_possible"]

        # Calculate the student's percentage.
        percentage = (
            mark / total_possible
        ) * 100

        pdf.drawString(
            25 * mm,
            y,
            result["subject_name"]
        )

        pdf.drawString(
            125 * mm,
            y,
            f"{mark:.1f}/{total_possible:.1f}"
        )

        pdf.drawString(
            155 * mm,
            y,
            f"{percentage:.1f}%"
        )

        total_percentage += percentage

        y -= 8 * mm

    # ------------------------------------------------------
    # CALCULATE AVERAGE
    # ------------------------------------------------------

    average = (
        total_percentage / number_of_subjects
    )

    y -= 5 * mm

    pdf.line(
        25 * mm,
        y,
        185 * mm,
        y
    )

    y -= 10 * mm

    pdf.setFont("Helvetica-Bold", 11)

    pdf.drawString(
        25 * mm,
        y,
        f"Average : {average:.2f}%"
    )

    y -= 10 * mm

    # Determine whether the student passed.
    if average >= 50:
        result_text = "PASS"
    else:
        result_text = "FAIL"

    pdf.drawString(
        25 * mm,
        y,
        f"Result : {result_text}"
    )

    # ------------------------------------------------------
    # FOOTER
    # ------------------------------------------------------

    pdf.setFont("Helvetica", 8)

    pdf.drawString(
        25 * mm,
        15 * mm,
        f"Generated: {datetime.now().strftime('%Y-%m-%d')}"
    )

    # Save and close the PDF.
    pdf.save()

    print("\nReport card created successfully!")
    print(f"PDF file: {filename}")




def generate_guardian_child_report_card_pdf(
    student_number,
    school_year,
    term_number
):
    """
    Generate a PDF report card for a child selected
    by a guardian.

    This function:
    1. Gets the student's information.
    2. Gets marks for the selected term only.
    3. Calculates each subject percentage.
    4. Calculates the overall average.
    5. Creates a PDF report card.
    """

    # ---------------------------------------------------------
    # STEP 1:
    # Get the student's report-card results for the
    # selected school term.
    # ---------------------------------------------------------

    report_card = get_student_report_card_by_term_db(
        student_number,
        school_year,
        term_number
    )

    # If there are no marks for this term,
    # there is nothing to print.
    if not report_card:
        print(
            f"\nNo report-card results found for "
            f"Term {term_number}."
        )
        return

    # ---------------------------------------------------------
    # STEP 2:
    # Get the student's basic information.
    # ---------------------------------------------------------

    connection = get_connection()

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            s.student_number,
            s.student_name,
            s.classroom,
            g.grade_name
        FROM students s
        JOIN grades g
            ON g.grade_id = s.grade_id
        WHERE s.student_number = ?
    """, (student_number,))

    student = cursor.fetchone()

    connection.close()

    # Make sure the student exists.
    if student is None:
        print("\nStudent not found.")
        return

    # ---------------------------------------------------------
    # STEP 3:
    # Create the PDF filename.
    # ---------------------------------------------------------

    filename = (
        f"guardian_report_card_"
        f"{student['student_number']}_"
        f"{school_year}_"
        f"term{term_number}.pdf"
    )

    # ---------------------------------------------------------
    # STEP 4:
    # Create the PDF document.
    # ---------------------------------------------------------

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from datetime import datetime

    pdf = canvas.Canvas(
        filename,
        pagesize=A4
    )

    page_width, page_height = A4

    # ---------------------------------------------------------
    # SCHOOL TITLE
    # ---------------------------------------------------------

    pdf.setFont(
        "Helvetica-Bold",
        18
    )

    pdf.drawCentredString(
        page_width / 2,
        page_height - 30 * mm,
        "PYTHON SCHOOL"
    )

    pdf.setFont(
        "Helvetica-Bold",
        14
    )

    pdf.drawCentredString(
        page_width / 2,
        page_height - 40 * mm,
        "STUDENT REPORT CARD"
    )

    # ---------------------------------------------------------
    # STUDENT INFORMATION
    # ---------------------------------------------------------

    pdf.setFont(
        "Helvetica",
        11
    )

    y = page_height - 60 * mm

    pdf.drawString(
        25 * mm,
        y,
        f"School Year : {school_year}"
    )

    y -= 8 * mm

    pdf.drawString(
        25 * mm,
        y,
        f"Term : {term_number}"
    )

    y -= 8 * mm

    pdf.drawString(
        25 * mm,
        y,
        f"Student Number : {student['student_number']}"
    )

    y -= 8 * mm

    pdf.drawString(
        25 * mm,
        y,
        f"Student Name : {student['student_name']}"
    )

    y -= 8 * mm

    pdf.drawString(
        25 * mm,
        y,
        f"Grade : {student['grade_name']}"
    )

    y -= 8 * mm

    pdf.drawString(
        25 * mm,
        y,
        f"Classroom : {student['classroom']}"
    )

    y -= 15 * mm

    # ---------------------------------------------------------
    # TABLE HEADINGS
    # ---------------------------------------------------------

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        25 * mm,
        y,
        "SUBJECT"
    )

    pdf.drawString(
        115 * mm,
        y,
        "MARK"
    )

    pdf.drawString(
        145 * mm,
        y,
        "PERCENTAGE"
    )

    pdf.drawString(
        175 * mm,
        y,
        "DATE"
    )

    y -= 5 * mm

    pdf.line(
        25 * mm,
        y,
        190 * mm,
        y
    )

    y -= 8 * mm

    # ---------------------------------------------------------
    # DISPLAY EACH SUBJECT RESULT
    # ---------------------------------------------------------

    pdf.setFont(
        "Helvetica",
        9
    )

    total_percentage = 0

    number_of_subjects = len(report_card)

    for result in report_card:

        mark = result["mark_value"]

        total_possible = result["total_possible"]

        # Protect against division by zero.
        if total_possible > 0:
            percentage = (
                mark / total_possible
            ) * 100
        else:
            percentage = 0

        pdf.drawString(
            25 * mm,
            y,
            result["subject_name"]
        )

        pdf.drawString(
            115 * mm,
            y,
            f"{mark:.1f}/{total_possible:.1f}"
        )

        pdf.drawString(
            145 * mm,
            y,
            f"{percentage:.1f}%"
        )

        pdf.drawString(
            175 * mm,
            y,
            result["exam_date"]
        )

        total_percentage += percentage

        y -= 8 * mm

    # ---------------------------------------------------------
    # CALCULATE OVERALL AVERAGE
    # ---------------------------------------------------------

    if number_of_subjects > 0:
        average = (
            total_percentage /
            number_of_subjects
        )
    else:
        average = 0

    y -= 5 * mm

    pdf.line(
        25 * mm,
        y,
        190 * mm,
        y
    )

    y -= 10 * mm

    pdf.setFont(
        "Helvetica-Bold",
        11
    )

    pdf.drawString(
        25 * mm,
        y,
        f"Average : {average:.2f}%"
    )

    y -= 10 * mm

    # ---------------------------------------------------------
    # PASS / FAIL
    # ---------------------------------------------------------

    if average >= 50:
        result_text = "PASS"
    else:
        result_text = "FAIL"

    pdf.drawString(
        25 * mm,
        y,
        f"Result : {result_text}"
    )

    # ---------------------------------------------------------
    # FOOTER
    # ---------------------------------------------------------

    pdf.setFont(
        "Helvetica",
        8
    )

    pdf.drawString(
        25 * mm,
        15 * mm,
        "Generated by Guardian Panel: "
        + datetime.now().strftime("%Y-%m-%d")
    )

    # Finish and save the PDF.
    pdf.save()

    print(
        "\nReport card created successfully!"
    )

    print(
        f"PDF file: {filename}"
    )










# This function will automatically use the logged-in student's:
# Grade
# Classroom
# and retrieve the correct timetable from SQLite.
# Student sees the timetable relevant to their grade and classroom
# ----------------------------------------------------------
# GET STUDENT TIMETABLE FROM SQLITE
# ----------------------------------------------------------

def get_student_timetable_db(student_number):

    # Open the school database.
    connection = get_connection()

    # Create a cursor to run SQL queries.
    cursor = connection.cursor()

    # Find the student's grade and classroom.
    cursor.execute("""
        
        SELECT
            s.student_number,
            s.grade_id,
            s.classroom,
            g.grade_name
        
        FROM students s
        JOIN grades g
            ON g.grade_id = s.grade_id
        WHERE s.student_number = ?
    """, (student_number,))

    student = cursor.fetchone()

    # If the student does not exist, stop here.
    if student is None:
        connection.close()
        return []

    # ------------------------------------------------------
    # FIND THE STUDENT'S TIMETABLE
    # ------------------------------------------------------
    #
    # We match BOTH:
    #
    # 1. Grade
    # 2. Classroom
    #
    # This prevents a student in 12A from seeing the
    # timetable belonging to another Grade 12 classroom.
    #

    cursor.execute("""
        SELECT
            tt.timetable_id,
            g.grade_name,
            tt.classroom,
            tt.day,
            tt.start_time,
            tt.end_time,
            s.subject_name,
            t.teacher_name
        FROM timetable tt

        JOIN grades g
            ON g.grade_id = tt.grade_id

        JOIN subjects s
            ON s.subject_id = tt.subject_id

        JOIN teachers t
            ON t.teacher_number = tt.teacher_number

        WHERE tt.grade_id = ?
        AND tt.classroom = ?

        ORDER BY
            CASE tt.day
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
                ELSE 8
            END,
            tt.start_time
    """, (
        # Use the student's actual grade_id.
        #
        # We need to get it from the students table.
        #
        student["grade_id"],
        student["classroom"]
    ))

    timetable = cursor.fetchall()

    connection.close()

    return timetable



# ----------------------------------------------------------
# GET SCHOOL NEWS FROM SQLITE
# ----------------------------------------------------------

def get_student_school_news_db():

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can run SQL queries.
    cursor = connection.cursor()

    # Get school news from the database.
    #
    # We join with the admins table so we can display
    # the name of the administrator who posted the news.
    cursor.execute("""
        SELECT
            sn.news_id,
            sn.title,
            sn.content,
            sn.date_posted,
            sn.category,
            a.admin_name
        FROM school_news sn
        JOIN admins a
            ON a.admin_id = sn.admin_id
        ORDER BY sn.date_posted DESC, sn.news_id DESC
    """)

    # Fetch all available news records.
    news = cursor.fetchall()

    # Close the database connection.
    connection.close()

    # Return the news records to the student menu.
    return news
    
    


# ----------------------------------------------------------
# POST SCHOOL NEWS
# ----------------------------------------------------------

def post_school_news_db(
    title,
    content,
    category,
    admin_id,
    grade_id=None
):

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can run SQL commands.
    cursor = connection.cursor()

    try:
        # Get today's date.
        date_posted = date.today().isoformat()

        # Insert the news into the school_news table.
        cursor.execute("""
            INSERT INTO school_news (
                title,
                content,
                date_posted,
                category,
                admin_id,
                grade_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title,
            content,
            date_posted,
            category,
            admin_id,
            grade_id
        ))

        # Save the new news record.
        connection.commit()

        print("\nSchool news posted successfully.")

    except Exception as error:

        # Undo the database change if something goes wrong.
        connection.rollback()

        print(f"\nError posting school news: {error}")

    finally:

        # Always close the database connection.
        connection.close()   
        



# ----------------------------------------------------------
# ADD TIMETABLE TO SQLITE
# ----------------------------------------------------------

def add_timetable_db(
    grade_name,
    classroom,
    day,
    start_time,
    end_time,
    subject_name,
    teacher_number
):

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can run SQL commands.
    cursor = connection.cursor()

    try:

        # --------------------------------------------------
        # FIND THE GRADE ID
        # --------------------------------------------------

        # The Principal enters the grade name, for example 12.
        # We find the matching grade_id from the grades table.
        cursor.execute("""
            SELECT grade_id
            FROM grades
            WHERE grade_name = ?
        """, (grade_name,))

        grade = cursor.fetchone()

        # Check whether the grade exists.
        if grade is None:
            print("\nGrade not found.")
            return

        # Store the actual grade ID from the database.
        grade_id = grade["grade_id"]

        # --------------------------------------------------
        # FIND THE SUBJECT ID
        # --------------------------------------------------

        # The Principal enters the subject name.
        # We find its subject_id from the subjects table.
        cursor.execute("""
            SELECT subject_id
            FROM subjects
            WHERE subject_name = ?
        """, (subject_name,))

        subject = cursor.fetchone()

        # Check whether the subject exists.
        if subject is None:
            print("\nSubject not found.")
            return

        # Store the actual subject ID.
        subject_id = subject["subject_id"]

        # --------------------------------------------------
        # CHECK THE TEACHER ID
        # --------------------------------------------------

        # The Principal enters the unique teacher number.
        cursor.execute("""
            SELECT teacher_number
            FROM teachers
            WHERE teacher_number = ?
        """, (teacher_number,))

        teacher = cursor.fetchone()

        # Check whether the teacher exists.
        if teacher is None:
            print("\nTeacher ID not found.")
            return

        # --------------------------------------------------
        # INSERT THE TIMETABLE
        # --------------------------------------------------

        # Now that we have:
        # grade_id
        # subject_id
        # teacher_number
        #
        # we can insert the timetable record.
        cursor.execute("""
            INSERT INTO timetable (
                grade_id,
                classroom,
                day,
                start_time,
                end_time,
                subject_id,
                teacher_number
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            grade_id,
            classroom,
            day,
            start_time,
            end_time,
            subject_id,
            teacher_number
        ))

        # Save the timetable record.
        connection.commit()

        print("\nTimetable added successfully.")

    except Exception as error:

        # Undo the database change if something goes wrong.
        connection.rollback()

        print(f"\nError adding timetable: {error}")

    finally:

        # Always close the database connection.
        connection.close()

        
        
# ----------------------------------------------------------
# VIEW ALL TIMETABLE RECORDS FROM SQLITE FOR ADMIN
# ----------------------------------------------------------

def view_timetable_admin():

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can run SQL queries.
    cursor = connection.cursor()

    # Get all timetable records.
    #
    # We join the related tables so that we can display:
    # - Grade name
    # - Classroom
    # - Day
    # - Time
    # - Subject name
    # - Teacher ID
    # - Teacher name
    cursor.execute("""
        SELECT
            tt.timetable_id,
            g.grade_name,
            tt.classroom,
            tt.day,
            tt.start_time,
            tt.end_time,
            s.subject_name,
            t.teacher_number,
            t.teacher_name
        FROM timetable tt
        JOIN grades g
            ON g.grade_id = tt.grade_id
        JOIN subjects s
            ON s.subject_id = tt.subject_id
        JOIN teachers t
            ON t.teacher_number = tt.teacher_number
        ORDER BY
            CASE tt.day
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
                ELSE 8
            END,
            tt.start_time
    """)

    # Get all records returned by the query.
    timetable = cursor.fetchall()

    # Close the database connection.
    connection.close()

    # Return the timetable records.
    return timetable




# ----------------------------------------------------------
# EDIT TIMETABLE RECORD
# ----------------------------------------------------------

def edit_timetable_db():

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can run SQL commands.
    cursor = connection.cursor()

    try:

        # --------------------------------------------------
        # ASK WHICH TIMETABLE RECORD TO EDIT
        # --------------------------------------------------

        # Each timetable record has a unique timetable_id.
        timetable_id = int(input("Enter Timetable ID to edit: "))

        # Check that the timetable record exists.
        cursor.execute("""
            SELECT timetable_id
            FROM timetable
            WHERE timetable_id = ?
        """, (timetable_id,))

        timetable = cursor.fetchone()

        if timetable is None:
            print("\nTimetable ID not found.")
            return

        # --------------------------------------------------
        # GET THE NEW INFORMATION
        # --------------------------------------------------

        grade_name = input("Enter New Grade: ")
        classroom = input("Enter New Classroom: ")
        day = input("Enter New Day: ")
        start_time = input("Enter New Start Time: ")
        end_time = input("Enter New End Time: ")
        subject_name = input("Enter New Subject: ")

        # Teacher number is unique.
        teacher_number = int(input("Enter New Teacher ID: "))

        # --------------------------------------------------
        # FIND THE GRADE ID
        # --------------------------------------------------

        cursor.execute("""
            SELECT grade_id
            FROM grades
            WHERE grade_name = ?
        """, (grade_name,))

        grade = cursor.fetchone()

        if grade is None:
            print("\nGrade not found.")
            return

        grade_id = grade["grade_id"]

        # --------------------------------------------------
        # FIND THE SUBJECT ID
        # --------------------------------------------------

        cursor.execute("""
            SELECT subject_id
            FROM subjects
            WHERE subject_name = ?
        """, (subject_name,))

        subject = cursor.fetchone()

        if subject is None:
            print("\nSubject not found.")
            return

        subject_id = subject["subject_id"]

        # --------------------------------------------------
        # CHECK THE TEACHER ID
        # --------------------------------------------------

        cursor.execute("""
            SELECT teacher_number
            FROM teachers
            WHERE teacher_number = ?
        """, (teacher_number,))

        teacher = cursor.fetchone()

        if teacher is None:
            print("\nTeacher ID not found.")
            return

        # --------------------------------------------------
        # UPDATE THE TIMETABLE
        # --------------------------------------------------

        cursor.execute("""
            UPDATE timetable
            SET
                grade_id = ?,
                classroom = ?,
                day = ?,
                start_time = ?,
                end_time = ?,
                subject_id = ?,
                teacher_number = ?
            WHERE timetable_id = ?
        """, (
            grade_id,
            classroom,
            day,
            start_time,
            end_time,
            subject_id,
            teacher_number,
            timetable_id
        ))

        # Save the changes.
        connection.commit()

        print("\nTimetable updated successfully.")

    except ValueError:
        print("\nNumbers only for Timetable ID and Teacher ID.")

    except Exception as error:

        # Undo the update if something goes wrong.
        connection.rollback()

        print(f"\nError editing timetable: {error}")

    finally:

        # Always close the database connection.
        connection.close()




# ----------------------------------------------------------
# DELETE TIMETABLE RECORD
# ----------------------------------------------------------

def delete_timetable_db():

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can run SQL commands.
    cursor = connection.cursor()

    try:

        # --------------------------------------------------
        # ASK WHICH RECORD TO DELETE
        # --------------------------------------------------

        # Timetable ID uniquely identifies one timetable record.
        timetable_id = int(input("Enter Timetable ID to delete: "))

        # --------------------------------------------------
        # FIND THE TIMETABLE RECORD
        # --------------------------------------------------

        # Get the timetable information before deleting it.
        # This allows us to show the Principal exactly
        # which lesson is about to be deleted.
        cursor.execute("""
            SELECT
                tt.timetable_id,
                g.grade_name,
                tt.classroom,
                tt.day,
                tt.start_time,
                tt.end_time,
                s.subject_name,
                t.teacher_number,
                t.teacher_name
            FROM timetable tt
            JOIN grades g
                ON g.grade_id = tt.grade_id
            JOIN subjects s
                ON s.subject_id = tt.subject_id
            JOIN teachers t
                ON t.teacher_number = tt.teacher_number
            WHERE tt.timetable_id = ?
        """, (timetable_id,))

        timetable = cursor.fetchone()

        # Check whether the timetable exists.
        if timetable is None:
            print("\nTimetable ID not found.")
            return

        # --------------------------------------------------
        # SHOW THE RECORD
        # --------------------------------------------------

        print("\n===== TIMETABLE TO DELETE =====")

        print(f"Timetable ID : {timetable['timetable_id']}")
        print(f"Grade        : {timetable['grade_name']}")
        print(f"Classroom    : {timetable['classroom']}")
        print(f"Day          : {timetable['day']}")
        print(
            f"Time         : "
            f"{timetable['start_time']} - {timetable['end_time']}"
        )
        print(f"Subject      : {timetable['subject_name']}")
        print(f"Teacher ID   : {timetable['teacher_number']}")
        print(f"Teacher      : {timetable['teacher_name']}")

        # --------------------------------------------------
        # ASK FOR CONFIRMATION
        # --------------------------------------------------

        confirmation = input(
            "\nAre you sure you want to delete this timetable? (yes/no): "
        )

        if confirmation.lower() != "yes":
            print("\nDeletion cancelled.")
            return

        # --------------------------------------------------
        # DELETE THE RECORD
        # --------------------------------------------------

        cursor.execute("""
            DELETE FROM timetable
            WHERE timetable_id = ?
        """, (timetable_id,))

        # Save the deletion.
        connection.commit()

        print("\nTimetable deleted successfully.")

    except ValueError:

        # The Timetable ID must be a number.
        print("\nTimetable ID must be a number.")

    except Exception as error:

        # Undo the database change if something goes wrong.
        connection.rollback()

        print(f"\nError deleting timetable: {error}")

    finally:

        # Always close the database connection.
        connection.close()




# we will use this function to display fees status in student profile 
# ----------------------------------------------------------
# GET STUDENT FEE STATUS FROM SQLITE
# ----------------------------------------------------------

def get_student_fee_status_db(student_number):

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can run SQL queries.
    cursor = connection.cursor()

    try:

        # --------------------------------------------------
        # GET THE STUDENT'S ANNUAL FEE
        # --------------------------------------------------

        # We get the student's grade first.
        # The annual fee comes from fees_structure.
        cursor.execute("""
            SELECT
                s.student_number,
                g.grade_name,
                fs.amount AS annual_fee
            FROM students s
            JOIN grades g
                ON g.grade_id = s.grade_id
            JOIN fees_structure fs
                ON fs.grade_id = s.grade_id
            WHERE s.student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

        # Check whether the student exists and has
        # a fee structure.
        if student is None:
            return None

        annual_fee = float(student["annual_fee"])

        # --------------------------------------------------
        # GET THE CURRENT SCHOOL TERM
        # --------------------------------------------------

        current_term = get_current_school_term_db()

        if current_term is None:

            print("\nNo current school term found.")

            return None

        school_year = current_term["school_year"]
        current_term_number = current_term["term_number"]

        # --------------------------------------------------
        # CALCULATE THE TERM FEE
        # --------------------------------------------------

        # There are four terms in the school year.
        term_fee = annual_fee / 4

        # --------------------------------------------------
        # GET ALL PAYMENTS FOR THIS SCHOOL YEAR
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                payment_id,
                amount,
                payment_date,
                term_number
            FROM fee_payments
            WHERE student_number = ?
            AND school_year = ?
            ORDER BY payment_date ASC, payment_id ASC
        """, (student_number, school_year))

        payments = cursor.fetchall()

        # --------------------------------------------------
        # CALCULATE HOW MUCH HAS BEEN PAID
        # --------------------------------------------------

        total_paid = sum(
            float(payment["amount"])
            for payment in payments
        )

        # --------------------------------------------------
        # WORK OUT THE BALANCE FOR EACH TERM
        # --------------------------------------------------

        remaining_payment = total_paid

        previous_balance = 0.0
        current_term_paid = 0.0

        # We process the four terms from Term 1
        # through Term 4.
        for term_number in range(1, 5):

            # Each term starts with the same term fee.
            term_balance = term_fee

            # Apply available payments to this term.
            payment_for_term = min(
                remaining_payment,
                term_balance
            )

            term_balance -= payment_for_term
            remaining_payment -= payment_for_term

            # If this is before the current term,
            # its unpaid balance is a previous balance.
            if term_number < current_term_number:

                previous_balance += term_balance

            # If this is the current term, record
            # how much was paid toward it.
            elif term_number == current_term_number:

                current_term_paid = payment_for_term

        # --------------------------------------------------
        # CALCULATE TOTAL AMOUNT OWING
        # --------------------------------------------------

        # The total amount due up to the current term
        # consists of:
        #
        # previous unpaid terms
        # +
        # current term unpaid amount
        #
        current_term_balance = max(
            term_fee - current_term_paid,
            0
        )

        total_due = previous_balance + current_term_balance

        # Prevent tiny floating-point values such as
        # 1.776e-15 from appearing.
        total_due = round(total_due, 2)
        previous_balance = round(previous_balance, 2)
        current_term_paid = round(current_term_paid, 2)
        current_term_balance = round(current_term_balance, 2)

        # --------------------------------------------------
        # DETERMINE PAYMENT STATUS
        # --------------------------------------------------

        if total_due <= 0:

            status = "PAID"

        else:

            status = "OWING"

        # --------------------------------------------------
        # RETURN THE FEE INFORMATION
        # --------------------------------------------------

        return {
            "student_number": student["student_number"],
            "grade_name": student["grade_name"],
            "annual_fee": round(annual_fee, 2),
            "term_fee": round(term_fee, 2),
            "school_year": school_year,
            "current_term": current_term_number,
            "total_paid": round(total_paid, 2),
            "previous_balance": previous_balance,
            "current_term_paid": current_term_paid,
            "current_term_balance": current_term_balance,
            "total_due": total_due,
            "status": status
        }

    except Exception as error:

        print(f"\nError getting student fee status: {error}")

        return None

    finally:

        # Always close the database connection.
        connection.close()
        
        


# we will use this function to display the subjects the student takes in student profile
# ----------------------------------------------------------
# GET STUDENT SUBJECTS FROM SQLITE
# ----------------------------------------------------------

def get_student_subjects_db(student_number):

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can run SQL commands.
    cursor = connection.cursor()

    try:

        # Get all subjects registered for this student.
        cursor.execute("""
            SELECT
                subject_name
            FROM student_subjects
            WHERE student_number = ?
            ORDER BY subject_name
        """, (student_number,))

        subjects = cursor.fetchall()

        # Return the subjects.
        return subjects

    except Exception as error:

        print(f"\nError getting student subjects: {error}")

        return []

    finally:

        # Always close the database connection.
        connection.close()




# ----------------------------------------------------------
# GET COMPLETE STUDENT PROFILE FROM SQLITE
# ----------------------------------------------------------

def get_student_profile_db(student_number):

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can run SQL commands.
    cursor = connection.cursor()

    try:

        # --------------------------------------------------
        # GET STUDENT INFORMATION
        # --------------------------------------------------

        # Get the student's personal information.
        #
        # We join the grades table so we can display
        # the grade name instead of only the grade_id.
        cursor.execute("""
            SELECT
                s.student_number,
                s.student_name,
                s.id_number,
                s.nationality,
                s.grade_id,
                g.grade_name,
                s.classroom,
                s.age,
                s.gender
            FROM students s
            JOIN grades g
                ON g.grade_id = s.grade_id
            WHERE s.student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

        # Check whether the student exists.
        if student is None:
            return None

        # --------------------------------------------------
        # GET PARENT / GUARDIAN INFORMATION
        # --------------------------------------------------

        # A student is connected to a guardian through
        # the guardian_students table.
        cursor.execute("""
            SELECT
                gs.relationship,
                g.guardian_id,
                g.first_name,
                g.last_name,
                g.phone_number,
                g.email,
                g.address
            FROM guardian_students gs
            JOIN guardians g
                ON g.guardian_id = gs.guardian_id
            WHERE gs.student_number = ?
        """, (student_number,))

        guardians = cursor.fetchall()
        
        # --------------------------------------------------
        # GET STUDENT SUBJECTS
        # --------------------------------------------------

        # Get the subjects that this student is registered for.
        subjects = get_student_subjects_db(student_number)
        
        homework = get_student_homework_summary_db(student_number)
        
        results = get_student_results_db(student_number)
        
        attendance = get_student_profile_attendance_db(student_number)
        
        timetable = get_student_timetable_db(student_number)
        

        # --------------------------------------------------
        # GET FEE INFORMATION
        # --------------------------------------------------

        # Use the term-aware fee calculation.
        #
        # This gives us:
        # - Annual fee
        # - Term fee
        # - Total paid
        # - Previous balance
        # - Current term balance
        # - Total amount owing
        # - PAID / OWING status
        fee_status = get_student_fee_status_db(student_number)

        # --------------------------------------------------
        # RETURN COMPLETE PROFILE
        # --------------------------------------------------

        return {
            "student": student,
            "guardians": guardians,
            "subjects": subjects,
            "homework": homework,
            "submitted": homework, 
            "results": results,
            "attendance": attendance,
            "timetable": timetable,
            "fee_status": fee_status
        }

    except Exception as error:

        print(f"\nError getting student profile: {error}")

        return None

    finally:

        # Always close the database connection.
        connection.close()



# we will use this function to display the homework sumary the student submited and not submitted in student profile         
# ----------------------------------------------------------
# GET STUDENT HOMEWORK SUMMARY FROM SQLITE
# ----------------------------------------------------------

# ----------------------------------------------------------
# GET STUDENT HOMEWORK SUMMARY
# ----------------------------------------------------------

def get_student_homework_summary_db(student_number):
    """
    Get a summary of homework for a student.

    IMPORTANT:
    A homework submission is considered SUBMITTED when
    a record exists in homework_submissions.

    The teacher's marking status is separate.

    For example:

        submission exists + status = Completed
            -> Submitted

        submission exists + status = Not Completed
            -> Submitted

        no submission record
            -> Not Submitted
    """

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can run SQL commands.
    cursor = connection.cursor()

    try:

        # Find all homework assigned to this student's
        # grade and registered subjects.
        cursor.execute("""
            SELECT

                COUNT(h.homework_id) AS total_assigned,

                -- If a submission record exists,
                -- the student has submitted the homework.
                SUM(
                    CASE
                        WHEN hs.submission_id IS NOT NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS submitted,

                -- If there is no submission record,
                -- the homework has not been submitted.
                SUM(
                    CASE
                        WHEN hs.submission_id IS NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS not_submitted

            FROM homework h

            JOIN students st
                ON st.student_number = ?

            JOIN subjects s
                ON s.subject_id = h.subject_id

            JOIN student_subjects ss
                ON ss.student_number = st.student_number
                AND ss.subject_name = s.subject_name

            LEFT JOIN homework_submissions hs
                ON hs.homework_id = h.homework_id
                AND hs.student_number = st.student_number

            WHERE h.grade_id = st.grade_id

        """, (student_number,))

        # Get the single summary row returned by SQL.
        summary = cursor.fetchone()

        # If nothing was found, return zeros.
        if summary is None:

            return {
                "total_assigned": 0,
                "submitted": 0,
                "not_submitted": 0
            }

        # Return clean numbers instead of None.
        return {
            "total_assigned":
                summary["total_assigned"] or 0,

            "submitted":
                summary["submitted"] or 0,

            "not_submitted":
                summary["not_submitted"] or 0
        }

    except Exception as error:

        print(
            f"\nError getting homework summary: "
            f"{error}"
        )

        return {
            "total_assigned": 0,
            "submitted": 0,
            "not_submitted": 0
        }

    finally:

        # Always close the database connection.
        connection.close()
        
        
        
         
#  we will use this function to display  the student results student profile 
# ----------------------------------------------------------
# GET STUDENT RESULTS FROM SQLITE
# ----------------------------------------------------------

def get_student_results_db(student_number):

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can run SQL commands.
    cursor = connection.cursor()

    try:

        # Get all results belonging to this student.
        cursor.execute("""
            SELECT
                m.mark_id,
                m.mark_value,
                m.total_possible,
                m.exam_date,
                s.subject_name,
                t.teacher_name
            FROM marks m

            JOIN subjects s
                ON s.subject_id = m.subject_id

            JOIN teachers t
                ON t.teacher_number = m.teacher_number

            WHERE m.student_number = ?

            ORDER BY m.exam_date DESC
        """, (student_number,))

        # Get all results returned by the database.
        results = cursor.fetchall()

        # Return the results.
        return results

    except Exception as error:

        print(f"\nError getting student results: {error}")

        return []

    finally:

        # Always close the database connection.
        connection.close()




# ----------------------------------------------------------
# GET STUDENT ATTENDANCE FROM SQLITE
# ----------------------------------------------------------

def get_student_profile_attendance_db(student_number):

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can run SQL commands.
    cursor = connection.cursor()

    try:

        # Get all attendance records for this student.
        cursor.execute("""
            SELECT
                a.attendance_id,
                a.attendance_date,
                a.status,
                s.subject_name,
                t.teacher_name
            FROM attendance a

            JOIN subjects s
                ON s.subject_id = a.subject_id

            JOIN teachers t
                ON t.teacher_number = a.teacher_number

            WHERE a.student_number = ?

            ORDER BY a.attendance_date DESC,
                     a.attendance_id DESC
        """, (student_number,))

        # Get all attendance records.
        attendance = cursor.fetchall()

        # Return the attendance records.
        return attendance

    except Exception as error:

        print(f"\nError getting student attendance: {error}")

        return []

    finally:

        # Always close the database connection.
        connection.close()




# ----------------------------------------------------------
# GET STUDENT TIMETABLE FROM SQLITE FOR STUDENT PROFILE 
# ----------------------------------------------------------

def get_student_timetable_db(student_number):

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can run SQL commands.
    cursor = connection.cursor()

    try:

        # First, get the student's grade and classroom.
        cursor.execute("""
            SELECT
                s.student_number,
                s.grade_id,
                s.classroom,
                g.grade_name
            FROM students s

            JOIN grades g
                ON g.grade_id = s.grade_id

            WHERE s.student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

        # If the student does not exist, return an empty list.
        if student is None:
            return []

        # Get the timetable for the student's
        # grade and classroom.
        cursor.execute("""
            SELECT
                tt.timetable_id,
                g.grade_name,
                tt.classroom,
                tt.day,
                tt.start_time,
                tt.end_time,
                s.subject_name,
                t.teacher_name

            FROM timetable tt

            JOIN grades g
                ON g.grade_id = tt.grade_id

            JOIN subjects s
                ON s.subject_id = tt.subject_id

            JOIN teachers t
                ON t.teacher_number = tt.teacher_number

            WHERE tt.grade_id = ?
            AND tt.classroom = ?

            ORDER BY
                CASE tt.day
                    WHEN 'Monday' THEN 1
                    WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3
                    WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5
                    WHEN 'Saturday' THEN 6
                    WHEN 'Sunday' THEN 7
                    ELSE 8
                END,

                tt.start_time
        """, (
            student["grade_id"],
            student["classroom"]
        ))

        # Get all timetable records.
        timetable = cursor.fetchall()

        # Return the timetable.
        return timetable

    except Exception as error:

        print(f"\nError getting student timetable: {error}")

        return []

    finally:

        # Always close the database connection.
        connection.close()





# ----------------------------------------------------------
# SUBMIT HOMEWORK PDF TO SQLITE
# ----------------------------------------------------------

def submit_homework_pdf_db(
    homework_id,
    student_number,
    file_path
):
    """
    Save a student's PDF homework submission
    in the SQLite database.

    The actual PDF file will be handled separately.
    This function only records the submission details.
    """

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can execute SQL commands.
    cursor = connection.cursor()

    try:

        # Check whether this student has already
        # submitted this homework.
        cursor.execute("""
            SELECT
                submission_id
            FROM homework_submissions
            WHERE homework_id = ?
            AND student_number = ?
        """, (
            homework_id,
            student_number
        ))

        existing_submission = cursor.fetchone()

        # A student can only have one submission
        # for each homework assignment.
        if existing_submission is not None:

            print("\nYou have already submitted this homework.")

            return False

        # Get today's date.
        submission_date = datetime.now().strftime("%Y-%m-%d")

        # Insert the submission into the database.
        cursor.execute("""
            INSERT INTO homework_submissions (
                homework_id,
                student_number,
                submission_text,
                file_path,
                submitted_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            homework_id,
            student_number,
            None,
            file_path,
            submission_date,
            "Submitted"
        ))

        # Save the changes permanently.
        connection.commit()

        print("\nHomework submitted successfully.")

        return True

    except Exception as error:

        # Display the error if something goes wrong.
        print(
            f"\nError submitting homework: {error}"
        )

        # Cancel any unfinished database changes.
        connection.rollback()

        return False

    finally:

        # Always close the database connection.
        connection.close()
        



# ----------------------------------------------------------
# SAVE STUDENT PDF HOMEWORK
# ----------------------------------------------------------

def save_student_homework_pdf(
    homework_id,
    student_number,
    source_file_path,
    homework_title
):
    """
    Validate and copy a student's PDF homework file.

    The PDF is copied into:
        homework_submissions/student_number/

    The database record is then created.
    """

    # Import shutil here because it is used to copy files.
    import shutil

    # Import os so we can work with file paths.
    import os

    # ------------------------------------------------------
    # STEP 1: Check whether the PDF file exists.
    # ------------------------------------------------------

    if not os.path.isfile(source_file_path):

        print("\nError: The PDF file was not found.")

        return False

    # ------------------------------------------------------
    # STEP 2: Check that the file has a PDF extension.
    # ------------------------------------------------------

    if not source_file_path.lower().endswith(".pdf"):

        print("\nError: Only PDF documents are allowed.")

        return False

    # ------------------------------------------------------
    # STEP 3: Create the student's submission folder.
    # ------------------------------------------------------

    student_folder = os.path.join(
        "homework_submissions",
        str(student_number)
    )

    # Create the folder if it does not already exist.
    os.makedirs(
        student_folder,
        exist_ok=True
    )

    # ------------------------------------------------------
    # STEP 4: Create the destination filename.
    # ------------------------------------------------------

    # Remove characters that could cause problems
    # in a filename.
    safe_title = "".join(
        character if character.isalnum() or character in " -_"
        else "_"
        for character in homework_title
    ).strip()

    destination_file = os.path.join(
        student_folder,
        f"{homework_id}_{safe_title}.pdf"
    )

    # ------------------------------------------------------
    # STEP 5: Copy the PDF into the school folder.
    # ------------------------------------------------------

    try:

        shutil.copy2(
            source_file_path,
            destination_file
        )

    except Exception as error:

        print(
            f"\nError copying PDF file: {error}"
        )

        return False

    # ------------------------------------------------------
    # STEP 6: Save the submission in SQLite.
    # ------------------------------------------------------

    database_saved = submit_homework_pdf_db(
        homework_id,
        student_number,
        destination_file
    )

    # ------------------------------------------------------
    # STEP 7: If the database rejected the submission,
    # remove the copied PDF so we don't leave an
    # unregistered file behind.
    # ------------------------------------------------------

    if not database_saved:

        try:

            os.remove(destination_file)

        except Exception:

            pass

        return False

    # ------------------------------------------------------
    # STEP 8: Everything succeeded.
    # ------------------------------------------------------

    print(
        f"\nPDF saved successfully:"
        f"\n{destination_file}"
    )

    return True





# ----------------------------------------------------------
# GET HOMEWORK AVAILABLE FOR STUDENT SUBMISSION
# ----------------------------------------------------------

def get_student_homework_for_submission_db(student_number):
    """
    Get homework assigned to the student's grade and
    registered subjects.

    The function also checks whether the student has
    already submitted each homework.
    """

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can execute SQL commands.
    cursor = connection.cursor()

    try:

        # Find homework assigned to this student's grade
        # and registered subjects.
        cursor.execute("""
            SELECT
                h.homework_id,
                h.title,
                h.description,
                h.due_date,
                s.subject_name,
                t.teacher_name,

                hs.submission_id,
                hs.file_path,
                hs.submitted_date,
                hs.status,
                hs.mark,
                hs.total_possible,
                hs.marked_date

            FROM homework h

            JOIN students st
                ON st.student_number = ?

            JOIN subjects s
                ON s.subject_id = h.subject_id

            JOIN student_subjects ss
                ON ss.student_number = st.student_number
                AND ss.subject_name = s.subject_name

            JOIN teachers t
                ON t.teacher_number = h.teacher_number

            LEFT JOIN homework_submissions hs
                ON hs.homework_id = h.homework_id
                AND hs.student_number = st.student_number

            WHERE h.grade_id = st.grade_id

            ORDER BY h.due_date ASC,
                     h.homework_id ASC
        """, (student_number,))

        homework = cursor.fetchall()

        return homework

    except Exception as error:

        print(
            f"\nError getting homework for submission: "
            f"{error}"
        )

        return []

    finally:

        # Always close the database connection.
        connection.close()




# ----------------------------------------------------------
# GET HOMEWORK SUBMISSIONS FOR TEACHER
# ----------------------------------------------------------

def get_teacher_homework_submissions_db(teacher_number):
    """
    Get homework submissions belonging to this teacher.

    We show:
    - Homework title
    - Subject
    - Student
    - Student number
    - Submission date
    - Submission status
    - Homework mark
    - Total possible mark
    - PDF file location
    - Marked date
    """

    # Open the school database.
    connection = get_connection()

    # Create a cursor so we can execute SQL commands.
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                hs.submission_id,
                hs.homework_id,
                hs.student_number,
                st.student_name,
                h.title,
                s.subject_name,
                hs.file_path,
                hs.submitted_date,
                hs.status,
                hs.mark,
                hs.total_possible,
                hs.marked_date

            FROM homework_submissions hs

            JOIN homework h
                ON hs.homework_id = h.homework_id

            JOIN students st
                ON hs.student_number = st.student_number

            JOIN subjects s
                ON h.subject_id = s.subject_id

            WHERE h.teacher_number = ?

            ORDER BY hs.submitted_date DESC,
                     hs.submission_id DESC

        """, (teacher_number,))

        # Get all matching submissions.
        submissions = cursor.fetchall()

        return submissions

    except Exception as error:

        print(
            f"\nError getting homework submissions: "
            f"{error}"
        )

        return []

    finally:

        # Always close the database connection.
        connection.close()




# ----------------------------------------------------------
# OPEN HOMEWORK PDF TEACHER SIDE
# ----------------------------------------------------------

def open_homework_pdf(file_path):
    """
    Open a student's homework PDF using Android's
    default PDF application.

    Termux provides the 'termux-open' command,
    which allows Python to ask Android to open a file.
    """

    import os

    # Check that the PDF actually exists before
    # trying to open it.
    if not os.path.isfile(file_path):

        print("\nError: PDF file not found.")

        return False

    # Make sure that only PDF files are opened.
    if not file_path.lower().endswith(".pdf"):

        print("\nError: This is not a PDF file.")

        return False

    try:

        # Ask Android to open the PDF using the
        # default application associated with PDF files.
        result = os.system(
            f'termux-open "{file_path}"'
        )

        if result != 0:

            print(
                "\nCould not open the PDF."
            )

            return False

        print(
            "\nOpening PDF..."
        )

        return True

    except Exception as error:

        print(
            f"\nError opening PDF: {error}"
        )

        return False



# ----------------------------------------------------------
# MARK HOMEWORK SUBMISSION
# ----------------------------------------------------------

def mark_homework_submission_db(
    submission_id,
    teacher_number,
    mark,
    total_possible,
    status
):
    """
    Mark a student's homework submission.

    The teacher can save:
    - Mark obtained
    - Total possible mark
    - Completion status
    - Teacher who marked it
    - Date it was marked
    """

    # Open a connection to the SQLite database.
    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ------------------------------------------------------
        # Check that the submission exists.
        # ------------------------------------------------------

        cursor.execute("""
            SELECT submission_id
            FROM homework_submissions
            WHERE submission_id = ?
        """, (submission_id,))

        submission = cursor.fetchone()

        if submission is None:
            print("\nHomework submission not found.")
            return False

        # ------------------------------------------------------
        # Get today's date.
        # ------------------------------------------------------

        marked_date = datetime.now().strftime("%Y-%m-%d")

        # ------------------------------------------------------
        # Update the homework submission.
        #
        # We save:
        # mark
        # total_possible
        # status
        # marked_date
        # teacher_number
        # ------------------------------------------------------

        cursor.execute("""
            UPDATE homework_submissions
            SET
                mark = ?,
                total_possible = ?,
                status = ?,
                marked_date = ?,
                teacher_number = ?
            WHERE submission_id = ?
        """, (
            mark,
            total_possible,
            status,
            marked_date,
            teacher_number,
            submission_id
        ))

        # Save the changes permanently.
        connection.commit()

        print("\nHomework marked successfully.")

        return True

    except Exception as error:

        print(
            f"\nError marking homework: {error}"
        )

        # Undo any incomplete database changes.
        connection.rollback()

        return False

    finally:

        # Always close the database connection.
        connection.close()




# ----------------------------------------------------------
# SELECT PDF FROM ANDROID PHONE
# ----------------------------------------------------------

def select_pdf_from_android():
    """
    Open the Android file picker and allow the student
    to select a PDF homework file.

    A temporary filename is used for every selection.
    """

    import os
    import subprocess
    import time

    # Use the absolute Android storage path.
    # This makes sure Python checks the same location
    # where Termux:API creates the selected PDF.
    selected_pdf = (
        "/storage/emulated/0/"
        "PythonLessons/DataBasseLessons/"
        "SchoolSystemDatabase/SchoolProject/"
        "selected_homework.pdf"
)

    print("\nOpening Android file picker...")
    print("Please select your homework PDF.")

    try:

        # Run Termux:API's Android file picker.
        result = subprocess.run(
            [
                "termux-storage-get",
                selected_pdf
            ]
        )

        # Check the command result.
        if result.returncode != 0:

            print(
                "\nPDF selection was cancelled."
            )

            return None

        # Check whether Android created the file.
        if not os.path.isfile(selected_pdf):

            print(
                "\nPDF file was not created."
            )

            return None

        # Check that the file is not empty.
        file_size = os.path.getsize(selected_pdf)

        if file_size == 0:

            print(
                "\nThe selected PDF is empty."
            )

            os.remove(selected_pdf)

            return None

        print(
            "\nPDF selected successfully."
        )

        print(
            f"Temporary file: "
            f"{selected_pdf}"
        )

        return selected_pdf

    except Exception as error:

        print(
            f"\nError selecting PDF: "
            f"{error}"
        )

        return None


                 
def set_school_term_dates_db(school_year, term_number, start_date, end_date):
    """
    Save or update the start and end dates for a school term.

    If the term already exists for the selected school year,
    the existing dates will be updated.

    If the term does not exist yet, a new term record will
    be created.
    """

    # Open the database connection.
    connection = get_connection()

    # Create a cursor so we can execute SQL commands.
    cursor = connection.cursor()

    try:

        # ------------------------------------------------------
        # CHECK WHETHER THIS TERM ALREADY EXISTS
        # ------------------------------------------------------

        cursor.execute("""
            SELECT term_id
            FROM school_terms
            WHERE school_year = ?
              AND term_number = ?
        """, (
            school_year,
            term_number
        ))

        existing_term = cursor.fetchone()

        # ------------------------------------------------------
        # UPDATE EXISTING TERM
        # ------------------------------------------------------

        if existing_term:

            cursor.execute("""
                UPDATE school_terms
                SET
                    start_date = ?,
                    end_date = ?
                WHERE term_id = ?
            """, (
                start_date,
                end_date,
                existing_term["term_id"]
            ))

            print(
                f"\nTerm {term_number} dates updated successfully."
            )

        # ------------------------------------------------------
        # CREATE NEW TERM
        # ------------------------------------------------------

        else:

            # We need a required_amount because your
            # school_terms table requires this column.
            #
            # We will temporarily set it to 0.
            # The existing fee-management system can update
            # the amount separately.
            cursor.execute("""
                INSERT INTO school_terms (
                    school_year,
                    term_number,
                    start_date,
                    end_date,
                    required_amount
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                school_year,
                term_number,
                start_date,
                end_date,
                0
            ))

            print(
                f"\nTerm {term_number} dates saved successfully."
            )

        # Save the changes.
        connection.commit()

        return True

    except Exception as error:

        # If something goes wrong, undo the database changes.
        connection.rollback()

        print(
            f"\nError saving term dates: {error}"
        )

        return False

    finally:

        # Always close the database connection.
        connection.close()



def get_fees_structure_db():
    """
    Get the fee structure for all grades from the SQLite database.

    We join fees_structure with grades so that we can display
    the actual grade name instead of only the grade_id.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            fs.fees_id,
            fs.grade_id,
            g.grade_name,
            fs.amount
        FROM fees_structure fs

        JOIN grades g
            ON g.grade_id = fs.grade_id

        ORDER BY fs.grade_id
    """)

    fees = cursor.fetchall()

    connection.close()

    return fees
    
    
    


def update_grade_fee_db(grade_name, new_fee):
    """
    Update the fee amount for a specific grade.

    Example:
        Grade 12 -> R5000
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # First find the grade_id using the grade name.
        cursor.execute("""
            SELECT grade_id, grade_name
            FROM grades
            WHERE grade_name = ?
        """, (grade_name,))

        grade = cursor.fetchone()

        if grade is None:
            print("\nGrade not found.")
            return False

        # Check whether this grade already has a fee structure.
        cursor.execute("""
            SELECT fees_id, amount
            FROM fees_structure
            WHERE grade_id = ?
        """, (grade["grade_id"],))

        existing_fee = cursor.fetchone()

        if existing_fee:
            # Update the existing fee.
            cursor.execute("""
                UPDATE fees_structure
                SET amount = ?
                WHERE grade_id = ?
            """, (new_fee, grade["grade_id"]))

            print(
                f"\nGrade {grade['grade_name']} fee "
                f"updated successfully."
            )

        else:
            # If the grade does not have a fee yet,
            # create a new fee record for it.
            cursor.execute("""
                INSERT INTO fees_structure (
                    grade_id,
                    amount
                )
                VALUES (?, ?)
            """, (grade["grade_id"], new_fee))

            print(
                f"\nFee structure created for "
                f"Grade {grade['grade_name']}."
            )

        connection.commit()
        return True

    except Exception as error:
        connection.rollback()

        print(f"\nError updating fee structure: {error}")

        return False

    finally:
        connection.close()




def get_school_fee_report_db(grade_name=None):
    """
    Create a fee report for either:

    1. The whole school, when grade_name is None.
    2. One specific grade, when grade_name is provided.

    The function calculates:
    - Total students
    - Students who have paid
    - Students owing
    - Total fee expected
    - Total paid
    - Total outstanding

    It also calculates the individual balance for every student.
    """

    # ---------------------------------------------------------
    # STEP 1: Find the current school term.
    # ---------------------------------------------------------

    current_term = get_current_school_term_db()

    if current_term is None:
        return None

    school_year = current_term["school_year"]
    term_number = current_term["term_number"]

    # ---------------------------------------------------------
    # STEP 2: Open the database.
    # ---------------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # -----------------------------------------------------
        # STEP 3: Get the students.
        #
        # If a grade was supplied, only get students
        # belonging to that grade.
        # -----------------------------------------------------

        if grade_name:

            cursor.execute("""
                SELECT
                    s.student_number,
                    s.student_name,
                    g.grade_name,
                    s.classroom
                FROM students s
                JOIN grades g
                    ON g.grade_id = s.grade_id
                WHERE g.grade_name = ?
                ORDER BY s.student_name
            """, (grade_name,))

        else:

            cursor.execute("""
                SELECT
                    s.student_number,
                    s.student_name,
                    g.grade_name,
                    s.classroom
                FROM students s
                JOIN grades g
                    ON g.grade_id = s.grade_id
                ORDER BY g.grade_name, s.student_name
            """)

        students = cursor.fetchall()

    finally:
        connection.close()

    # ---------------------------------------------------------
    # STEP 4: Prepare totals.
    # ---------------------------------------------------------

    total_students = len(students)

    students_who_paid = 0
    students_owing = 0

    total_fee_expected = 0
    total_paid = 0
    total_outstanding = 0

    student_details = []

    # ---------------------------------------------------------
    # STEP 5: Calculate the fee information for every student.
    #
    # We use the SAME fee calculation function already used
    # by the student's fee statement.
    # ---------------------------------------------------------

    for student in students:

        try:

            fee = get_student_total_fee_due_db(
                student["student_number"],
                school_year,
                term_number
            )

        except ValueError:
            continue

        # Annual fee for this student's grade.
        annual_fee = fee["annual_fee"]

        # Total amount paid during the current school year.
        current_term_paid = fee["current_term_paid"]

        # Previous balances that were paid using current-term
        # payments are already accounted for by the fee function.
        #
        # We therefore calculate the total amount paid in the
        # school year directly from fee_payments.
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                COALESCE(SUM(amount), 0) AS total_paid
            FROM fee_payments
            WHERE student_number = ?
            AND school_year = ?
        """, (
            student["student_number"],
            school_year
        ))

        payment_row = cursor.fetchone()
        student_total_paid = payment_row["total_paid"]

        connection.close()

        # The student's final outstanding balance.
        balance = fee["remaining_balance"]

        # -----------------------------------------------------
        # Count students who have made at least one payment.
        # -----------------------------------------------------

        if student_total_paid > 0:
            students_who_paid += 1

        # -----------------------------------------------------
        # Count students who still owe money.
        # -----------------------------------------------------

        if balance > 0:
            students_owing += 1

        # -----------------------------------------------------
        # Add the student's annual fee to the expected total.
        # -----------------------------------------------------

        total_fee_expected += annual_fee

        # -----------------------------------------------------
        # Add their payments to the school-wide total.
        # -----------------------------------------------------

        total_paid += student_total_paid

        # -----------------------------------------------------
        # Add their outstanding balance.
        # -----------------------------------------------------

        total_outstanding += balance

        # -----------------------------------------------------
        # Save the student's information.
        # -----------------------------------------------------

        student_details.append({
            "student_number": student["student_number"],
            "student_name": student["student_name"],
            "grade_name": student["grade_name"],
            "classroom": student["classroom"],
            "annual_fee": annual_fee,
            "total_paid": student_total_paid,
            "balance": balance
        })

    # ---------------------------------------------------------
    # STEP 6: Return the complete report.
    # ---------------------------------------------------------

    return {
        "school_year": school_year,
        "current_term": term_number,

        "total_students": total_students,
        "students_who_paid": students_who_paid,
        "students_owing": students_owing,

        "total_fee_expected": total_fee_expected,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,

        "students": student_details
    }




def get_grade_term_fee_report_db(
    grade_name,
    school_year,
    term_number
):
    """
    Create a fee report for one grade and one selected term.

    IMPORTANT:
    Payments are allocated in the same order as the student's
    normal Fees Statement:

    1. Each term has an annual_fee / 4 fee.
    2. Unpaid balances from earlier terms are carried forward.
    3. When a student pays during the selected term, the payment
       first clears previous outstanding balances.
    4. Any money left after clearing previous balances is used
       to pay the selected term.
    5. The remaining amount is the actual outstanding amount
       for the selected term.

    Example for Nifah:

        Previous balance = R13,500
        Term 3 payments  = R15,100

        R13,500 clears previous terms
        R1,600 remains for Term 3

        Term 3 fee = R12,500
        Term 3 outstanding = R10,900
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # ---------------------------------------------------------
        # Get all students belonging to the selected grade.
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                s.student_number,
                s.student_name,
                g.grade_name,
                s.classroom,
                f.amount AS annual_fee
            FROM students s
            JOIN grades g
                ON g.grade_id = s.grade_id
            JOIN fees_structure f
                ON f.grade_id = s.grade_id
            WHERE g.grade_name = ?
            ORDER BY s.student_name
        """, (grade_name,))

        students = cursor.fetchall()

        total_students = len(students)

        students_paid = 0
        students_owing = 0

        total_fee_expected = 0
        total_paid = 0
        total_outstanding = 0

        student_details = []

        # ---------------------------------------------------------
        # Process each student separately.
        # ---------------------------------------------------------
        for student in students:

            student_number = student["student_number"]
            annual_fee = float(student["annual_fee"])

            # Every annual fee is divided into four terms.
            term_fee = annual_fee / 4

            # -----------------------------------------------------
            # Calculate the unpaid balance from all terms BEFORE
            # the selected term.
            #
            # Example:
            # Term 1 owes R1,000
            # Term 2 owes R12,500
            # Previous balance = R13,500
            # -----------------------------------------------------
            previous_balance = 0

            for previous_term in range(1, term_number):

                cursor.execute("""
                    SELECT
                        COALESCE(SUM(amount), 0) AS amount_paid
                    FROM fee_payments
                    WHERE student_number = ?
                      AND school_year = ?
                      AND term_number = ?
                """, (
                    student_number,
                    school_year,
                    previous_term
                ))

                payment_row = cursor.fetchone()

                amount_paid_previous = float(
                    payment_row["amount_paid"]
                )

                # Calculate this term's unpaid amount.
                term_balance = term_fee - amount_paid_previous

                if term_balance > 0:
                    previous_balance += term_balance

            # -----------------------------------------------------
            # Get ALL payments made during the selected term.
            # -----------------------------------------------------
            cursor.execute("""
                SELECT
                    COALESCE(SUM(amount), 0) AS amount_paid
                FROM fee_payments
                WHERE student_number = ?
                  AND school_year = ?
                  AND term_number = ?
            """, (
                student_number,
                school_year,
                term_number
            ))

            payment_row = cursor.fetchone()

            current_term_paid = float(
                payment_row["amount_paid"]
            )

            # -----------------------------------------------------
            # First use the selected-term payments to clear any
            # previous outstanding balance.
            # -----------------------------------------------------
            payment_used_for_previous = min(
                current_term_paid,
                previous_balance
            )

            previous_balance_left = (
                previous_balance
                - payment_used_for_previous
            )

            # -----------------------------------------------------
            # Whatever remains from the selected-term payment
            # can now be used toward the selected term's fee.
            # -----------------------------------------------------
            payment_left_for_current = (
                current_term_paid
                - payment_used_for_previous
            )

            current_term_paid_applied = min(
                payment_left_for_current,
                term_fee
            )

            # -----------------------------------------------------
            # Calculate the actual outstanding amount for the
            # selected term.
            # -----------------------------------------------------
            current_term_balance = (
                term_fee
                - current_term_paid_applied
            )

            if current_term_balance < 0:
                current_term_balance = 0

            # -----------------------------------------------------
            # A student counts as "paid" for this selected term
            # if some money was actually applied to the selected
            # term.
            # -----------------------------------------------------
            if current_term_paid_applied > 0:
                students_paid += 1

            if current_term_balance > 0:
                students_owing += 1

            # -----------------------------------------------------
            # Add this student's figures to the grade totals.
            #
            # IMPORTANT:
            # total_paid here means money APPLIED TO THE SELECTED
            # TERM, not all money physically received during that
            # term.
            # -----------------------------------------------------
            total_fee_expected += term_fee
            total_paid += current_term_paid_applied
            total_outstanding += current_term_balance

            student_details.append({
                "student_number": student_number,
                "student_name": student["student_name"],
                "grade_name": student["grade_name"],
                "classroom": student["classroom"],

                "term_fee": term_fee,

                # Total cash paid during this selected term.
                "amount_paid": current_term_paid,

                # Amount of that payment actually applied to
                # the selected term after previous balances
                # were cleared.
                "amount_applied_to_term":
                    current_term_paid_applied,

                # Amount used to clear previous terms.
                "payment_used_for_previous":
                    payment_used_for_previous,

                "previous_balance":
                    previous_balance,

                "previous_balance_left":
                    previous_balance_left,

                "balance":
                    current_term_balance
            })

        return {
            "school_year": school_year,
            "term_number": term_number,
            "grade_name": grade_name,

            "total_students": total_students,
            "students_paid": students_paid,
            "students_owing": students_owing,

            "total_fee_expected":
                total_fee_expected,

            # This is the amount actually applied to
            # the selected term.
            "total_paid":
                total_paid,

            "total_outstanding":
                total_outstanding,

            "students":
                student_details
        }

    finally:
        connection.close()





def get_all_students_db():
    """
    Get all students from the database.

    We join the students table with the grades table so that
    the report shows the actual grade name instead of only
    the grade_id.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                s.student_number,
                s.student_name,
                g.grade_name,
                s.classroom,
                s.nationality,
                s.id_number
            FROM students s
            LEFT JOIN grades g
                ON g.grade_id = s.grade_id
            ORDER BY s.student_number
        """)

        return cursor.fetchall()

    finally:
        connection.close()




def get_all_teachers_db():
    """
    Get all teachers from the database.

    A teacher can teach multiple subjects and/or grades.

    The teachers table stores the teacher's personal information.

    The teacher_subjects table stores:
        - teacher_number
        - subject_name
        - grade_name

    Therefore, we collect the teacher's subjects separately
    and combine them into one record for display.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # ---------------------------------------------------------
        # Get the basic information about every teacher.
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                teacher_number,
                teacher_name,
                id_number,
                gender,
                nationality,
                email_address,
                status
            FROM teachers
            ORDER BY teacher_number
        """)

        teachers = cursor.fetchall()

        teacher_details = []

        # ---------------------------------------------------------
        # Get subjects and grades for each teacher.
        # ---------------------------------------------------------
        for teacher in teachers:

            cursor.execute("""
                SELECT
                    subject_name,
                    grade_name
                FROM teacher_subjects
                WHERE teacher_number = ?
                ORDER BY grade_name, subject_name
            """, (
                teacher["teacher_number"],
            ))

            assignments = cursor.fetchall()

            # -----------------------------------------------------
            # Convert the teacher's subject/grade assignments
            # into a simple list for phase16.py to display.
            # -----------------------------------------------------
            subjects_and_grades = []

            for assignment in assignments:

                subjects_and_grades.append({
                    "subject_name":
                        assignment["subject_name"],

                    "grade_name":
                        assignment["grade_name"]
                })

            teacher_details.append({
                "teacher_number":
                    teacher["teacher_number"],

                "teacher_name":
                    teacher["teacher_name"],

                "id_number":
                    teacher["id_number"],

                "gender":
                    teacher["gender"],

                "nationality":
                    teacher["nationality"],

                "email_address":
                    teacher["email_address"],

                "status":
                    teacher["status"],

                "subjects_and_grades":
                    subjects_and_grades
            })

        return teacher_details

    finally:
        connection.close()





def get_students_by_grade_db(grade_name):
    """
    Get all students belonging to one specific grade.

    The students table stores grade_id, so we join it with
    the grades table to find the actual grade name.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                s.student_number,
                s.student_name,
                s.id_number,
                s.nationality,
                s.gender,
                s.age,
                s.classroom,
                s.fees_balance,
                g.grade_name
            FROM students s
            JOIN grades g
                ON g.grade_id = s.grade_id
            WHERE g.grade_name = ?
            ORDER BY s.student_number
        """, (grade_name,))

        return cursor.fetchall()

    finally:
        connection.close()





def get_results_by_grade_db(grade_name, subject_name):
    """
    Get student results for one specific grade and subject.

    The marks table stores:
        - student_number
        - subject_id
        - mark_value
        - total_possible
        - exam_date

    We use JOINs to connect:
        marks -> students -> grades
        marks -> subjects

    This means the results come directly from SQLite
    instead of the old in-memory students dictionary.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                s.student_number,
                s.student_name,
                g.grade_name,
                sub.subject_name,
                m.mark_value,
                m.total_possible,
                m.exam_date
            FROM marks m

            JOIN students s
                ON s.student_number = m.student_number

            JOIN grades g
                ON g.grade_id = s.grade_id

            JOIN subjects sub
                ON sub.subject_id = m.subject_id

            WHERE g.grade_name = ?
              AND sub.subject_name = ?

            ORDER BY s.student_number, m.exam_date
        """, (
            grade_name,
            subject_name
        ))

        return cursor.fetchall()

    finally:
        connection.close()




def get_school_statistics_db():
    """
    Get general school statistics directly from SQLite.

    This function collects statistics for:
        - Students
        - Teachers
        - Grades
        - Marks / academic results
        - Attendance
        - Homework
        - Homework submissions
        - Fees

    All information comes directly from the database.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # ============================================================
        # 1. TOTAL STUDENTS
        # ============================================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM students
        """)

        total_students = cursor.fetchone()[0]


        # ============================================================
        # 2. TOTAL TEACHERS
        # ============================================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM teachers
        """)

        total_teachers = cursor.fetchone()[0]


        # ============================================================
        # 3. TOTAL GRADES
        # ============================================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM grades
        """)

        total_grades = cursor.fetchone()[0]


        # ============================================================
        # 4. STUDENTS BY GRADE
        # ============================================================

        cursor.execute("""
            SELECT
                g.grade_name,
                COUNT(s.student_number) AS student_count
            FROM grades g
            LEFT JOIN students s
                ON s.grade_id = g.grade_id
            GROUP BY g.grade_id, g.grade_name
            ORDER BY g.grade_id
        """)

        students_by_grade = cursor.fetchall()


        # ============================================================
        # 5. ACADEMIC / MARK STATISTICS
        # ============================================================

        cursor.execute("""
            SELECT
                COUNT(*) AS total_marks,

                AVG(
                    CASE
                        WHEN total_possible > 0
                        THEN (mark_value * 100.0) / total_possible
                    END
                ) AS average_percentage,

                MAX(
                    CASE
                        WHEN total_possible > 0
                        THEN (mark_value * 100.0) / total_possible
                    END
                ) AS highest_percentage,

                MIN(
                    CASE
                        WHEN total_possible > 0
                        THEN (mark_value * 100.0) / total_possible
                    END
                ) AS lowest_percentage

            FROM marks
        """)

        academic = cursor.fetchone()


        # ============================================================
        # 6. ATTENDANCE STATISTICS
        # ============================================================

        cursor.execute("""
            SELECT
                COUNT(*) AS total_attendance,

                SUM(
                    CASE
                        WHEN LOWER(status) = 'present'
                        THEN 1
                        ELSE 0
                    END
                ) AS present_count,

                SUM(
                    CASE
                        WHEN LOWER(status) = 'absent'
                        THEN 1
                        ELSE 0
                    END
                ) AS absent_count

            FROM attendance
        """)

        attendance = cursor.fetchone()

        total_attendance = attendance["total_attendance"]
        present_count = attendance["present_count"] or 0
        absent_count = attendance["absent_count"] or 0

        if total_attendance > 0:
            attendance_percentage = (
                present_count / total_attendance
            ) * 100
        else:
            attendance_percentage = 0


        # ============================================================
        # 7. HOMEWORK STATISTICS
        # ============================================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM homework
        """)

        total_homework = cursor.fetchone()[0]


        # ============================================================
        # 8. HOMEWORK SUBMISSIONS
        # ============================================================

        cursor.execute("""
            SELECT
                COUNT(*) AS total_submissions,

                SUM(
                    CASE
                        WHEN LOWER(status) = 'completed'
                          OR LOWER(status) = 'complete'
                        THEN 1
                        ELSE 0
                    END
                ) AS completed_count,

                SUM(
                    CASE
                        WHEN LOWER(status) = 'not completed'
                          OR LOWER(status) = 'not_completed'
                        THEN 1
                        ELSE 0
                    END
                ) AS not_completed_count,

                AVG(
                    CASE
                        WHEN total_possible > 0
                        THEN (mark * 100.0) / total_possible
                    END
                ) AS average_homework_percentage

            FROM homework_submissions
        """)

        homework = cursor.fetchone()

        total_submissions = homework["total_submissions"]
        completed_count = homework["completed_count"] or 0
        not_completed_count = homework["not_completed_count"] or 0
        average_homework_percentage = (
            homework["average_homework_percentage"] or 0
        )


        # ============================================================
        # 9. FEE PAYMENT STATISTICS
        # ============================================================

        cursor.execute("""
            SELECT
                COALESCE(SUM(amount), 0)
                FROM fee_payments
        """)

        total_fees_paid = cursor.fetchone()[0]


        # ============================================================
        # 10. RETURN EVERYTHING IN ONE DICTIONARY
        # ============================================================

        return {
            "total_students": total_students,
            "total_teachers": total_teachers,
            "total_grades": total_grades,

            "students_by_grade": students_by_grade,

            "total_marks": academic["total_marks"],
            "average_percentage": academic["average_percentage"] or 0,
            "highest_percentage": academic["highest_percentage"] or 0,
            "lowest_percentage": academic["lowest_percentage"] or 0,

            "total_attendance": total_attendance,
            "present_count": present_count,
            "absent_count": absent_count,
            "attendance_percentage": attendance_percentage,

            "total_homework": total_homework,
            "total_submissions": total_submissions,
            "completed_count": completed_count,
            "not_completed_count": not_completed_count,
            "average_homework_percentage":
                average_homework_percentage,

            "total_fees_paid": total_fees_paid
        }

    finally:
        connection.close()



def get_admin_logs_db():
    """
    Get all administrator audit logs directly from SQLite.

    The admin_logs table records important actions performed
    by administrators.

    We return the newest actions first so the most recent
    activity appears at the top of the audit log.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                log_id,
                admin_name,
                category,
                action,
                teacher_number,
                student_number,
                admin_id,
                action_time
            FROM admin_logs
            ORDER BY action_time DESC, log_id DESC
        """)

        return cursor.fetchall()

    finally:
        connection.close()





def change_admin_password_db(admin_id, current_password, new_password):
    """
    Change an administrator's password.

    Steps:
        1. Find the administrator in SQLite.
        2. Verify the current password using the existing
           password_hash + password_salt system.
        3. Generate a new random salt.
        4. Hash the new password with the new salt.
        5. Save the new hash and salt in SQLite.

    The existing password system is preserved, so existing
    administrator accounts continue using the same format.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # ============================================================
        # 1. GET THE ADMINISTRATOR
        # ============================================================

        cursor.execute("""
            SELECT
                admin_id,
                password_hash,
                password_salt,
                status
            FROM admins
            WHERE admin_id = ?
        """, (admin_id,))

        admin = cursor.fetchone()

        if admin is None:
            return False, "Administrator account not found."

        # Do not allow a disabled/inactive account to change
        # its password.
        if admin["status"] != "Active":
            return False, "Administrator account is not active."


        # ============================================================
        # 2. VERIFY THE CURRENT PASSWORD
        # ============================================================

        salt = bytes.fromhex(admin["password_salt"])

        current_hash = hashlib.sha256(
            current_password.encode() + salt
        ).hexdigest()

        if current_hash != admin["password_hash"]:
            return False, "Current password is incorrect."


        # ============================================================
        # 3. VALIDATE THE NEW PASSWORD
        # ============================================================

        if not new_password:
            return False, "New password cannot be empty."

        if len(new_password) < 8:
            return False, "New password must be at least 8 characters."

        if new_password == current_password:
            return False, "New password must be different from the current password."


        # ============================================================
        # 4. GENERATE A NEW SALT
        # ============================================================

        new_salt = os.urandom(16)

        # Convert the salt to hexadecimal so it can be stored
        # in the TEXT password_salt column.
        new_salt_hex = new_salt.hex()


        # ============================================================
        # 5. CREATE THE NEW PASSWORD HASH
        # ============================================================

        new_hash = hashlib.sha256(
            new_password.encode() + new_salt
        ).hexdigest()


        # ============================================================
        # 6. SAVE THE NEW PASSWORD
        # ============================================================

        cursor.execute("""
            UPDATE admins
            SET
                password_hash = ?,
                password_salt = ?,
                failed_attempts = 0
            WHERE admin_id = ?
        """, (
            new_hash,
            new_salt_hex,
            admin_id
        ))

        connection.commit()

        return True, "Password changed successfully."

    except ValueError:
        # Handles a corrupted/invalid stored salt.
        return False, "Stored password information is invalid."

    finally:
        connection.close()



def record_student_fee_payment_db(student_number, amount_paid):
    """
    Record a fee payment made by a student in the school office.

    The payment is saved in the fee_payments table.

    IMPORTANT:
    We do NOT manually subtract the payment from
    students.fees_balance.

    The fee system calculates the student's balance from
    the payment history, including payments that clear
    previous-term balances first.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # ============================================================
        # 1. FIND THE STUDENT
        # ============================================================

        cursor.execute("""
            SELECT
                s.student_number,
                s.student_name,
                s.id_number,
                g.grade_name
            FROM students s
            LEFT JOIN grades g
                ON g.grade_id = s.grade_id
            WHERE s.student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

        if student is None:
            return False, "Student not found.", None

        # ============================================================
        # 2. CHECK THE PAYMENT AMOUNT
        # ============================================================

        if amount_paid <= 0:
            return False, "Amount must be greater than zero.", None

        # ============================================================
        # 3. FIND THE CURRENT SCHOOL TERM
        # ============================================================

        # We use the existing school-term function so that the
        # payment is automatically recorded for the active term.

        current_school_term = get_current_school_term_db()

        if current_school_term is None:
            return False, "No active school term found.", None

        school_year = current_school_term["school_year"]
        current_term = current_school_term["term_number"]

        # ============================================================
        # 4. GET THE STUDENT'S CURRENT OUTSTANDING BALANCE
        # ============================================================

        # IMPORTANT:
        # get_student_total_fee_due_db() requires:
        #
        #   student_number
        #   school_year
        #   current_term
        #
        # The previous version only supplied student_number,
        # which caused the TypeError.

        fee_status = get_student_total_fee_due_db(
            student_number,
            school_year,
            current_term
        )

        if fee_status is None:
            return (
                False,
                "Could not calculate the student's balance.",
                None
            )

        # The function returns the actual remaining balance
        # using the complete fee allocation system.
        current_balance = fee_status["remaining_balance"]

        # ============================================================
        # 5. MAKE SURE THE PAYMENT DOES NOT EXCEED THE BALANCE
        # ============================================================

        if amount_paid > current_balance:
            return (
                False,
                "Amount paid cannot be greater than the "
                "outstanding balance.",
                current_balance
            )

        # ============================================================
        # 6. RECORD THE PAYMENT
        # ============================================================

        cursor.execute("""
            INSERT INTO fee_payments (
                student_number,
                amount,
                payment_date,
                term_number,
                school_year
            )
            VALUES (?, ?, date('now'), ?, ?)
        """, (
            student_number,
            amount_paid,
            current_term,
            school_year
        ))

        # Save the payment permanently.
        connection.commit()

        # ============================================================
        # 7. CALCULATE THE NEW BALANCE
        # ============================================================

        # Calculate the balance again AFTER the payment has been
        # saved. This gives us the student's new actual balance.

        updated_fee_status = get_student_total_fee_due_db(
            student_number,
            school_year,
            current_term
        )

        if updated_fee_status is None:
            return (
                False,
                "Payment was recorded, but the new balance "
                "could not be calculated.",
                None
            )

        new_balance = updated_fee_status["remaining_balance"]

        # ============================================================
        # 8. PREPARE PAYMENT INFORMATION FOR THE RECEIPT
        # ============================================================

        payment_information = {
            "student_number": student["student_number"],
            "student_name": student["student_name"],
            "id_number": student["id_number"],
            "grade_name": student["grade_name"],

            # Balance BEFORE this payment
            "previous_balance": current_balance,

            # Amount just paid
            "amount_paid": amount_paid,

            # Balance AFTER this payment
            "new_balance": new_balance,

            # Term in which the payment was recorded
            "school_year": school_year,
            "term_number": current_term
        }

        # ============================================================
        # 9. RETURN SUCCESS
        # ============================================================

        return (
            True,
            "Payment recorded successfully.",
            payment_information
        )

    except Exception as e:
        # If something goes wrong, undo any unfinished database
        # transaction so the database is not left in a bad state.
        connection.rollback()

        return (
            False,
            f"Error recording payment: {e}",
            None
        )

    finally:
        # Always close the database connection.
        connection.close()
        



# A function that lets an authorized admin link an existing guardian to an existing student.
def link_guardian_to_student_db(
    guardian_id,
    student_number,
    relationship
):
    """
    Link a guardian to a student.

    The guardian_students table stores the relationship between
    a specific guardian and a specific student.

    Example:

        Guardian 4000055
        Student 1000050
        Relationship: Mother

    This is kept in guardian_students because the same guardian
    could have different relationships with different students.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # --------------------------------------------------
        # Check that the guardian exists
        # --------------------------------------------------
        cursor.execute("""
            SELECT guardian_id, first_name, last_name
            FROM guardians
            WHERE guardian_id = ?
        """, (guardian_id,))

        guardian = cursor.fetchone()

        if guardian is None:
            return False, "Guardian not found."

        # --------------------------------------------------
        # Check that the student exists
        # --------------------------------------------------
        cursor.execute("""
            SELECT student_number, student_name
            FROM students
            WHERE student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

        if student is None:
            return False, "Student not found."

        # --------------------------------------------------
        # Check whether this guardian is already linked
        # to this student.
        # --------------------------------------------------
        cursor.execute("""
            SELECT relationship
            FROM guardian_students
            WHERE guardian_id = ?
              AND student_number = ?
        """, (
            guardian_id,
            student_number
        ))

        existing_link = cursor.fetchone()

        if existing_link is not None:
            return False, (
                "This guardian is already linked to this student "
                f"as {existing_link[0]}."
            )

        # --------------------------------------------------
        # Save the relationship.
        # --------------------------------------------------
        cursor.execute("""
            INSERT INTO guardian_students (
                guardian_id,
                student_number,
                relationship
            )
            VALUES (?, ?, ?)
        """, (
            guardian_id,
            student_number,
            relationship
        ))

        connection.commit()

        return True, "Guardian successfully linked to student."

    except sqlite3.IntegrityError as error:
        connection.rollback()
        return False, f"Database error: {error}"

    except Exception as error:
        connection.rollback()
        return False, f"Error linking guardian to student: {error}"

    finally:
        connection.close()




# the interactive admin function. This is the part the Principal or Accounts user will actually use.
def link_guardian_to_student():
    """
    Interactive function used by an authorized admin to link
    an existing guardian to an existing student.

    The admin chooses:
        1. Guardian
        2. Student
        3. Relationship

    The relationship is stored in guardian_students because
    it describes the relationship between THIS guardian and
    THIS student.
    """

    print("\n===== LINK GUARDIAN TO STUDENT =====\n")

    # --------------------------------------------------
    # STEP 1: Ask for the Guardian Number
    # --------------------------------------------------
    try:
        guardian_id = int(
            input("Enter Guardian Number: ")
        )
    except ValueError:
        print("\nGuardian Number must be a number.\n")
        return

    # --------------------------------------------------
    # Check that the guardian exists and display
    # the guardian's information.
    # --------------------------------------------------
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            guardian_id,
            first_name,
            last_name,
            phone_number
        FROM guardians
        WHERE guardian_id = ?
    """, (guardian_id,))

    guardian = cursor.fetchone()

    connection.close()

    if guardian is None:
        print("\nGuardian not found.\n")
        return

    print("\nGuardian Found")
    print("------------------------------")
    print("Guardian Number:", guardian[0])
    print("Name           :", guardian[1], guardian[2])
    print("Phone          :", guardian[3])

    # --------------------------------------------------
    # STEP 2: Ask for the Student Number
    # --------------------------------------------------
    try:
        student_number = int(
            input("\nEnter Student Number: ")
        )
    except ValueError:
        print("\nStudent Number must be a number.\n")
        return

    # --------------------------------------------------
    # Check that the student exists and display
    # the student's information.
    # --------------------------------------------------
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            s.student_number,
            s.student_name,
            g.grade_name,
            s.classroom
        FROM students s
        LEFT JOIN grades g
            ON g.grade_id = s.grade_id
        WHERE s.student_number = ?
    """, (student_number,))

    student = cursor.fetchone()

    connection.close()

    if student is None:
        print("\nStudent not found.\n")
        return

    print("\nStudent Found")
    print("------------------------------")
    print("Student Number:", student["student_number"])
    print("Name          :", student["student_name"])
    print("Grade         :", student["grade_name"])
    print("Class         :", student["classroom"])

    # --------------------------------------------------
    # STEP 3: Choose the relationship
    # --------------------------------------------------
    relationships = [
        "Mother",
        "Father",
        "Guardian",
        "Grandmother",
        "Grandfather",
        "Aunt",
        "Uncle",
        "Other"
    ]

    print("\n===== SELECT RELATIONSHIP =====\n")

    for number, relationship in enumerate(
        relationships,
        start=1
    ):
        print(f"{number}. {relationship}")

    try:
        relationship_choice = int(
            input("\nChoose relationship: ")
        )
    except ValueError:
        print("\nPlease enter a number.\n")
        return

    # --------------------------------------------------
    # Make sure the selected number is valid.
    # --------------------------------------------------
    if not 1 <= relationship_choice <= len(relationships):
        print("\nInvalid relationship choice.\n")
        return

    relationship = relationships[
        relationship_choice - 1
    ]

    # --------------------------------------------------
    # STEP 4: Show everything before saving.
    # --------------------------------------------------
    print("\n===== CONFIRM LINK =====\n")
    print(
        "Guardian:",
        guardian[1],
        guardian[2],
        f"({guardian_id})"
    )
    print(
        "Student :",
        student["student_name"],
        f"({student_number})"
    )
    print("Relationship:", relationship)

    confirmation = input(
        "\nLink this guardian to this student? (Y/N): "
    ).strip().upper()

    if confirmation != "Y":
        print("\nLink cancelled.\n")
        return

    # --------------------------------------------------
    # STEP 5: Save the relationship in the database.
    # --------------------------------------------------
    success, message = link_guardian_to_student_db(
        guardian_id,
        student_number,
        relationship
    )

    if success:
        print("\n" + message)
        print()
    else:
        print("\n" + message)
        print()




def get_guardian_children_db(guardian_id):
    """
    Get all students linked to a particular guardian.

    The guardian_students table tells us which students
    belong to this guardian.

    We also get the student's grade and relationship.
    """

    connection = get_connection()

    # Return database rows using column names.
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                s.student_number,
                s.student_name,
                s.id_number,
                s.nationality,
                s.age,
                s.gender,
                s.classroom,
                g.grade_name,
                gs.relationship

            FROM guardian_students gs

            JOIN students s
                ON s.student_number = gs.student_number

            LEFT JOIN grades g
                ON g.grade_id = s.grade_id

            WHERE gs.guardian_id = ?

            ORDER BY s.student_name
        """, (guardian_id,))

        children = cursor.fetchall()

        # Convert each SQLite Row into a normal dictionary.
        return [dict(child) for child in children]

    except Exception as error:

        print(
            f"\nError getting guardian's children: {error}"
        )

        return []

    finally:
        connection.close()




def view_guardian_children(guardian_id):
    """
    Display all students linked to this guardian.

    A guardian may have more than one child, so we display
    every student connected to this Guardian Number.
    """

    children = get_guardian_children_db(guardian_id)

    print("\n===== YOUR CHILDREN =====\n")

    # --------------------------------------------------
    # Check whether this guardian has any linked students.
    # --------------------------------------------------
    if not children:
        print("No students are currently linked to your account.\n")
        return

    # --------------------------------------------------
    # Display every child linked to this guardian.
    # --------------------------------------------------
    for number, child in enumerate(children, start=1):

        print(f"----- CHILD {number} -----")

        print(
            "Student Number:",
            child["student_number"]
        )

        print(
            "Name          :",
            child["student_name"]
        )

        print(
            "ID Number     :",
            child["id_number"]
        )

        print(
            "Nationality   :",
            child["nationality"]
        )

        print(
            "Age           :",
            child["age"]
        )

        print(
            "Gender        :",
            child["gender"]
        )

        print(
            "Grade         :",
            child["grade_name"]
        )

        print(
            "Class         :",
            child["classroom"]
        )

        print(
            "Relationship  :",
            child["relationship"]
        )

        print("------------------------------")

    print()




def view_guardian_child_attendance(guardian_id):
    """
    Allow a guardian to view the attendance of one of their children.

    The guardian:
        1. Selects a child.
        2. Selects a school term.
        3. Views the attendance summary.
        4. Views the attendance records.
        5. Can return to the term selection.

    This keeps the guardian inside the attendance feature
    until they choose to go back.
    """

    # ----------------------------------------------------------
    # Get all students linked to this guardian.
    # ----------------------------------------------------------
    children = get_guardian_children_db(guardian_id)

    print("\n===== CHILD ATTENDANCE =====\n")

    if not children:
        print("No students are currently linked to your account.\n")
        return

    # ----------------------------------------------------------
    # Display the guardian's children.
    # ----------------------------------------------------------
    for number, child in enumerate(children, start=1):
        print(
            f"{number}. "
            f"{child['student_name']} "
            f"(Student Number: {child['student_number']})"
        )

    print("0. Back")

    # ----------------------------------------------------------
    # Ask the guardian to select a child.
    # ----------------------------------------------------------
    try:
        choice = int(input("\nChoose a child: "))

    except ValueError:
        print("\nNumbers only allowed.\n")
        return

    if choice == 0:
        return

    if choice < 1 or choice > len(children):
        print("\nInvalid child selection.\n")
        return

    # Get the selected child.
    selected_child = children[choice - 1]

    student_number = selected_child["student_number"]
    student_name = selected_child["student_name"]

    # ----------------------------------------------------------
    # Get the current school term.
    # ----------------------------------------------------------
    current_term = get_current_school_term_db()

    if current_term:
        current_school_year = current_term["school_year"]
        current_term_number = current_term["term_number"]
    else:
        current_school_year = 2026
        current_term_number = 1

    # ----------------------------------------------------------
    # Keep showing the term menu until the guardian chooses Back.
    # ----------------------------------------------------------
    while True:

        print("\n===== SELECT ATTENDANCE TERM =====\n")

        print("1. Term 1")
        print("2. Term 2")
        print("3. Term 3")
        print("4. Term 4")
        print("5. All Attendance")
        print("0. Back")

        # ------------------------------------------------------
        # Ask the guardian to select a term.
        # ------------------------------------------------------
        try:
            term_choice = int(input("\nChoose a term: "))

        except ValueError:
            print("\nNumbers only allowed.\n")
            continue

        # Return to the Guardian Panel.
        if term_choice == 0:
            return

        # Check that the option is valid.
        if term_choice not in range(1, 6):
            print("\nInvalid term selection.\n")
            continue

        # ------------------------------------------------------
        # Get attendance records.
        #
        # Option 5 shows all attendance.
        #
        # Options 1-4 show attendance for a specific term.
        # ------------------------------------------------------
        if term_choice == 5:

            attendance = get_student_attendance_db(
                student_number
            )

            selected_term_text = "All Terms"

        else:

            attendance = get_guardian_child_attendance_by_term_db(
                student_number,
                current_school_year,
                term_choice
            )

            selected_term_text = f"Term {term_choice}"

        # ------------------------------------------------------
        # Display student information.
        # ------------------------------------------------------
        print("\n======================================")
        print("         STUDENT ATTENDANCE")
        print("======================================")
        print("Student Number :", student_number)
        print("Student Name   :", student_name)
        print("Grade          :", selected_child["grade_name"])
        print("Class          :", selected_child["classroom"])
        print("School Year    :", current_school_year)
        print("Attendance Term:", selected_term_text)
        print("--------------------------------------")

        # ------------------------------------------------------
        # If there are no records, don't leave the feature.
        #
        # Instead, show the message and return to the term menu.
        # ------------------------------------------------------
        if not attendance:

            print(
                "\nNo attendance records found for "
                f"{selected_term_text}."
            )

            input(
                "\nPress Enter to return to the term selection..."
            )

            continue

        # ------------------------------------------------------
        # Calculate attendance statistics.
        # ------------------------------------------------------
        total_records = len(attendance)

        present_count = 0
        absent_count = 0

        for record in attendance:

            status = str(record[2]).strip().lower()

            if status == "present":
                present_count += 1

            elif status == "absent":
                absent_count += 1

        # ------------------------------------------------------
        # Calculate attendance percentage.
        # ------------------------------------------------------
        attendance_percentage = (
            present_count / total_records
        ) * 100

        # ------------------------------------------------------
        # Display attendance summary.
        # ------------------------------------------------------
        print("\n===== ATTENDANCE SUMMARY =====")
        print("Total Records :", total_records)
        print("Present       :", present_count)
        print("Absent        :", absent_count)
        print(
            "Attendance    : "
            f"{attendance_percentage:.2f}%"
        )
        print("--------------------------------------")

        # ------------------------------------------------------
        # Display individual attendance records.
        # ------------------------------------------------------
        print("\n===== ATTENDANCE RECORDS =====\n")

        for record in attendance:

            print("Date    :", record[1])
            print("Status  :", record[2])
            print("Subject :", record[3])
            print("Teacher :", record[4])
            print("--------------------------------------")

        # ------------------------------------------------------
        # After viewing the records, ask what the guardian wants
        # to do next.
        # ------------------------------------------------------
        print("\n1. View another term")
        print("0. Back to Guardian Panel")

        try:
            next_choice = int(
                input("\nChoose an option: ")
            )

        except ValueError:
            print("\nNumbers only allowed.")
            continue

        if next_choice == 0:
            return

        elif next_choice == 1:
            continue

        else:
            print("\nInvalid option.")
    
    
    

def get_guardian_child_attendance_by_term_db(
    student_number,
    school_year,
    term_number
):
    """
    Get attendance records for a student for a specific school term.

    The attendance table stores the attendance date.
    We use the school_terms table to find the start and end
    dates for the selected term.

    Example:

        Student: 1000064
        School Year: 2026
        Term: 3

    The function will only return attendance records that
    happened between the Term 3 start and end dates.
    """

    # Open a connection to the database.
    connection = get_connection()

    # Create a cursor so we can execute SQL commands.
    cursor = connection.cursor()

    # ----------------------------------------------------------
    # First find the start and end dates of the selected term.
    # ----------------------------------------------------------
    cursor.execute("""
        SELECT
            start_date,
            end_date
        FROM school_terms
        WHERE school_year = ?
          AND term_number = ?
    """, (
        school_year,
        term_number
    ))

    term = cursor.fetchone()

    # If the term does not exist, return an empty list.
    if term is None:
        connection.close()
        return []

    start_date = term[0]
    end_date = term[1]

    # ----------------------------------------------------------
    # Get attendance records for this student that fall
    # between the selected term's start and end dates.
    #
    # We use the same joins as get_student_attendance_db()
    # so the guardian sees the subject and teacher names.
    # ----------------------------------------------------------
    cursor.execute("""
        SELECT
            a.attendance_id,
            a.attendance_date,
            a.status,
            s.subject_name,
            t.teacher_name
        FROM attendance a

        JOIN student_subjects ss
            ON ss.student_number = a.student_number

        JOIN subjects s
            ON s.subject_id = a.subject_id
            AND s.subject_name = ss.subject_name

        JOIN teachers t
            ON t.teacher_number = a.teacher_number

        WHERE a.student_number = ?
          AND a.attendance_date BETWEEN ? AND ?

        ORDER BY a.attendance_date DESC
    """, (
        student_number,
        start_date,
        end_date
    ))

    # Get all matching attendance records.
    attendance = cursor.fetchall()

    # Close the database connection.
    connection.close()

    # Return the attendance records.
    return attendance    



def get_guardian_child_homework_db(student_number):
    """
    Get all homework assigned to a specific student.

    This function is designed for the Guardian Panel.

    It shows:
    1. Homework information
    2. Subject
    3. Teacher
    4. Grade
    5. Whether the student submitted the homework
    6. Submission date
    7. Teacher's marking status
    8. Mark received

    IMPORTANT:
    A LEFT JOIN is used for homework_submissions.

    Why?

    Some homework may not have been submitted yet.
    We still want that homework to appear in the guardian's
    homework list.

    Therefore:

        Submission exists
            -> Submitted

        No submission exists
            -> Not Submitted
    """

    connection = get_connection()

    # Row objects allow us to use names such as:
    # homework["title"]
    # homework["subject_name"]
    # homework["submission_status"]
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                h.homework_id,
                h.title,
                h.description,
                h.due_date,
                h.date_posted,

                s.subject_name,

                t.teacher_name,

                g.grade_name,

                hs.submission_id,
                hs.submitted_date,

                hs.status AS submission_status,

                hs.mark,
                hs.total_possible

            FROM homework h

            JOIN students st
                ON st.student_number = ?

            JOIN subjects s
                ON s.subject_id = h.subject_id

            JOIN student_subjects ss
                ON ss.student_number = st.student_number
                AND ss.subject_name = s.subject_name

            JOIN grades g
                ON g.grade_id = h.grade_id
                AND g.grade_id = st.grade_id

            JOIN teachers t
                ON t.teacher_number = h.teacher_number

            LEFT JOIN homework_submissions hs
                ON hs.homework_id = h.homework_id
                AND hs.student_number = st.student_number

            WHERE h.grade_id = st.grade_id

            ORDER BY h.due_date
        """, (student_number,))

        homework = cursor.fetchall()

        return [dict(item) for item in homework]

    except Exception as error:

        print(
            f"\nError getting guardian child homework: "
            f"{error}"
        )

        return []

    finally:
        connection.close()





def get_guardian_child_homework_by_term_db(
    student_number,
    school_year,
    term_number
):
    """
    Get a child's homework for a specific school term.

    The function first finds the start and end dates
    of the selected term from the school_terms table.

    It then returns homework that:
    - Belongs to the student's grade
    - Belongs to a subject assigned to the student
    - Was posted during the selected term
    """

    connection = get_connection()

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    try:
        # ------------------------------------------------------
        # FIND THE SELECTED TERM
        # ------------------------------------------------------
        cursor.execute("""
            SELECT
                start_date,
                end_date
            FROM school_terms
            WHERE school_year = ?
              AND term_number = ?
        """, (
            school_year,
            term_number
        ))

        term = cursor.fetchone()

        # If the term does not exist, return no homework.
        if term is None:
            return []

        start_date = term["start_date"]
        end_date = term["end_date"]

        # ------------------------------------------------------
        # GET HOMEWORK FOR THE SELECTED TERM
        # ------------------------------------------------------
        cursor.execute("""
            SELECT
                h.homework_id,
                h.title,
                h.description,
                h.due_date,
                h.date_posted,

                s.subject_name,

                t.teacher_name,

                g.grade_name,

                hs.submission_id,
                hs.submitted_date,

                hs.status AS submission_status,

                hs.mark,
                hs.total_possible

            FROM homework h

            JOIN students st
                ON st.student_number = ?

            JOIN subjects s
                ON s.subject_id = h.subject_id

            JOIN student_subjects ss
                ON ss.student_number = st.student_number
                AND ss.subject_name = s.subject_name

            JOIN grades g
                ON g.grade_id = h.grade_id
                AND g.grade_id = st.grade_id

            JOIN teachers t
                ON t.teacher_number = h.teacher_number

            LEFT JOIN homework_submissions hs
                ON hs.homework_id = h.homework_id
                AND hs.student_number = st.student_number

            WHERE h.grade_id = st.grade_id

              AND h.date_posted BETWEEN ? AND ?

            ORDER BY h.date_posted DESC
        """, (
            student_number,
            start_date,
            end_date
        ))

        homework = cursor.fetchall()

        return [dict(item) for item in homework]

    except Exception as error:

        print(
            f"\nError getting homework by term: "
            f"{error}"
        )

        return []

    finally:
        connection.close()






def view_guardian_child_homework(guardian_id):
    """
    Allow a guardian to select a child and then select
    a school term to view that child's homework.

    Menu:

        Term 1
        Term 2
        Term 3
        Term 4
        All Homework
        Back
    """

    # ----------------------------------------------------------
    # GET CHILDREN LINKED TO THIS GUARDIAN
    # ----------------------------------------------------------
    children = get_guardian_children_db(guardian_id)

    if not children:
        print("\nNo students are currently linked to your account.\n")
        return

    # ----------------------------------------------------------
    # SELECT CHILD
    # ----------------------------------------------------------
    print("\n===== SELECT YOUR CHILD =====\n")

    for number, child in enumerate(children, start=1):
        print(
            f"{number}. "
            f"{child['student_name']} "
            f"(Student No: {child['student_number']})"
        )

    print("0. Back")

    try:
        child_choice = int(
            input("\nChoose a child: ")
        )
    except ValueError:
        print("\nNumbers only allowed.\n")
        return

    if child_choice == 0:
        return

    if child_choice < 1 or child_choice > len(children):
        print("\nInvalid child selection.\n")
        return

    selected_child = children[child_choice - 1]

    student_number = selected_child["student_number"]

    # ----------------------------------------------------------
    # GET CURRENT SCHOOL YEAR
    # ----------------------------------------------------------
    current_school_term = get_current_school_term_db()

    if current_school_term is None:

        print("\nSchool term information is not available.\n")
        input("Press Enter to return...")
        return

    current_school_year = current_school_term["school_year"]

    # ----------------------------------------------------------
    # TERM SELECTION LOOP
    # ----------------------------------------------------------
    while True:

        print("\n======================================")
        print("       SELECT HOMEWORK TERM")
        print("======================================\n")

        print("1. Term 1")
        print("2. Term 2")
        print("3. Term 3")
        print("4. Term 4")
        print("5. All Homework")
        print("0. Back to Guardian Panel")

        try:
            term_choice = int(
                input("\nChoose a term: ")
            )
        except ValueError:
            print("\nNumbers only allowed.\n")
            continue

        if term_choice == 0:
            return

        # ------------------------------------------------------
        # ALL HOMEWORK
        # ------------------------------------------------------
        if term_choice == 5:

            homework_list = get_guardian_child_homework_db(
                student_number
            )

            selected_term_text = "All Homework"

        # ------------------------------------------------------
        # SPECIFIC TERM
        # ------------------------------------------------------
        elif term_choice in range(1, 5):

            homework_list = get_guardian_child_homework_by_term_db(
                student_number,
                current_school_year,
                term_choice
            )

            selected_term_text = f"Term {term_choice}"

        else:

            print(
                "\nInvalid option. "
                "Please choose 0 to 5.\n"
            )

            continue

        # ------------------------------------------------------
        # DISPLAY CHILD INFORMATION
        # ------------------------------------------------------
        print("\n======================================")
        print("       CHILD'S HOMEWORK")
        print("======================================\n")

        print(
            f"Student Name : "
            f"{selected_child['student_name']}"
        )

        print(
            f"Student No   : "
            f"{selected_child['student_number']}"
        )

        print(
            f"Grade        : "
            f"{selected_child['grade_name']}"
        )

        print(
            f"Class        : "
            f"{selected_child['classroom']}"
        )

        print(
            f"School Year  : "
            f"{current_school_year}"
        )

        print(
            f"Selected Term: "
            f"{selected_term_text}"
        )

        print("--------------------------------------")

        # ------------------------------------------------------
        # NO HOMEWORK
        # ------------------------------------------------------
        if not homework_list:

            print(
                f"\nNo homework records found for "
                f"{selected_term_text}."
            )

            input(
                "\nPress Enter to return to "
                "term selection..."
            )

            continue

        # ------------------------------------------------------
        # DISPLAY HOMEWORK
        # ------------------------------------------------------
        for number, homework in enumerate(
            homework_list,
            start=1
        ):

            print(
                f"\n===== HOMEWORK {number} ====="
            )

            print(
                f"Subject      : "
                f"{homework['subject_name']}"
            )

            print(
                f"Homework     : "
                f"{homework['title']}"
            )

            if homework["description"]:

                print(
                    f"Description  : "
                    f"{homework['description']}"
                )

            print(
                f"Date Posted  : "
                f"{homework['date_posted']}"
            )

            print(
                f"Due Date     : "
                f"{homework['due_date']}"
            )

            print(
                f"Teacher      : "
                f"{homework['teacher_name']}"
            )

            # --------------------------------------------------
            # SUBMISSION INFORMATION
            # --------------------------------------------------
            if homework["submission_id"] is None:

                print(
                    "Submission   : Not Submitted"
                )

                print(
                    "Submitted Date: --"
                )

                print(
                    "Teacher Status: --"
                )

                print(
                    "Mark         : --"
                )

            else:

                print(
                    "Submission   : Submitted"
                )

                print(
                    f"Submitted Date: "
                    f"{homework['submitted_date']}"
                )

                print(
                    f"Teacher Status: "
                    f"{homework['submission_status']}"
                )

                if homework["mark"] is not None:

                    print(
                        f"Mark         : "
                        f"{homework['mark']}"
                        f"/"
                        f"{homework['total_possible']}"
                    )

                else:

                    print(
                        "Mark         : Not Marked"
                    )

            print("--------------------------------------")

        print()

        input(
            "Press Enter to return to "
            "term selection..."
        )





def print_guardian_child_report_card(guardian_id):
    """
    Allow a guardian to select one of their children,
    select a school term, check the child's fee balance,
    and print the child's report card.

    The report card is only generated when the child's
    outstanding fee balance is R0.00.
    """

    # ---------------------------------------------------------
    # STEP 1:
    # Get all students linked to this guardian.
    # ---------------------------------------------------------

    children = get_guardian_children_db(guardian_id)

    if not children:
        print(
            "\nNo students are currently linked "
            "to your account.\n"
        )
        return

    # ---------------------------------------------------------
    # STEP 2:
    # Display the guardian's children.
    # ---------------------------------------------------------

    print("\n===== SELECT YOUR CHILD =====\n")

    for number, child in enumerate(children, start=1):
        print(
            f"{number}. "
            f"{child['student_name']} "
            f"({child['student_number']})"
        )

    print("0. Back to Guardian Panel")

    # ---------------------------------------------------------
    # STEP 3:
    # Let the guardian select a child.
    # ---------------------------------------------------------

    try:
        child_choice = int(
            input("\nChoose your child: ")
        )
    except ValueError:
        print("\nNumbers only allowed.\n")
        return

    if child_choice == 0:
        return

    if (
        child_choice < 1
        or child_choice > len(children)
    ):
        print("\nInvalid child selection.\n")
        return

    selected_child = children[
        child_choice - 1
    ]

    student_number = selected_child[
        "student_number"
    ]

    # ---------------------------------------------------------
    # STEP 4:
    # Get the current school year.
    # ---------------------------------------------------------

    current_school_term = (
        get_current_school_term_db()
    )

    if current_school_term is None:
        print(
            "\nSchool term information is unavailable.\n"
        )
        return

    school_year = current_school_term[
        "school_year"
    ]

    # ---------------------------------------------------------
    # STEP 5:
    # Display the selected child.
    # ---------------------------------------------------------

    print("\n===== REPORT CARD =====\n")

    print(
        "Student Number :",
        selected_child["student_number"]
    )

    print(
        "Name           :",
        selected_child["student_name"]
    )

    print(
        "Grade          :",
        selected_child["grade_name"]
    )

    print(
        "Class          :",
        selected_child["classroom"]
    )

    print(
        "School Year    :",
        school_year
    )

    # ---------------------------------------------------------
    # STEP 6:
    # Select the report-card term.
    # ---------------------------------------------------------

    print("\n===== SELECT TERM =====\n")

    print("1. Term 1")
    print("2. Term 2")
    print("3. Term 3")
    print("4. Term 4")
    print("0. Back")

    try:
        term_choice = int(
            input("\nChoose a term: ")
        )
    except ValueError:
        print("\nNumbers only allowed.\n")
        return

    if term_choice == 0:
        return

    if term_choice not in range(1, 5):
        print("\nInvalid term selection.\n")
        return

    term_number = term_choice

    # ---------------------------------------------------------
    # STEP 7:
    # Check the child's fee balance.
    #
    # We use the SAME fee calculation already used by
    # the student report-card system.
    # ---------------------------------------------------------

    fee_status = get_student_total_fee_due_db(
        student_number,
        school_year,
        term_number
    )

    # Make sure the fee calculation succeeded.
    if fee_status is None:
        print(
            "\nUnable to retrieve the student's "
            "fee information.\n"
        )
        return

    remaining_balance = fee_status[
        "remaining_balance"
    ]

    # ---------------------------------------------------------
    # STEP 8:
    # Lock the report card if there is still money owing.
    # ---------------------------------------------------------

    if remaining_balance > 0:

        print("\n======================================")
        print("        REPORT CARD LOCKED")
        print("======================================")

        print(
            f"\nOutstanding Balance: "
            f"R{remaining_balance:,.2f}"
        )

        print(
            "\nPlease clear all outstanding "
            "fee balances before accessing "
            "the report card."
        )

        print(
            "\n======================================\n"
        )

        return

    # ---------------------------------------------------------
    # STEP 9:
    # Generate the report card.
    # ---------------------------------------------------------

    print(
        "\nFees are fully paid."
    )

    print(
        f"Generating Term {term_number} "
        "report card...\n"
    )

    generate_guardian_child_report_card_pdf(
        student_number,
        school_year,
        term_number
    )




def view_guardian_child_timetable(guardian_id):
    """
    Allow a guardian to select one of their children
    and view that child's timetable.

    The timetable is obtained using the existing
    get_student_timetable_db() function.

    That function matches the student's:
    - Grade
    - Classroom

    This prevents a student from seeing the timetable
    belonging to another classroom.
    """

    # ---------------------------------------------------------
    # STEP 1:
    # Get all children linked to this guardian.
    # ---------------------------------------------------------

    children = get_guardian_children_db(guardian_id)

    if not children:
        print(
            "\nNo students are currently linked "
            "to your account.\n"
        )
        return

    # ---------------------------------------------------------
    # STEP 2:
    # Display the guardian's children.
    # ---------------------------------------------------------

    print("\n===== SELECT YOUR CHILD =====\n")

    for number, child in enumerate(children, start=1):
        print(
            f"{number}. "
            f"{child['student_name']} "
            f"({child['student_number']})"
        )

    print("0. Back to Guardian Panel")

    # ---------------------------------------------------------
    # STEP 3:
    # Let the guardian select a child.
    # ---------------------------------------------------------

    try:
        child_choice = int(
            input("\nChoose your child: ")
        )

    except ValueError:
        print("\nNumbers only allowed.\n")
        return

    if child_choice == 0:
        return

    if (
        child_choice < 1
        or child_choice > len(children)
    ):
        print("\nInvalid child selection.\n")
        return

    selected_child = children[
        child_choice - 1
    ]

    student_number = selected_child[
        "student_number"
    ]

    # ---------------------------------------------------------
    # STEP 4:
    # Get the student's timetable.
    #
    # The existing database function automatically
    # matches the student's grade and classroom.
    # ---------------------------------------------------------

    timetable = get_student_timetable_db(
        student_number
    )

    # ---------------------------------------------------------
    # STEP 5:
    # Display the student's information.
    # ---------------------------------------------------------

    print("\n===== YOUR CHILD'S TIMETABLE =====\n")

    print(
        "Student Number :",
        selected_child["student_number"]
    )

    print(
        "Name           :",
        selected_child["student_name"]
    )

    print(
        "Grade          :",
        selected_child["grade_name"]
    )

    print(
        "Class          :",
        selected_child["classroom"]
    )

    print("\n---------------------------------------------")

    # ---------------------------------------------------------
    # STEP 6:
    # Check whether timetable records exist.
    # ---------------------------------------------------------

    if not timetable:
        print(
            "\nNo timetable records were found "
            "for this student.\n"
        )
        return

    # ---------------------------------------------------------
    # STEP 7:
    # Display each timetable record.
    #
    # get_student_timetable_db() returns:
    #
    # 0 = timetable_id
    # 1 = grade_name
    # 2 = classroom
    # 3 = day
    # 4 = start_time
    # 5 = end_time
    # 6 = subject_name
    # 7 = teacher_name
    # ---------------------------------------------------------

    current_day = None

    for record in timetable:

        day = record[3]

        # When the day changes, print a new heading.
        if day != current_day:

            print(
                f"\n===== {day.upper()} ====="
            )

            current_day = day

        print(
            f"{record[4]} - {record[5]}  |  "
            f"{record[6]}  |  "
            f"Teacher: {record[7]}"
        )

    print(
        "\n---------------------------------------------"
    )

    print(
        "\nEnd of timetable.\n"
    )



def view_guardian_child_school_news(guardian_id):
    """
    Allow a guardian to select one of their children
    and view school news relevant to that child.

    News visibility works as follows:

    1. General news
       grade_id IS NULL
       -> Visible to everyone.

    2. Grade-specific news
       grade_id matches the child's grade_id
       -> Visible to that child's guardian.

    3. News for another grade
       -> Not displayed.
    """

    # ---------------------------------------------------------
    # STEP 1:
    # Get all children linked to this guardian.
    # ---------------------------------------------------------

    children = get_guardian_children_db(guardian_id)

    if not children:
        print(
            "\nNo students are currently linked "
            "to your account.\n"
        )
        return

    # ---------------------------------------------------------
    # STEP 2:
    # Display the guardian's children.
    # ---------------------------------------------------------

    print("\n===== SELECT YOUR CHILD =====\n")

    for number, child in enumerate(children, start=1):
        print(
            f"{number}. "
            f"{child['student_name']} "
            f"({child['student_number']})"
        )

    print("0. Back to Guardian Panel")

    # ---------------------------------------------------------
    # STEP 3:
    # Let the guardian select a child.
    # ---------------------------------------------------------

    try:
        child_choice = int(
            input("\nChoose your child: ")
        )

    except ValueError:
        print("\nNumbers only allowed.\n")
        return

    if child_choice == 0:
        return

    if (
        child_choice < 1
        or child_choice > len(children)
    ):
        print("\nInvalid child selection.\n")
        return

    selected_child = children[
        child_choice - 1
    ]

    student_number = selected_child[
        "student_number"
    ]

    # ---------------------------------------------------------
    # STEP 4:
    # Get the child's grade_id.
    #
    # get_guardian_children_db() gives us the grade name,
    # but not the grade_id.
    #
    # We therefore get the grade_id directly from students.
    # ---------------------------------------------------------

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT grade_id
        FROM students
        WHERE student_number = ?
    """, (student_number,))

    student = cursor.fetchone()

    connection.close()

    if student is None:
        print("\nStudent not found.\n")
        return

    grade_id = student[0]

    # ---------------------------------------------------------
    # STEP 5:
    # Get relevant school news.
    #
    # General news:
    #     grade_id IS NULL
    #
    # Grade-specific news:
    #     grade_id = child's grade_id
    # ---------------------------------------------------------

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            sn.news_id,
            sn.title,
            sn.content,
            sn.date_posted,
            sn.category,
            a.admin_name
        FROM school_news sn
        JOIN admins a
            ON a.admin_id = sn.admin_id
        WHERE sn.grade_id IS NULL
           OR sn.grade_id = ?
        ORDER BY
            sn.date_posted DESC,
            sn.news_id DESC
    """, (grade_id,))

    news = cursor.fetchall()

    connection.close()

    # ---------------------------------------------------------
    # STEP 6:
    # Display the selected child.
    # ---------------------------------------------------------

    print("\n===== YOUR CHILD'S SCHOOL NEWS =====\n")

    print(
        "Student Number :",
        selected_child["student_number"]
    )

    print(
        "Name           :",
        selected_child["student_name"]
    )

    print(
        "Grade          :",
        selected_child["grade_name"]
    )

    print(
        "Class          :",
        selected_child["classroom"]
    )

    print(
        "\n---------------------------------------------"
    )

    # ---------------------------------------------------------
    # STEP 7:
    # Check whether any news was found.
    # ---------------------------------------------------------

    if not news:
        print(
            "\nNo school news is currently available.\n"
        )
        return

    # ---------------------------------------------------------
    # STEP 8:
    # Display the news.
    # ---------------------------------------------------------

    for item in news:

        print("\n===== NEWS =====")

        print(
            "News ID       :",
            item[0]
        )

        print(
            "Title         :",
            item[1]
        )

        print(
            "Category      :",
            item[4]
        )

        print(
            "Date Posted   :",
            item[3]
        )

        print(
            "Posted By     :",
            item[5]
        )

        print(
            "Content       :",
            item[2]
        )

        print(
            "---------------------------------------------"
        )

    print()
    
    

def view_guardian_child_fees_statement(guardian_id):
    """
    Allow a guardian to select one of their children
    and view that child's complete fees statement.

    The actual fee calculation is handled by the existing
    show_student_fees_statement() function.

    This function only:
    1. Gets the guardian's children.
    2. Lets the guardian select a child.
    3. Sends that child's student number to the
       existing fee statement function.
    """

    # ---------------------------------------------------------
    # STEP 1:
    # Get all students linked to this guardian.
    # ---------------------------------------------------------

    children = get_guardian_children_db(guardian_id)

    if not children:
        print(
            "\nNo students are currently linked "
            "to your account.\n"
        )
        return

    # ---------------------------------------------------------
    # STEP 2:
    # Display the guardian's children.
    # ---------------------------------------------------------

    print("\n===== SELECT YOUR CHILD =====\n")

    for number, child in enumerate(children, start=1):
        print(
            f"{number}. "
            f"{child['student_name']} "
            f"({child['student_number']})"
        )

    print("0. Back to Guardian Panel")

    # ---------------------------------------------------------
    # STEP 3:
    # Let the guardian select a child.
    # ---------------------------------------------------------

    try:
        child_choice = int(
            input("\nChoose your child: ")
        )

    except ValueError:
        print("\nNumbers only allowed.\n")
        return

    if child_choice == 0:
        return

    if (
        child_choice < 1
        or child_choice > len(children)
    ):
        print("\nInvalid child selection.\n")
        return

    # ---------------------------------------------------------
    # STEP 4:
    # Get the selected child.
    # ---------------------------------------------------------

    selected_child = children[
        child_choice - 1
    ]

    student_number = selected_child[
        "student_number"
    ]

    # ---------------------------------------------------------
    # STEP 5:
    # Display the selected child.
    # ---------------------------------------------------------

    print("\n===== CHILD FEES STATEMENT =====\n")

    print(
        "Student Number :",
        selected_child["student_number"]
    )

    print(
        "Name           :",
        selected_child["student_name"]
    )

    print(
        "Grade          :",
        selected_child["grade_name"]
    )

    print(
        "Class          :",
        selected_child["classroom"]
    )

    print(
        "\nLoading fees statement...\n"
    )

    # ---------------------------------------------------------
    # STEP 6:
    # Use the existing fee statement function.
    #
    # This is important because we don't want two different
    # fee calculation systems in the project.
    # ---------------------------------------------------------

    show_student_fees_statement(
        student_number
    )
         


def make_guardian_child_fee_payment(guardian_id):
    """
    Allow a guardian to select one of their children
    and make a school fee payment.

    The guardian does NOT choose the school year or term.
    The system automatically uses today's date and finds
    the correct school term from the school_terms table.

    The existing record_fee_payment() function is then used
    to save the payment and apply the existing fee rules.
    """

    # ---------------------------------------------------------
    # GET THE GUARDIAN'S CHILDREN
    # ---------------------------------------------------------
    children = get_guardian_children_db(guardian_id)

    if not children:
        print(
            "\nNo students are currently linked "
            "to your account.\n"
        )
        return

    # ---------------------------------------------------------
    # LET THE GUARDIAN CHOOSE A CHILD
    # ---------------------------------------------------------
    print("\n===== SELECT YOUR CHILD =====\n")

    for number, child in enumerate(children, start=1):
        print(
            f"{number}. "
            f"{child['student_name']} "
            f"({child['student_number']})"
        )

    print("0. Back to Guardian Panel")

    try:
        child_choice = int(
            input("\nChoose your child: ")
        )
    except ValueError:
        print("\nNumbers only allowed.\n")
        return

    if child_choice == 0:
        return

    if (
        child_choice < 1
        or child_choice > len(children)
    ):
        print("\nInvalid child selection.\n")
        return

    selected_child = children[child_choice - 1]

    student_number = selected_child["student_number"]

    # ---------------------------------------------------------
    # GET TODAY'S DATE
    # ---------------------------------------------------------
    from datetime import date

    payment_date = date.today().isoformat()

    # ---------------------------------------------------------
    # FIND THE CURRENT SCHOOL TERM
    # ---------------------------------------------------------
    current_term = get_current_school_term_db()

    if current_term is None:
        print(
            "\nNo active school term was found.\n"
        )
        return

    school_year = current_term["school_year"]
    term_number = current_term["term_number"]

    # ---------------------------------------------------------
    # GET CURRENT FEE INFORMATION
    # ---------------------------------------------------------
    fee_status = get_student_total_fee_due_db(
        student_number,
        school_year,
        term_number
    )

    if fee_status is None:
        print(
            "\nUnable to retrieve the student's "
            "fee information.\n"
        )
        return

    remaining_balance = fee_status["remaining_balance"]

    # ---------------------------------------------------------
    # DISPLAY STUDENT INFORMATION
    # ---------------------------------------------------------
    print("\n===== MAKE FEE PAYMENT =====\n")

    print(
        "Student Number :",
        selected_child["student_number"]
    )
    print(
        "Name           :",
        selected_child["student_name"]
    )
    print(
        "Grade          :",
        selected_child["grade_name"]
    )
    print(
        "Class          :",
        selected_child["classroom"]
    )
    print(
        "School Year    :",
        school_year
    )
    print(
        "Current Term   :",
        term_number
    )
    print(
        "Payment Date   :",
        payment_date
    )

    print(
        f"\nOutstanding Balance : "
        f"R{remaining_balance:,.2f}"
    )

    # ---------------------------------------------------------
    # CHECK IF FEES ARE ALREADY PAID
    # ---------------------------------------------------------
    if remaining_balance <= 0:
        print(
            "\n✓ This student's fees are fully paid.\n"
        )
        return

    # ---------------------------------------------------------
    # ASK FOR PAYMENT AMOUNT
    # ---------------------------------------------------------
    try:
        amount = float(
            input("\nEnter payment amount: R")
        )
    except ValueError:
        print(
            "\nInvalid amount. "
            "Please enter numbers only.\n"
        )
        return

    # ---------------------------------------------------------
    # CHECK PAYMENT AMOUNT
    # ---------------------------------------------------------
    if amount <= 0:
        print(
            "\nPayment amount must be greater than zero.\n"
        )
        return

    if amount > remaining_balance:
        print(
            "\nPayment cannot be greater than "
            "the outstanding balance."
        )
        print(
            f"Outstanding Balance: "
            f"R{remaining_balance:,.2f}\n"
        )
        return

    # ---------------------------------------------------------
    # SHOW PAYMENT SUMMARY BEFORE SAVING
    # ---------------------------------------------------------
    print("\n===== PAYMENT SUMMARY =====\n")

    print(
        "Student       :",
        selected_child["student_name"]
    )
    print(
        "Student Number:",
        student_number
    )
    print(
        "School Year   :",
        school_year
    )
    print(
        "Term          :",
        term_number
    )
    print(
        "Payment Date  :",
        payment_date
    )
    print(
        f"Amount        : R{amount:,.2f}"
    )
    print(
        f"Balance Before: R{remaining_balance:,.2f}"
    )

    confirm = input(
        "\nConfirm this payment? (Y/N): "
    ).strip().upper()

    if confirm != "Y":
        print("\nPayment cancelled.\n")
        return

    # ---------------------------------------------------------
    # RECORD THE PAYMENT
    # ---------------------------------------------------------
    try:
        new_balance = record_fee_payment(
            student_number,
            amount,
            payment_date
        )

        print(
            "\n======================================"
        )
        print(
            "        PAYMENT SUCCESSFUL"
        )
        print(
            "======================================"
        )

        print(
            f"\nAmount Paid       : R{amount:,.2f}"
        )
        print(
            f"Previous Balance  : "
            f"R{remaining_balance:,.2f}"
        )
        print(
            f"New Overall Balance: "
            f"R{new_balance:,.2f}"
        )

        print(
            "\nPayment has been recorded successfully."
        )
        print(
            "======================================\n"
        )

    except ValueError as error:
        print(
            f"\nPayment failed: {error}\n"
        )

    except Exception as error:
        print(
            f"\nAn unexpected error occurred: {error}\n"
        )


def view_guardian_child_payment_history(guardian_id):
    """
    Allow a guardian to select one of their children
    and view that child's complete fee payment history.

    The actual payment records are retrieved by the existing
    get_payment_history_db() function.
    """

    # ---------------------------------------------------------
    # GET THE GUARDIAN'S CHILDREN
    # ---------------------------------------------------------
    children = get_guardian_children_db(guardian_id)

    if not children:
        print(
            "\nNo students are currently linked "
            "to your account.\n"
        )
        return

    # ---------------------------------------------------------
    # LET THE GUARDIAN CHOOSE A CHILD
    # ---------------------------------------------------------
    print("\n===== SELECT YOUR CHILD =====\n")

    for number, child in enumerate(children, start=1):
        print(
            f"{number}. "
            f"{child['student_name']} "
            f"({child['student_number']})"
        )

    print("0. Back to Guardian Panel")

    try:
        child_choice = int(
            input("\nChoose your child: ")
        )
    except ValueError:
        print("\nNumbers only allowed.\n")
        return

    if child_choice == 0:
        return

    if (
        child_choice < 1
        or child_choice > len(children)
    ):
        print("\nInvalid child selection.\n")
        return

    # ---------------------------------------------------------
    # GET THE SELECTED CHILD
    # ---------------------------------------------------------
    selected_child = children[child_choice - 1]

    student_number = selected_child["student_number"]

    # ---------------------------------------------------------
    # GET PAYMENT HISTORY
    # ---------------------------------------------------------
    payments = get_payment_history_db(
        student_number
    )

    # ---------------------------------------------------------
    # DISPLAY STUDENT INFORMATION
    # ---------------------------------------------------------
    print("\n===== CHILD PAYMENT HISTORY =====\n")

    print(
        "Student Number :",
        selected_child["student_number"]
    )
    print(
        "Name           :",
        selected_child["student_name"]
    )
    print(
        "Grade          :",
        selected_child["grade_name"]
    )
    print(
        "Class          :",
        selected_child["classroom"]
    )

    print(
        "\n---------------------------------------------"
    )

    # ---------------------------------------------------------
    # CHECK WHETHER THE STUDENT HAS PAYMENTS
    # ---------------------------------------------------------
    if not payments:
        print(
            "\nNo payment history found "
            "for this student.\n"
        )
        return

    # ---------------------------------------------------------
    # DISPLAY PAYMENT HISTORY
    # ---------------------------------------------------------
    print("\n===== PAYMENT RECORDS =====\n")

    total_paid = 0

    for payment in payments:

        payment_id = payment[0]
        student_number = payment[1]
        amount = payment[2]
        payment_date = payment[3]
        school_year = payment[4]
        term_number = payment[5]

        print(
            f"Payment ID   : {payment_id}"
        )
        print(
            f"Payment Date : {payment_date}"
        )
        print(
            f"School Year  : {school_year}"
        )
        print(
            f"Term         : {term_number}"
        )
        print(
            f"Amount Paid  : R{amount:,.2f}"
        )

        print(
            "---------------------------------------------"
        )

        # Add this payment to the running total.
        total_paid += amount

    # ---------------------------------------------------------
    # DISPLAY TOTAL PAID
    # ---------------------------------------------------------
    print(
        f"\nTotal Paid : R{total_paid:,.2f}"
    )

    print(
        "\nEnd of payment history.\n"
    )



def change_guardian_password_db(
    guardian_id,
    current_password,
    new_password
):
    """
    Change a Guardian's password.

    This function:
    1. Finds the Guardian account.
    2. Checks whether the account is locked.
    3. Verifies the current password.
    4. Creates a new random salt.
    5. Creates a new SHA-256 password hash.
    6. Saves the new hash and salt.
    """

    # ---------------------------------------------------------
    # OPEN DATABASE CONNECTION
    # ---------------------------------------------------------
    connection = get_connection()

    # Use sqlite3.Row so we can access columns by name.
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    try:

        # -----------------------------------------------------
        # GET THE GUARDIAN'S CURRENT PASSWORD INFORMATION
        # -----------------------------------------------------
        cursor.execute("""
            SELECT
                guardian_id,
                password_hash,
                password_salt,
                status
            FROM guardians
            WHERE guardian_id = ?
        """, (guardian_id,))

        guardian = cursor.fetchone()

        # -----------------------------------------------------
        # CHECK WHETHER THE GUARDIAN EXISTS
        # -----------------------------------------------------
        if guardian is None:
            return False, "Guardian not found."

        # -----------------------------------------------------
        # CHECK WHETHER THE ACCOUNT IS LOCKED
        # -----------------------------------------------------
        if guardian["status"] == "locked":
            return False, (
                "Your account is locked. "
                "Contact the School."
            )

        # -----------------------------------------------------
        # VERIFY THE CURRENT PASSWORD
        # -----------------------------------------------------

        # Convert the stored hexadecimal salt back
        # into bytes.
        current_salt = bytes.fromhex(
            guardian["password_salt"]
        )

        # Create a hash from the password entered
        # by the Guardian.
        current_password_hash = hashlib.sha256(
            current_password.encode() + current_salt
        ).hexdigest()

        # Compare the newly calculated hash with
        # the hash stored in the database.
        if current_password_hash != guardian["password_hash"]:
            return False, "Current password is incorrect."

        # -----------------------------------------------------
        # CHECK THE NEW PASSWORD
        # -----------------------------------------------------

        if not new_password:
            return False, "New password cannot be empty."

        # -----------------------------------------------------
        # CREATE A NEW RANDOM SALT
        # -----------------------------------------------------

        # Each new password receives a new random salt.
        new_salt = secrets.token_bytes(16)

        # -----------------------------------------------------
        # CREATE THE NEW PASSWORD HASH
        # -----------------------------------------------------

        new_password_hash = hashlib.sha256(
            new_password.encode() + new_salt
        ).hexdigest()

        # Convert the new salt to hexadecimal so it can
        # be stored in the TEXT password_salt column.
        new_password_salt = new_salt.hex()

        # -----------------------------------------------------
        # SAVE THE NEW PASSWORD
        # -----------------------------------------------------
        cursor.execute("""
            UPDATE guardians
            SET
                password_hash = ?,
                password_salt = ?,
                failed_attempts = 0
            WHERE guardian_id = ?
        """, (
            new_password_hash,
            new_password_salt,
            guardian_id
        ))

        # -----------------------------------------------------
        # SAVE THE DATABASE CHANGES
        # -----------------------------------------------------
        connection.commit()

        return True, "Password changed successfully."

    except Exception as error:

        # If something goes wrong, undo any changes.
        connection.rollback()

        return False, (
            f"Unable to change password: {error}"
        )

    finally:

        # Always close the database connection.
        connection.close()
        
        
        
        
        
def change_guardian_password(guardian_id):
    """
    Allow a Guardian to change their password.

    The Guardian must enter:
    1. Their current password.
    2. Their new password.
    3. Their new password again for confirmation.

    The actual database update is handled by
    change_guardian_password_db().
    """

    print("\n===== CHANGE YOUR PASSWORD =====\n")

    # ---------------------------------------------------------
    # ASK FOR THE CURRENT PASSWORD
    # ---------------------------------------------------------
    current_password = input(
        "Enter current password: "
    )

    # ---------------------------------------------------------
    # ASK FOR THE NEW PASSWORD
    # ---------------------------------------------------------
    new_password = input(
        "Enter new password: "
    )

    # ---------------------------------------------------------
    # CONFIRM THE NEW PASSWORD
    # ---------------------------------------------------------
    confirm_password = input(
        "Confirm new password: "
    )

    # ---------------------------------------------------------
    # CHECK WHETHER THE NEW PASSWORDS MATCH
    # ---------------------------------------------------------
    if new_password != confirm_password:
        print(
            "\nNew passwords do not match.\n"
        )
        return

    # ---------------------------------------------------------
    # MAKE SURE THE NEW PASSWORD IS NOT EMPTY
    # ---------------------------------------------------------
    if not new_password:
        print(
            "\nNew password cannot be empty.\n"
        )
        return

    # ---------------------------------------------------------
    # CHANGE THE PASSWORD IN THE DATABASE
    # ---------------------------------------------------------
    success, message = change_guardian_password_db(
        guardian_id,
        current_password,
        new_password
    )

    # ---------------------------------------------------------
    # DISPLAY THE RESULT
    # ---------------------------------------------------------
    if success:
        print(
            "\n======================================"
        )
        print(
            "       PASSWORD CHANGED SUCCESSFULLY"
        )
        print(
            "======================================"
        )
        print(
            "\nYour password has been updated."
        )
        print(
            "Please use your new password the next "
            "time you log in.\n"
        )

    else:
        print(
            f"\nPassword change failed: {message}\n"
        )




def get_guardian_child_submitted_homework_db(student_number):
    """
    Get homework that a specific student has submitted.

    IMPORTANT:
    A homework assignment is considered submitted when
    a record exists in homework_submissions.

    This function returns only homework where a submission
    record exists for the selected student.
    """

    # ---------------------------------------------------------
    # OPEN DATABASE CONNECTION
    # ---------------------------------------------------------
    connection = get_connection()

    # Use Row objects so we can access columns by name.
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    try:

        # -----------------------------------------------------
        # GET SUBMITTED HOMEWORK
        # -----------------------------------------------------
        cursor.execute("""
            SELECT
                h.homework_id,
                h.title,
                h.description,
                h.due_date,
                h.date_posted,

                s.subject_name,

                t.teacher_name,

                g.grade_name,

                hs.submission_id,
                hs.submitted_date,
                hs.status AS submission_status,
                hs.mark,
                hs.total_possible,
                hs.marked_date,

                marker.teacher_name AS marked_by

            FROM homework_submissions hs

            JOIN homework h
                ON h.homework_id = hs.homework_id

            JOIN students st
                ON st.student_number = hs.student_number

            JOIN subjects s
                ON s.subject_id = h.subject_id

            JOIN student_subjects ss
                ON ss.student_number = st.student_number
                AND ss.subject_name = s.subject_name

            JOIN grades g
                ON g.grade_id = h.grade_id
                AND g.grade_id = st.grade_id

            JOIN teachers t
                ON t.teacher_number = h.teacher_number

            LEFT JOIN teachers marker
                ON marker.teacher_number = hs.teacher_number

            WHERE hs.student_number = ?

            ORDER BY
                hs.submitted_date DESC,
                hs.submission_id DESC

        """, (student_number,))

        # Get all submitted homework records.
        homework = cursor.fetchall()

        # Convert SQLite Row objects into dictionaries.
        return [dict(item) for item in homework]

    except Exception as error:

        print(
            f"\nError getting submitted homework: "
            f"{error}"
        )

        return []

    finally:

        # Always close the database connection.
        connection.close()
        
        
        

def view_guardian_child_submitted_homework(guardian_id):
    """
    Allow a guardian to select one of their children
    and view homework that the child has submitted.
    """

    # ---------------------------------------------------------
    # GET THE GUARDIAN'S CHILDREN
    # ---------------------------------------------------------
    children = get_guardian_children_db(guardian_id)

    if not children:
        print(
            "\nNo students are currently linked "
            "to your account.\n"
        )
        return

    # ---------------------------------------------------------
    # LET THE GUARDIAN CHOOSE A CHILD
    # ---------------------------------------------------------
    print("\n===== SELECT YOUR CHILD =====\n")

    for number, child in enumerate(children, start=1):
        print(
            f"{number}. "
            f"{child['student_name']} "
            f"({child['student_number']})"
        )

    print("0. Back to Guardian Panel")

    try:
        child_choice = int(
            input("\nChoose your child: ")
        )

    except ValueError:
        print("\nNumbers only allowed.\n")
        return

    if child_choice == 0:
        return

    if (
        child_choice < 1
        or child_choice > len(children)
    ):
        print("\nInvalid child selection.\n")
        return

    # ---------------------------------------------------------
    # GET THE SELECTED CHILD
    # ---------------------------------------------------------
    selected_child = children[child_choice - 1]

    student_number = selected_child["student_number"]

    # ---------------------------------------------------------
    # GET SUBMITTED HOMEWORK
    # ---------------------------------------------------------
    submitted_homework = (
        get_guardian_child_submitted_homework_db(
            student_number
        )
    )

    # ---------------------------------------------------------
    # DISPLAY CHILD INFORMATION
    # ---------------------------------------------------------
    print(
        "\n===== SUBMITTED HOMEWORK =====\n"
    )

    print(
        "Student Number :",
        selected_child["student_number"]
    )

    print(
        "Name           :",
        selected_child["student_name"]
    )

    print(
        "Grade          :",
        selected_child["grade_name"]
    )

    print(
        "Class          :",
        selected_child["classroom"]
    )

    print(
        "\n---------------------------------------------"
    )

    # ---------------------------------------------------------
    # CHECK WHETHER ANY HOMEWORK WAS SUBMITTED
    # ---------------------------------------------------------
    if not submitted_homework:

        print(
            "\nThis student has not submitted "
            "any homework yet.\n"
        )

        return

    # ---------------------------------------------------------
    # DISPLAY EACH SUBMISSION
    # ---------------------------------------------------------
    for homework in submitted_homework:

        print("\n===== SUBMISSION =====")

        print(
            "Homework ID   :",
            homework["homework_id"]
        )

        print(
            "Title         :",
            homework["title"]
        )

        print(
            "Subject       :",
            homework["subject_name"]
        )

        print(
            "Teacher       :",
            homework["teacher_name"]
        )

        print(
            "Date Posted   :",
            homework["date_posted"]
        )

        print(
            "Due Date      :",
            homework["due_date"]
        )

        print(
            "Submitted     :",
            homework["submitted_date"]
        )

        print(
            "Status        :",
            homework["submission_status"]
        )

        # -----------------------------------------------------
        # CHECK WHETHER THE TEACHER HAS MARKED IT
        # -----------------------------------------------------
        if homework["mark"] is not None:

            print(
                "Mark          :",
                f"{homework['mark']:.1f}"
            )

            if homework["total_possible"] is not None:

                print(
                    "Total Possible:",
                    f"{homework['total_possible']:.1f}"
                )

        else:

            print(
                "Mark          : Not marked yet"
            )

        # -----------------------------------------------------
        # SHOW MARKING INFORMATION
        # -----------------------------------------------------
        if homework["marked_date"] is not None:

            print(
                "Marked Date   :",
                homework["marked_date"]
            )

        else:

            print(
                "Marked Date   : Not marked yet"
            )

        if homework["marked_by"] is not None:

            print(
                "Marked By     :",
                homework["marked_by"]
            )

        else:

            print(
                "Marked By     : Not marked yet"
            )

        print(
            "---------------------------------------------"
        )

    print(
        "\nEnd of submitted homework.\n"
    )
    
    
    
# ----------------------------------------------------------
# ADD STUDENT DOCUMENT TO DATABASE
# ----------------------------------------------------------
# This function records an official school document that
# has been uploaded for a student.
#
# The actual PDF file is stored inside the
# "student_documents" folder.
#
# The database stores the information ABOUT the PDF:
#
# - document_id
# - student_number
# - document_title
# - document_type
# - file_path
# - uploaded_date
# - admin_id
#
# A student can have many documents.
#
# For example:
#
# Student 1000064
#     ├── Term 1 Report
#     ├── Term 2 Report
#     ├── Parents Circular
#     └── Academic Notice
#
# The admin_id allows us to know which administrator
# uploaded the document.
# ----------------------------------------------------------

def add_student_document_db(
    student_number,
    document_title,
    document_type,
    file_path,
    uploaded_date,
    admin_id
):
    """
    Saves information about an uploaded student document
    into the student_documents table.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # --------------------------------------------------
        # First check that the student actually exists.
        # --------------------------------------------------
        cursor.execute("""
            SELECT student_number
            FROM students
            WHERE student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

        if student is None:
            print("\nStudent not found.")
            return False

        # --------------------------------------------------
        # Insert the document information into the database.
        # --------------------------------------------------
        cursor.execute("""
            INSERT INTO student_documents (
                student_number,
                document_title,
                document_type,
                file_path,
                uploaded_date,
                admin_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student_number,
            document_title,
            document_type,
            file_path,
            uploaded_date,
            admin_id
        ))

        # --------------------------------------------------
        # Save the changes permanently.
        # --------------------------------------------------
        connection.commit()

        print("\nStudent document added successfully.")

        return True

    except Exception as error:

        # --------------------------------------------------
        # If something goes wrong, undo any changes that
        # may have been made during this operation.
        # --------------------------------------------------
        connection.rollback()

        print(f"\nError adding student document: {error}")

        return False

    finally:

        # --------------------------------------------------
        # Always close the database connection.
        # --------------------------------------------------
        connection.close()    




# ----------------------------------------------------------
# SAVE STUDENT PDF DOCUMENT
# ----------------------------------------------------------
# This function saves an official school PDF document
# uploaded by an administrator.
#
# The PDF selected by the administrator may be anywhere
# on the computer.
#
# This function copies that PDF into our school's
# "student_documents" storage folder.
#
# Each student gets their own folder.
#
# Example:
#
# student_documents/
#     ├── 1000064/
#     │      ├── 1000064_20260923_143522_a81f.pdf
#     │      └── 1000064_20260923_143701_b42c.pdf
#     │
#     └── 1000053/
#            └── 1000053_20260923_144010_c91d.pdf
#
# A unique filename is generated for every document.
# This prevents a new PDF from accidentally replacing
# an older PDF with the same name.
#
# IMPORTANT:
# This function only saves the physical PDF file.
# The database information will be saved separately using
# add_student_document_db().
# ----------------------------------------------------------

def save_student_pdf(student_number, source_file_path):
    """
    Copies a PDF selected by the administrator into the
    correct student's document folder.

    Returns:
        saved_file_path  -> if successful
        None             -> if unsuccessful
    """

    try:

        # --------------------------------------------------
        # Main folder where all student documents are stored.
        # --------------------------------------------------
        main_documents_folder = "student_documents"

        # --------------------------------------------------
        # Create the main folder if it does not already exist.
        #
        # exist_ok=True means Python will not give an error
        # if the folder already exists.
        # --------------------------------------------------
        os.makedirs(main_documents_folder, exist_ok=True)

        # --------------------------------------------------
        # Create a folder specifically for this student.
        #
        # Example:
        # student_documents/1000064/
        # --------------------------------------------------
        student_folder = os.path.join(
            main_documents_folder,
            str(student_number)
        )

        os.makedirs(student_folder, exist_ok=True)

        # --------------------------------------------------
        # Make sure the selected file is actually a PDF.
        # --------------------------------------------------
        if not source_file_path.lower().endswith(".pdf"):
            print("\nOnly PDF files are allowed.")
            return None

        # --------------------------------------------------
        # Make sure the source file actually exists.
        # --------------------------------------------------
        if not os.path.isfile(source_file_path):
            print("\nThe selected PDF file was not found.")
            return None

        # --------------------------------------------------
        # Get the current date and time.
        #
        # Example:
        # 20260923_143522
        # --------------------------------------------------
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # --------------------------------------------------
        # Generate a random value.
        #
        # This gives the filename another layer of uniqueness
        # in case two files are uploaded within the same
        # second.
        # --------------------------------------------------
        unique_code = secrets.token_hex(4)

        # --------------------------------------------------
        # Create the new filename.
        #
        # Example:
        # 1000064_20260923_143522_a81f3c2d.pdf
        # --------------------------------------------------
        new_filename = (
            f"{student_number}_"
            f"{timestamp}_"
            f"{unique_code}.pdf"
        )

        # --------------------------------------------------
        # Create the complete destination path.
        # --------------------------------------------------
        destination_path = os.path.join(
            student_folder,
            new_filename
        )

        # --------------------------------------------------
        # Copy the PDF into the student's folder.
        #
        # copy2() copies the file and also preserves useful
        # file metadata.
        # --------------------------------------------------
        shutil.copy2(
            source_file_path,
            destination_path
        )

        print("\nPDF uploaded successfully.")
        print(f"Saved to: {destination_path}")

        # --------------------------------------------------
        # Return the path.
        #
        # The Admin upload function will later give this path
        # to add_student_document_db() so that SQLite knows
        # where the PDF is stored.
        # --------------------------------------------------
        return destination_path

    except Exception as error:

        print(f"\nError saving student PDF: {error}")

        return None



# ----------------------------------------------------------
# SELECT STUDENT DOCUMENT PDF FROM ANDROID PHONE
# ----------------------------------------------------------
# This function opens the Android file picker and allows
# the administrator to select an official student PDF.
#
# This function is separate from the homework PDF picker.
#
# The selected PDF is temporarily copied to:
#
# selected_student_document.pdf
#
# After selection, the upload system copies the PDF into
# the student's permanent document folder.
# ----------------------------------------------------------

def select_student_document_from_android():
    """
    Opens the Android file picker and allows the
    administrator to select a student document PDF.

    Returns:
        The selected PDF path if successful.
        None if no PDF was selected or an error occurred.
    """

    import os
    import subprocess
    import time

    # ----------------------------------------------------------
    # USE A SIMPLE RELATIVE FILE PATH
    # ----------------------------------------------------------
    # This avoids the DatabasseLessons/DataBasseLessons
    # spelling difference between Termux and Android.
    selected_pdf = "selected_student_document.pdf"

    print("\nOpening Android file picker...")
    print("Please select the student's PDF document.")
    

    try:

        # --------------------------------------------------
        # Remove an old temporary PDF.
        #
        # This is important because we only want to accept
        # the PDF selected during this upload.
        # --------------------------------------------------

        if os.path.exists(selected_pdf):
            os.remove(selected_pdf)

        # --------------------------------------------------
        # Launch Android's file picker.
        #
        # We use subprocess.run() and wait for the command
        # to finish before continuing.
        # --------------------------------------------------

        result = subprocess.run(
            [
                "termux-storage-get",
                selected_pdf
            ],
            check=False
        )

        # --------------------------------------------------
        # Display the command result.
        #
        # Return code 0 normally means that the command
        # completed successfully.
        # --------------------------------------------------

        print(f"\nFile picker finished.")
        print(f"Picker return code: {result.returncode}")
        

        # --------------------------------------------------
        # Give the Android system a short amount of time
        # to finish writing the selected PDF.
        # --------------------------------------------------

        for _ in range(20):

            if os.path.isfile(selected_pdf):
                break

            time.sleep(0.5)

        # --------------------------------------------------
        # Check whether the PDF was actually created.
        # --------------------------------------------------

        if not os.path.isfile(selected_pdf):

            print("\nNo PDF document was selected.")
            return None

        # --------------------------------------------------
        # Confirm that the selected file is a PDF.
        # --------------------------------------------------

        if not selected_pdf.lower().endswith(".pdf"):

            print("\nOnly PDF files are allowed.")

            os.remove(selected_pdf)

            return None

        # --------------------------------------------------
        # Confirm successful selection.
        # --------------------------------------------------

        print("\nPDF document selected successfully.")
        print(f"Selected file: {selected_pdf}")

        return selected_pdf

    except Exception as error:

        print(
            f"\nError opening the Android file picker: {error}"
        )

        return None




# ----------------------------------------------------------
# UPLOAD STUDENT DOCUMENT
# ----------------------------------------------------------
# This function handles the STORAGE and DATABASE part of
# uploading an official student PDF.
#
# IMPORTANT:
#
# This function does NOT open the Android file picker.
#
# The Android file picker has its own separate function:
#
#     select_student_document_from_android()
#
# The Admin interface will first select the PDF and then
# pass the selected PDF path to this function.
#
# The process is:
#
# 1. Check that the student exists.
# 2. Check that the selected PDF exists.
# 3. Copy the PDF into permanent student storage.
# 4. Save the document information into SQLite.
#
# This separation keeps the file-picker system independent
# from the database/storage system.
# ----------------------------------------------------------

def upload_student_document_db(
    student_number,
    document_title,
    document_type,
    admin_id,
    selected_pdf,
    term_number=None
):
    """
    Saves a selected student PDF into permanent storage
    and records it in the database.

    Term numbers are used only for:

        Report Card     -> Term 1, 2, 3 or 4
        Progress Report -> Term 1, 2, 3 or 4

    These documents do NOT use a term number:

        Circular
        Notice
        Other
    """

    # ------------------------------------------------------
    # STEP 1
    # Check that the student exists.
    # ------------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT student_number
            FROM students
            WHERE student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

    finally:

        connection.close()

    if student is None:

        print("\nStudent not found.")

        return False

    # ------------------------------------------------------
    # STEP 2
    # Check that a PDF was selected.
    # ------------------------------------------------------

    if selected_pdf is None:

        print("\nNo PDF was provided.")

        return False

    # ------------------------------------------------------
    # STEP 3
    # Check that the selected PDF exists.
    # ------------------------------------------------------

    if not os.path.isfile(selected_pdf):

        print("\nThe selected PDF file was not found.")

        print("File path:")
        print(selected_pdf)

        return False

    # ------------------------------------------------------
    # STEP 4
    # Only PDF files are allowed.
    # ------------------------------------------------------

    if not selected_pdf.lower().endswith(".pdf"):

        print("\nOnly PDF files are allowed.")

        return False

    print("\nSelected PDF confirmed.")
    print(f"Source file: {selected_pdf}")

    # ------------------------------------------------------
    # STEP 5
    # Copy the PDF into permanent student storage.
    # ------------------------------------------------------

    saved_file_path = save_student_pdf(
        student_number,
        selected_pdf
    )

    if saved_file_path is None:

        print("\nThe PDF could not be saved.")

        return False

    # ------------------------------------------------------
    # STEP 6
    # Get today's date.
    # ------------------------------------------------------

    uploaded_date = datetime.now().strftime("%Y-%m-%d")

    # ------------------------------------------------------
    # STEP 7
    # Save the document information into SQLite.
    # ------------------------------------------------------

    success = add_student_document_db(
        student_number,
        document_title,
        document_type,
        saved_file_path,
        uploaded_date,
        admin_id,
        term_number
    )

    # ------------------------------------------------------
    # STEP 8
    # If the database record failed,
    # remove the copied PDF.
    # ------------------------------------------------------

    if not success:

        try:

            if os.path.exists(saved_file_path):

                os.remove(saved_file_path)

            print("\nThe copied PDF was removed.")

        except Exception as error:

            print(
                f"\nWarning: Could not remove copied PDF: "
                f"{error}"
            )

        return False

    # ------------------------------------------------------
    # STEP 9
    # Show successful upload information.
    # ------------------------------------------------------

    print("\n==========================================")
    print(" STUDENT DOCUMENT UPLOAD COMPLETE")
    print("==========================================")

    print(
        f"Student number : {student_number}"
    )

    print(
        f"Document title : {document_title}"
    )

    print(
        f"Document type  : {document_type}"
    )

    if term_number is not None:

        print(
            f"Term           : {term_number}"
        )

    else:

        print(
            "Term           : Not applicable"
        )

    print(
        f"Saved file     : {saved_file_path}"
    )

    print("==========================================")

    return True




# ----------------------------------------------------------
# ADD STUDENT DOCUMENT TO DATABASE
# ----------------------------------------------------------
def add_student_document_db(
    student_number,
    document_title,
    document_type,
    file_path,
    uploaded_date,
    admin_id,
    term_number=None
):
    """
    Saves an uploaded student document into the
    student_documents table.

    term_number is used for:

        Report Card     -> Term 1, 2, 3 or 4
        Progress Report -> Term 1, 2, 3 or 4

    term_number is NULL for:

        Circular
        Notice
        Other
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # --------------------------------------------------
        # CHECK THAT THE STUDENT EXISTS
        # --------------------------------------------------

        cursor.execute("""
            SELECT student_number
            FROM students
            WHERE student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

        if student is None:

            print("\nStudent not found.")

            return False

        # --------------------------------------------------
        # INSERT THE DOCUMENT
        # --------------------------------------------------

        cursor.execute("""
            INSERT INTO student_documents (
                student_number,
                document_title,
                document_type,
                file_path,
                uploaded_date,
                admin_id,
                term_number
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            student_number,
            document_title,
            document_type,
            file_path,
            uploaded_date,
            admin_id,
            term_number
        ))

        # --------------------------------------------------
        # SAVE THE DATABASE CHANGE
        # --------------------------------------------------

        connection.commit()

        print(
            "\nStudent document added successfully."
        )

        return True

    except Exception as error:

        # --------------------------------------------------
        # CANCEL THE DATABASE CHANGE IF AN ERROR OCCURS
        # --------------------------------------------------

        connection.rollback()

        print(
            f"\nError adding student document: {error}"
        )

        return False

    finally:

        # --------------------------------------------------
        # ALWAYS CLOSE THE DATABASE CONNECTION
        # --------------------------------------------------

        connection.close()




# ----------------------------------------------------------
# GET STUDENT DOCUMENTS
# ----------------------------------------------------------
def get_student_documents_db(student_number):
    """
    Gets all documents belonging to a specific student.

    The function returns:

        document_id
        document_title
        document_type
        file_path
        uploaded_date
        term_number

    term_number will be:

        1, 2, 3 or 4
        for Report Cards and Progress Reports

        None
        for Circulars, Notices and Other documents.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # --------------------------------------------------
        # GET ALL DOCUMENTS FOR THIS STUDENT
        # --------------------------------------------------

        cursor.execute("""
            SELECT
                document_id,
                document_title,
                document_type,
                file_path,
                uploaded_date,
                term_number
            FROM student_documents
            WHERE student_number = ?
            ORDER BY uploaded_date DESC, document_id DESC
        """, (student_number,))

        documents = cursor.fetchall()

        return documents

    except Exception as error:

        print(
            f"\nError getting student documents: {error}"
        )

        return []

    finally:

        # --------------------------------------------------
        # ALWAYS CLOSE THE DATABASE CONNECTION
        # --------------------------------------------------

        connection.close()



# ----------------------------------------------------------
# STUDENT SCHOOL DOCUMENTS MENU
# ----------------------------------------------------------
def student_school_documents_menu(student_number):
    """
    Allows a student to view and open school documents.

    Documents available:

        1. Report Card
           - Term 1
           - Term 2
           - Term 3
           - Term 4

        2. Current School Circular
           - Latest circular only

        3. Progress Report
           - Term 1
           - Term 2
           - Term 3
           - Term 4

        4. Other Documents
           - Notices
           - Other documents

    Fee rules:

        Report Card     -> Fees must be fully paid
        Progress Report -> Fees must be fully paid

        Circular       -> No fee restriction
        Notice         -> No fee restriction
        Other          -> No fee restriction
    """

    # ------------------------------------------------------
    # IMPORTS USED BY THIS FUNCTION
    # ------------------------------------------------------

    import os
    import subprocess


    # ------------------------------------------------------
    # GET ALL DOCUMENTS BELONGING TO THIS STUDENT
    # ------------------------------------------------------

    documents = get_student_documents_db(
        student_number
    )


    # ------------------------------------------------------
    # MAIN SCHOOL DOCUMENT MENU
    # ------------------------------------------------------

    while True:

        print("\n==========================================")
        print("           SCHOOL DOCUMENTS")
        print("==========================================")

        print(
            "1. View and Download Your Report Card"
        )

        print(
            "2. View and Download Current School Circular"
        )

        print(
            "3. View and Download Progress Report"
        )

        print(
            "4. View and Download Other Documents"
        )

        print(
            "5. Back"
        )

        print("==========================================")


        choice = input(
            "\nSelect option: "
        ).strip()


        # ======================================================
        # OPTION 1 - REPORT CARD
        # ======================================================

        if choice == "1":

            # --------------------------------------------------
            # CHECK CURRENT SCHOOL TERM
            # --------------------------------------------------

            current_school_term = get_current_school_term_db()

            if current_school_term is None:

                print(
                    "\nThe current school term could not be found."
                )

                input(
                    "\nPress Enter to continue..."
                )

                continue


            # --------------------------------------------------
            # GET CURRENT SCHOOL YEAR AND TERM
            # --------------------------------------------------

            school_year = current_school_term[
                "school_year"
            ]

            current_term = current_school_term[
                "term_number"
            ]


            # --------------------------------------------------
            # CHECK WHETHER THE STUDENT HAS FULLY PAID FEES
            # --------------------------------------------------

            fee_status = get_student_total_fee_due_db(
                student_number,
                school_year,
                current_term
            )


            if fee_status is None:

                print(
                    "\nUnable to check your fee status."
                )

                input(
                    "\nPress Enter to continue..."
                )

                continue


            remaining_balance = float(
                fee_status["remaining_balance"]
            )


            # --------------------------------------------------
            # LOCK REPORT CARD IF FEES ARE NOT FULLY PAID
            # --------------------------------------------------

            if remaining_balance > 0:

                print("\n==========================================")
                print("          REPORT CARD LOCKED")
                print("==========================================")

                print(
                    "\nYour report card is currently locked."
                )

                print(
                    f"Outstanding balance: "
                    f"R{remaining_balance:.2f}"
                )

                print(
                    "\nPlease settle your school fees "
                    "before accessing your report card."
                )

                print("==========================================")

                input(
                    "\nPress Enter to continue..."
                )

                continue


            # --------------------------------------------------
            # FEES ARE FULLY PAID
            # --------------------------------------------------

            while True:

                print("\n==========================================")
                print("             REPORT CARD")
                print("==========================================")

                print("1. Term 1")
                print("2. Term 2")
                print("3. Term 3")
                print("4. Term 4")
                print("5. Back")

                term_choice = input(
                    "\nSelect term: "
                ).strip()


                if term_choice == "5":

                    break


                if term_choice not in (
                    "1",
                    "2",
                    "3",
                    "4"
                ):

                    print(
                        "\nInvalid term."
                    )

                    continue


                selected_term = int(
                    term_choice
                )


                # --------------------------------------------------
                # FIND THE REPORT CARD FOR THE SELECTED TERM
                # --------------------------------------------------

                matching_documents = []

                for document in documents:

                    if (
                        document["document_type"] == "Report"
                        and document["term_number"]
                        == selected_term
                    ):

                        matching_documents.append(
                            document
                        )


                # --------------------------------------------------
                # CHECK WHETHER A REPORT CARD EXISTS
                # --------------------------------------------------

                if not matching_documents:

                    print(
                        f"\nNo report card is available "
                        f"for Term {selected_term}."
                    )

                    input(
                        "\nPress Enter to continue..."
                    )

                    continue


                # --------------------------------------------------
                # USE THE MOST RECENT REPORT CARD
                # --------------------------------------------------

                document = matching_documents[0]


                print("\n==========================================")
                print("           REPORT CARD FOUND")
                print("==========================================")

                print(
                    f"Title : "
                    f"{document['document_title']}"
                )

                print(
                    f"Term  : "
                    f"{document['term_number']}"
                )

                print(
                    f"Date  : "
                    f"{document['uploaded_date']}"
                )

                print("==========================================")


                # --------------------------------------------------
                # CHECK THAT THE PDF STILL EXISTS
                # --------------------------------------------------

                if not os.path.isfile(
                    document["file_path"]
                ):

                    print(
                        "\nThe report card PDF could not "
                        "be found in storage."
                    )

                    input(
                        "\nPress Enter to continue..."
                    )

                    continue


                # --------------------------------------------------
                # OPEN THE REPORT CARD
                # --------------------------------------------------

                try:

                    subprocess.run(
                        [
                            "termux-open",
                            document["file_path"]
                        ],
                        check=False
                    )

                    print(
                        "\nOpening report card..."
                    )

                except Exception as error:

                    print(
                        f"\nCould not open the report card: "
                        f"{error}"
                    )


                input(
                    "\nPress Enter to continue..."
                )


        # ======================================================
        # OPTION 2 - CURRENT SCHOOL CIRCULAR
        # ======================================================

        elif choice == "2":

            # --------------------------------------------------
            # FIND CIRCULARS FOR THIS STUDENT
            # --------------------------------------------------

            circulars = []

            for document in documents:

                if document["document_type"] == "Circular":

                    circulars.append(
                        document
                    )


            # --------------------------------------------------
            # CHECK WHETHER A CIRCULAR EXISTS
            # --------------------------------------------------

            if not circulars:

                print(
                    "\nThere is currently no school circular "
                    "available."
                )

                input(
                    "\nPress Enter to continue..."
                )

                continue


            # --------------------------------------------------
            # THE FIRST ONE IS THE CURRENT/LATEST CIRCULAR
            #
            # get_student_documents_db() sorts newest first.
            # --------------------------------------------------

            current_circular = circulars[0]


            print("\n==========================================")
            print("        CURRENT SCHOOL CIRCULAR")
            print("==========================================")

            print(
                f"Title : "
                f"{current_circular['document_title']}"
            )

            print(
                f"Date  : "
                f"{current_circular['uploaded_date']}"
            )

            print("==========================================")


            # --------------------------------------------------
            # CHECK THAT THE PDF STILL EXISTS
            # --------------------------------------------------

            if not os.path.isfile(
                current_circular["file_path"]
            ):

                print(
                    "\nThe circular PDF could not be "
                    "found in storage."
                )

                input(
                    "\nPress Enter to continue..."
                )

                continue


            # --------------------------------------------------
            # OPEN CURRENT CIRCULAR
            # --------------------------------------------------

            try:

                subprocess.run(
                    [
                        "termux-open",
                        current_circular["file_path"]
                    ],
                    check=False
                )

                print(
                    "\nOpening current school circular..."
                )

            except Exception as error:

                print(
                    f"\nCould not open the circular: "
                    f"{error}"
                )


            input(
                "\nPress Enter to continue..."
            )


        # ======================================================
        # OPTION 3 - PROGRESS REPORT
        # ======================================================

        elif choice == "3":

            # --------------------------------------------------
            # CHECK CURRENT SCHOOL TERM
            # --------------------------------------------------

            current_school_term = get_current_school_term_db()

            if current_school_term is None:

                print(
                    "\nThe current school term could not be found."
                )

                input(
                    "\nPress Enter to continue..."
                )

                continue


            school_year = current_school_term[
                "school_year"
            ]

            current_term = current_school_term[
                "term_number"
            ]


            # --------------------------------------------------
            # CHECK WHETHER FEES ARE FULLY PAID
            # --------------------------------------------------

            fee_status = get_student_total_fee_due_db(
                student_number,
                school_year,
                current_term
            )


            if fee_status is None:

                print(
                    "\nUnable to check your fee status."
                )

                input(
                    "\nPress Enter to continue..."
                )

                continue


            remaining_balance = float(
                fee_status["remaining_balance"]
            )


            # --------------------------------------------------
            # LOCK PROGRESS REPORT IF MONEY IS OWED
            # --------------------------------------------------

            if remaining_balance > 0:

                print("\n==========================================")
                print("        PROGRESS REPORT LOCKED")
                print("==========================================")

                print(
                    "\nYour progress report is currently locked."
                )

                print(
                    f"Outstanding balance: "
                    f"R{remaining_balance:.2f}"
                )

                print(
                    "\nPlease settle your school fees "
                    "before accessing your progress report."
                )

                print("==========================================")

                input(
                    "\nPress Enter to continue..."
                )

                continue


            # --------------------------------------------------
            # FEES ARE FULLY PAID
            # --------------------------------------------------

            while True:

                print("\n==========================================")
                print("           PROGRESS REPORT")
                print("==========================================")

                print("1. Term 1")
                print("2. Term 2")
                print("3. Term 3")
                print("4. Term 4")
                print("5. Back")

                term_choice = input(
                    "\nSelect term: "
                ).strip()


                if term_choice == "5":

                    break


                if term_choice not in (
                    "1",
                    "2",
                    "3",
                    "4"
                ):

                    print(
                        "\nInvalid term."
                    )

                    continue


                selected_term = int(
                    term_choice
                )


                # --------------------------------------------------
                # FIND PROGRESS REPORT FOR SELECTED TERM
                # --------------------------------------------------

                matching_documents = []

                for document in documents:

                    if (
                        document["document_type"]
                        == "Progress Report"
                        and document["term_number"]
                        == selected_term
                    ):

                        matching_documents.append(
                            document
                        )


                # --------------------------------------------------
                # CHECK WHETHER A PROGRESS REPORT EXISTS
                # --------------------------------------------------

                if not matching_documents:

                    print(
                        f"\nNo progress report is available "
                        f"for Term {selected_term}."
                    )

                    input(
                        "\nPress Enter to continue..."
                    )

                    continue


                # --------------------------------------------------
                # USE THE MOST RECENT PROGRESS REPORT
                # --------------------------------------------------

                document = matching_documents[0]


                print("\n==========================================")
                print("        PROGRESS REPORT FOUND")
                print("==========================================")

                print(
                    f"Title : "
                    f"{document['document_title']}"
                )

                print(
                    f"Term  : "
                    f"{document['term_number']}"
                )

                print(
                    f"Date  : "
                    f"{document['uploaded_date']}"
                )

                print("==========================================")


                # --------------------------------------------------
                # CHECK THAT THE PDF STILL EXISTS
                # --------------------------------------------------

                if not os.path.isfile(
                    document["file_path"]
                ):

                    print(
                        "\nThe progress report PDF could "
                        "not be found in storage."
                    )

                    input(
                        "\nPress Enter to continue..."
                    )

                    continue


                # --------------------------------------------------
                # OPEN THE PROGRESS REPORT
                # --------------------------------------------------

                try:

                    subprocess.run(
                        [
                            "termux-open",
                            document["file_path"]
                        ],
                        check=False
                    )

                    print(
                        "\nOpening progress report..."
                    )

                except Exception as error:

                    print(
                        f"\nCould not open the progress report: "
                        f"{error}"
                    )


                input(
                    "\nPress Enter to continue..."
                )


        # ======================================================
        # OPTION 4 - OTHER DOCUMENTS
        # ================================================

        elif choice == "4":

            # --------------------------------------------------
            # FIND NOTICE AND OTHER DOCUMENTS
            #
            # Circulars are deliberately excluded because
            # the student gets those through Option 2.
            # Report Cards are excluded because they are
            # handled through Option 1.
            # Progress Reports are excluded because they are
            # handled through Option 3.
            # --------------------------------------------------

            other_documents = []

            for document in documents:

                if document["document_type"] in (
                    "Notice",
                    "Other"
                ):

                    other_documents.append(
                        document
                    )


            # --------------------------------------------------
            # CHECK WHETHER OTHER DOCUMENTS EXIST
            # --------------------------------------------------

            if not other_documents:

                print(
                    "\nNo other school documents are "
                    "currently available."
                )

                input(
                    "\nPress Enter to continue..."
                )

                continue


            # --------------------------------------------------
            # DISPLAY AVAILABLE DOCUMENTS
            # --------------------------------------------------

            while True:

                print("\n==========================================")
                print("          OTHER DOCUMENTS")
                print("==========================================")


                for number, document in enumerate(
                    other_documents,
                    start=1
                ):

                    print(
                        f"{number}. "
                        f"{document['document_title']}"
                    )

                    print(
                        f"   Type : "
                        f"{document['document_type']}"
                    )

                    print(
                        f"   Date : "
                        f"{document['uploaded_date']}"
                    )

                    print("------------------------------------------")


                print("0. Back")


                document_choice = input(
                    "\nEnter document number to open: "
                ).strip()


                if document_choice == "0":

                    break


                try:

                    selected_index = (
                        int(document_choice) - 1
                    )

                    document = other_documents[
                        selected_index
                    ]

                except (
                    ValueError,
                    IndexError
                ):

                    print(
                        "\nInvalid document number."
                    )

                    continue


                # --------------------------------------------------
                # CHECK THAT THE PDF STILL EXISTS
                # --------------------------------------------------

                if not os.path.isfile(
                    document["file_path"]
                ):

                    print(
                        "\nThe selected PDF could not "
                        "be found in storage."
                    )

                    input(
                        "\nPress Enter to continue..."
                    )

                    continue


                # --------------------------------------------------
                # OPEN THE SELECTED DOCUMENT
                # --------------------------------------------------

                try:

                    subprocess.run(
                        [
                            "termux-open",
                            document["file_path"]
                        ],
                        check=False
                    )

                    print(
                        "\nOpening document..."
                    )

                except Exception as error:

                    print(
                        f"\nCould not open the document: "
                        f"{error}"
                    )


                input(
                    "\nPress Enter to continue..."
                )


        # ======================================================
        # OPTION 5 - BACK
        # ======================================================

        elif choice == "5":

            break


        # ======================================================
        # INVALID OPTION
        # ======================================================

        else:

            print(
                "\nInvalid option."
            )



def delete_student_db(student_number):
    """
    Permanently delete a student from the school database.

    Because several tables use student_number as a foreign key
    with ON DELETE CASCADE, deleting the student will also remove
    the student's related records.

    Related records that may be deleted include:
        - Attendance
        - Fee payments
        - Homework submissions
        - Marks
        - Student documents
        - Student-subject assignments
        - Guardian-student relationships

    This function does NOT delete the guardian itself.
    It only removes the relationship between the student
    and the guardian.
    """

    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor so that we can execute SQL commands.
    cursor = connection.cursor()

    try:
        # ----------------------------------------------------------
        # Check that the student exists and get their information.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT
                students.student_number,
                students.student_name,
                grades.grade_name,
                students.classroom
            FROM students
            INNER JOIN grades
                ON students.grade_id = grades.grade_id
            WHERE students.student_number = ?
        """, (student_number,))

        student = cursor.fetchone()

        # Stop if the student does not exist.
        if student is None:
            raise ValueError("Student not found.")

        # ----------------------------------------------------------
        # Delete the student.
        #
        # SQLite will automatically remove related records where
        # the foreign key is configured with ON DELETE CASCADE.
        # ----------------------------------------------------------
        cursor.execute("""
            DELETE FROM students
            WHERE student_number = ?
        """, (student_number,))

        # Make sure the student was actually deleted.
        if cursor.rowcount == 0:
            connection.rollback()
            raise ValueError("Student could not be deleted.")

        # Save the deletion permanently.
        connection.commit()

        # Return the deleted student's information so that
        # the admin function can display it.
        return student

    except Exception:
        # Undo the transaction if anything goes wrong.
        connection.rollback()
        raise

    finally:
        # Always close the database connection.
        connection.close()




def delete_teacher_db(teacher_number):
    """
    Permanently delete a teacher from the school database.

    Because several tables use teacher_number as a foreign key
    with ON DELETE CASCADE, deleting the teacher will also
    remove related records.

    Related records may include:
        - Teacher-subject assignments
        - Attendance records entered by the teacher
        - Homework assigned by the teacher
        - Marks entered by the teacher
        - Teacher activity records
        - Timetable entries

    Homework submissions are NOT deleted because their
    teacher_number foreign key uses ON DELETE SET NULL.
    """

    # Open a connection to the SQLite database.
    connection = get_connection()

    # Create a cursor for executing SQL commands.
    cursor = connection.cursor()

    try:
        # First check that the teacher exists.
        cursor.execute("""
            SELECT
                teacher_number,
                teacher_name,
                email_address,
                status
            FROM teachers
            WHERE teacher_number = ?
        """, (teacher_number,))

        teacher = cursor.fetchone()

        # Stop if the teacher does not exist.
        if teacher is None:
            raise ValueError("Teacher not found.")

        # Delete the teacher.
        # The database's ON DELETE CASCADE rules will handle
        # the teacher's related records automatically.
        cursor.execute("""
            DELETE FROM teachers
            WHERE teacher_number = ?
        """, (teacher_number,))

        # Make sure a row was actually deleted.
        if cursor.rowcount == 0:
            connection.rollback()
            raise ValueError("Teacher could not be deleted.")

        # Save the deletion.
        connection.commit()

        # Return the deleted teacher's information.
        return teacher

    except Exception:
        # Undo the transaction if anything goes wrong.
        connection.rollback()
        raise

    finally:
        # Always close the database connection.
        connection.close()



def delete_admin_db(admin_id):
    """
    Permanently delete an administrator from the database.

    School news created by this administrator will be deleted
    because school_news.admin_id uses ON DELETE CASCADE.

    Student documents are different:
        student_documents.admin_id uses ON DELETE NO ACTION.

    Therefore, if the administrator is still referenced by
    student_documents, deletion will be blocked and the
    administrator will remain in the database.
    """

    # Open a connection to the database.
    connection = get_connection()

    # Create a cursor for executing SQL commands.
    cursor = connection.cursor()

    try:
        # Check that the administrator exists.
        cursor.execute("""
            SELECT
                admin_id,
                admin_name,
                category,
                email_address,
                status
            FROM admins
            WHERE admin_id = ?
        """, (admin_id,))

        admin = cursor.fetchone()

        if admin is None:
            raise ValueError("Administrator not found.")

        # Check whether student documents reference this admin.
        cursor.execute("""
            SELECT COUNT(*) AS document_count
            FROM student_documents
            WHERE admin_id = ?
        """, (admin_id,))

        document_count = cursor.fetchone()["document_count"]

        # Do not delete the admin if student documents depend on them.
        if document_count > 0:
            raise ValueError(
                f"This administrator cannot be deleted because "
                f"{document_count} student document(s) reference "
                f"this administrator."
            )

        # Delete the administrator.
        cursor.execute("""
            DELETE FROM admins
            WHERE admin_id = ?
        """, (admin_id,))

        if cursor.rowcount == 0:
            connection.rollback()
            raise ValueError("Administrator could not be deleted.")

        # Save the deletion.
        connection.commit()

        # Return the deleted administrator's information.
        return admin

    except Exception:
        # Undo the transaction if something goes wrong.
        connection.rollback()
        raise

    finally:
        # Always close the database connection.
        connection.close()




#this function helps when we run school_database.py we will see the tables we created
def show_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """)

    tables = cursor.fetchall()

    for table in tables:
        print(table["name"])

    connection.close()
    
    
if __name__ == "__main__":
        # Create all of our tables.
        create_tables()
        

        print("Database and tables created successfully.")


        print("\nTables in database:")
        show_tables()
        


import sqlite3

connection = sqlite3.connect("python_school.db")
cursor = connection.cursor()

cursor.execute("SELECT sqlite_version()")
version = cursor.fetchone()

print("SQLite version:", version[0])

connection.close()


