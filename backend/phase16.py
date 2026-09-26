import sqlite3
import hashlib
import secrets
import os

from school_database import get_connection
from school_database import create_tables
from school_database import (register_student_db,register_admin_db,register_teacher_db,get_school_fee_report_db)

from school_database import(register_guardian_db,login_guardian,login_3timespassword_block_guardian,unlock_guardian_account,
link_guardian_to_student_db,link_guardian_to_student,get_guardian_children_db,view_guardian_children,view_guardian_child_attendance,
get_guardian_child_attendance_by_term_db,get_guardian_child_homework_db,get_guardian_child_homework_by_term_db,view_guardian_child_homework,
generate_guardian_child_report_card_pdf,print_guardian_child_report_card,view_guardian_child_timetable,view_guardian_child_school_news,
view_guardian_child_fees_statement,make_guardian_child_fee_payment,view_guardian_child_payment_history,change_guardian_password_db,change_guardian_password,
get_guardian_child_submitted_homework_db,view_guardian_child_submitted_homework)

from school_database import(get_student_report_card_by_term_db)

from school_database import(add_student_document_db,save_student_pdf,select_student_document_from_android,upload_student_document_db,get_student_documents_db,
student_school_documents_menu,get_phase_for_grade,get_subjects_for_phase_db)

from school_database import(delete_subject_db,edit_teacher_subject_db)

from school_database import (get_grade_by_name,get_fee_for_grade,record_fee_payment,log_in,login_3timespassword_block,show_fees_statement,show_student_fees_statement,get_student_total_fee_due_db,
show_payment_history,get_grade_term_fee_report_db,login_admin,login_3timespassword_block_admin,login_teacher,login_3timespassword_block_teacher,add_subject_db,
unlock_teacher_account,unlock_admin_account,unlock_student_account,save_admin_log,view_admin_logs,assign_teacher_subject_db,
get_teacher_subjects_for_grade,get_teacher_subjects,record_mark_db,record_attendance_db,assign_homework_db,select_multiple_student_subjects,
assign_student_subject_db,assign_multiple_student_subjects_db,get_student_homework_db,get_student_attendance_db,get_student_results_db,
get_student_report_card_db,get_student_term_payment_status_db,get_current_school_term_db,generate_report_card_pdf,get_all_students_db,get_all_teachers_db,
get_students_by_grade_db,get_results_by_grade_db,get_school_statistics_db,get_admin_logs_db,change_admin_password_db,record_student_fee_payment_db)

from school_database import (get_student_timetable_db,get_student_school_news_db,post_school_news_db,add_timetable_db,view_timetable_admin,edit_timetable_db,
delete_timetable_db,get_student_profile_db,get_student_homework_for_submission_db,save_student_homework_pdf,get_teacher_homework_submissions_db,
get_teacher_homework_submissions_db,open_homework_pdf,mark_homework_submission_db,submit_homework_pdf_db,select_pdf_from_android,set_school_term_dates_db,
get_fees_structure_db,update_grade_fee_db,)

from datetime import datetime, date




# this func is for registering students
def register_student(current_user):
    print("===== PYTHON SCHOOL =====")
    print("Thank you for choosing Python School.")
    print("Please fill in the form below to create your students account.\n")

    student_name = input("1. Enter your name: ")

    id_number = input("2. Enter your ID number: ")

    age = int(input("3. Enter your age: "))

    gender = input("4. Enter your gender (Male/Female): ")

    nationality = input("5. Enter your nationality: ")

    grade_name = input("6. Enter your grade: ")

    grade_record = get_grade_by_name(grade_name)

    if grade_record is None:
        print("That grade does not exist.")
        print("Please enter a valid grade.")
        return

    else:
        grade_id = grade_record["grade_id"]

    # ----------------------------------------------------------
    # Find the fee associated with this grade.
    # ----------------------------------------------------------
    fee = get_fee_for_grade(grade_id)

    # Check whether a fee has been configured.
    if fee is None:
        print("\nNo fee structure has been set for this grade.")
        return

    # Get the fee amount.
    fees_balance = fee["amount"]

    # Tell the student what fee was assigned.
    print(f"\nYour grade: {grade_record['grade_name']}")
    print(f"Your school fee: {fees_balance:.2f}/year")

    classroom = input("7. Enter your Classroom: ")

    password = input("8. Choose your password:")
    print()

    # ----------------------------------------------------------
    # Create a secure password salt.
    # ----------------------------------------------------------
    salt = secrets.token_bytes(16)

    # Create the password hash using SHA-256.
    password_hash = hashlib.sha256(
        password.encode() + salt
    ).hexdigest()

    # Convert the salt into text so it can be stored in SQLite.
    password_salt = salt.hex()

    try:

        # ----------------------------------------------------------
        # Create the student.
        # ----------------------------------------------------------
        student_number = register_student_db(
            student_name,
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

        print("Student Number:", student_number)
        print()

        # Select subjects from the phase available for this student's grade.
        selected_subjects = select_multiple_student_subjects(grade_name)

        # ----------------------------------------------------------
        # Save all selected subjects for this student.
        # ----------------------------------------------------------
        assign_multiple_student_subjects_db(
            student_number,
            selected_subjects
        )

        print("\nSubjects successfully assigned to the student.")

        # ----------------------------------------------------------
        # Log the admin action.
        # ----------------------------------------------------------
        save_admin_log(
            admin_name=current_user["admin_name"],
            category=current_user["category"],
            action=f"Registered student: {student_name}",
            teacher_number=None,
            student_number=student_number,
            admin_id=None
        )

        # ----------------------------------------------------------
        # Finish registration.
        # ----------------------------------------------------------
        print("Registration successful!\n")
        print(f"Your Student Number is: {student_number}\n")

        # After registration, open the student menu.
        student_menu(current_user)

    except sqlite3.IntegrityError:
        print("Student already exists.")

    except ValueError as error:
        # Display validation errors such as:
        #
        # "Subject number 20 does not exist."
        # "No subjects were selected."
        #
        print(f"\nRegistration error: {error}")

    except Exception as error:
        # Catch any unexpected error so the program
        # doesn't crash without explaining what happened.
        print(f"\nAn unexpected error occurred: {error}")


def add_subject():
    """
    Allow the administrator to add a subject to a school phase.

    The administrator first selects the phase and then enters
    the subject name.

    The database function will:
        1. Create the subject if it does not exist.
        2. Reuse the subject if it already exists.
        3. Create the phase_subjects mapping.
    """

    print("\n===== ADD SUBJECT =====")

    # ----------------------------------------------------------
    # Display the available school phases.
    # ----------------------------------------------------------
    print("1. Foundation Phase")
    print("2. Intermediate Phase")
    print("3. Senior Phase")
    print("4. FET Phase")

    # Ask the administrator to choose a phase.
    phase_choice = input(
        "\nSelect phase: "
    ).strip()

    # ----------------------------------------------------------
    # Convert the administrator's choice into the actual
    # phase name used in the database.
    # ----------------------------------------------------------
    phase_map = {
        "1": "Foundation Phase",
        "2": "Intermediate Phase",
        "3": "Senior Phase",
        "4": "FET Phase"
    }

    # Check whether the selected number is valid.
    if phase_choice not in phase_map:
        print("\nInvalid phase selection.")
        return

    # Get the actual phase name.
    phase_name = phase_map[phase_choice]

    print(f"\nSelected phase: {phase_name}")

    # ----------------------------------------------------------
    # Ask the administrator for the subject name.
    # ----------------------------------------------------------
    subject_name = input(
        "Enter Subject Name: "
    ).strip()

    # Do not continue if the subject name is empty.
    if not subject_name:
        print("\nSubject name cannot be empty.")
        return

    try:
        # ------------------------------------------------------
        # Send the subject and phase to the database function.
        #
        # The database function handles:
        #   - creating the subject
        #   - reusing an existing subject
        #   - creating the phase_subjects relationship
        # ------------------------------------------------------
        subject_id = add_subject_db(
            subject_name,
            phase_name
        )

        # Display the information to the administrator.
        print("\n===== SUBJECT ADDED =====")
        print(f"Subject ID: {subject_id}")
        print(f"Subject: {subject_name}")
        print(f"Phase: {phase_name}")

        print("\nSubject added successfully!\n")

    except ValueError as error:
        # Display a friendly error message.
        print(f"\n{error}\n")

    except sqlite3.IntegrityError:
        # Handle any database integrity problem.
        print("\nSubject could not be added.\n")             
            


def delete_subject():
    """
    Allow the administrator to remove a subject from a
    specific school phase.

    IMPORTANT:
        This does NOT permanently delete the subject from
        the subjects table.

        It only removes the subject from the selected phase.

    The administrator:
        1. Selects a phase.
        2. Sees subjects assigned to that phase.
        3. Selects the subject to remove.
        4. Confirms the deletion.
    """

    print("\n===== DELETE SUBJECT =====")

    # Display the available school phases.
    print("1. Foundation Phase")
    print("2. Intermediate Phase")
    print("3. Senior Phase")
    print("4. FET Phase")

    # Ask the administrator to choose a phase.
    phase_choice = input(
        "\nSelect phase: "
    ).strip()

    # Convert the administrator's number into
    # the actual phase name stored in the database.
    phase_map = {
        "1": "Foundation Phase",
        "2": "Intermediate Phase",
        "3": "Senior Phase",
        "4": "FET Phase"
    }

    # Make sure the administrator selected a valid phase.
    if phase_choice not in phase_map:
        print("\nInvalid phase selection.")
        return

    phase_name = phase_map[phase_choice]

    print(f"\nSelected phase: {phase_name}")

    # Get all subjects currently assigned to this phase.
    subjects = get_subjects_for_phase_db(phase_name)

    # Check whether this phase has any subjects.
    if not subjects:
        print(
            f"\nNo subjects are currently assigned to "
            f"{phase_name}."
        )
        return

    print("\n===== SUBJECTS IN THIS PHASE =====")

    # Display the subjects with simple numbers.
    for number, subject in enumerate(subjects, start=1):
        print(
            f"{number}. {subject['subject_name']}"
        )

    # Ask which subject should be removed.
    subject_choice = input(
        "\nSelect subject to remove: "
    ).strip()

    # Make sure the input is a number.
    if not subject_choice.isdigit():
        print("\nInvalid subject selection.")
        return

    subject_number = int(subject_choice)

    # Make sure the number is within the displayed list.
    if subject_number < 1 or subject_number > len(subjects):
        print("\nInvalid subject selection.")
        return

    # Get the selected subject.
    selected_subject = subjects[subject_number - 1]
    subject_name = selected_subject["subject_name"]

    print(
        f"\nYou selected: {subject_name}"
    )
    print(
        f"Phase: {phase_name}"
    )

    # Ask the administrator to confirm the removal.
    confirmation = input(
        "\nAre you sure you want to remove this subject "
        "from this phase? (yes/no): "
    ).strip().lower()

    if confirmation != "yes":
        print("\nSubject deletion cancelled.")
        return

    try:
        # Remove only the phase-subject relationship.
        delete_subject_db(
            subject_name,
            phase_name
        )

        print("\n===== SUBJECT REMOVED =====")
        print(f"Subject: {subject_name}")
        print(f"Phase: {phase_name}")
        print("\nSubject removed successfully!\n")

    except ValueError as error:
        print(f"\n{error}\n")

    except sqlite3.IntegrityError:
        print(
            "\nThe subject could not be removed.\n"
        )



def assign_subject_teacher():
        
        teacher_number = input("Enter teacher Number: ")
        
        subject_name = input("Enter subject name: ")
        
        grade_name = input("Enter grade: ")
        
        
        try:

            # Send the subject's information to the database function.
            # This now unpacks all 4 returned items safely
            teacher_subject_id, teacher, subject, grade = assign_teacher_subject_db(
                teacher_number,
                subject_name,
                grade_name
            )

            print("Teacher Subject ID:", teacher_subject_id)
            print()

            print("Registration successful!\n")
            print(
                    f"{teacher['teacher_name']} assigned to "
                    f"{subject['subject_name']} - Grade {grade['grade_name']}."
            )
            print(f"Teacher Subject ID is: {teacher_subject_id}\n")
            

        except sqlite3.IntegrityError:
            print("This teacher is already assigned to this subject and grade.")  


            
def edit_assigned_subject():
    """
    Allow the Principal to edit an existing teacher assignment.

    The administrator can change:
        - Teacher
        - Subject
        - Grade

    The existing assignment is identified by
    teacher_subject_id.

    The database function performs the final validation
    before saving the changes.
    """

    print("\n===== EDIT ASSIGNED SUBJECT =====")

    # Open the database so we can display all assignments.
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # ----------------------------------------------------------
        # Get all current teacher-subject-grade assignments.
        # ----------------------------------------------------------
        cursor.execute("""
            SELECT
                teacher_subjects.teacher_subject_id,
                teacher_subjects.teacher_number,
                teachers.teacher_name,
                teacher_subjects.subject_name,
                teacher_subjects.grade_name
            FROM teacher_subjects
            INNER JOIN teachers
                ON teacher_subjects.teacher_number =
                   teachers.teacher_number
            ORDER BY
                teacher_subjects.grade_name,
                teacher_subjects.subject_name,
                teachers.teacher_name
        """)

        assignments = cursor.fetchall()

    finally:
        # Close this temporary database connection.
        connection.close()

    # Check whether there are any assignments.
    if not assignments:
        print("\nNo teacher subject assignments found.")
        return

    print("\n===== CURRENT TEACHER ASSIGNMENTS =====")

    # Display each assignment with a simple number.
    for number, assignment in enumerate(assignments, start=1):
        print(
            f"{number}. "
            f"{assignment['teacher_name']} | "
            f"{assignment['subject_name']} | "
            f"Grade {assignment['grade_name']}"
        )

    # Ask the administrator which assignment should be edited.
    assignment_choice = input(
        "\nSelect assignment to edit: "
    ).strip()

    # Check that the administrator entered a number.
    if not assignment_choice.isdigit():
        print("\nInvalid assignment selection.")
        return

    assignment_number = int(assignment_choice)

    # Check that the number exists in the list.
    if (
        assignment_number < 1
        or assignment_number > len(assignments)
    ):
        print("\nInvalid assignment selection.")
        return

    # Get the selected assignment.
    current_assignment = assignments[
        assignment_number - 1
    ]

    print("\n===== CURRENT ASSIGNMENT =====")
    print(
        f"Teacher: {current_assignment['teacher_name']}"
    )
    print(
        f"Subject: {current_assignment['subject_name']}"
    )
    print(
        f"Grade: {current_assignment['grade_name']}"
    )

    # --------------------------------------------------------------
    # SELECT NEW TEACHER
    # --------------------------------------------------------------
    print("\n===== SELECT NEW TEACHER =====")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                teacher_number,
                teacher_name
            FROM teachers
            ORDER BY teacher_name
        """)

        teachers = cursor.fetchall()

    finally:
        connection.close()

    if not teachers:
        print("\nNo teachers found.")
        return

    for number, teacher in enumerate(teachers, start=1):
        print(
            f"{number}. "
            f"{teacher['teacher_name']} "
            f"(Teacher No: {teacher['teacher_number']})"
        )

    teacher_choice = input(
        "\nSelect new teacher: "
    ).strip()

    if not teacher_choice.isdigit():
        print("\nInvalid teacher selection.")
        return

    teacher_number_choice = int(teacher_choice)

    if (
        teacher_number_choice < 1
        or teacher_number_choice > len(teachers)
    ):
        print("\nInvalid teacher selection.")
        return

    new_teacher = teachers[
        teacher_number_choice - 1
    ]

    # --------------------------------------------------------------
    # SELECT NEW GRADE
    # --------------------------------------------------------------
    print("\n===== SELECT NEW GRADE =====")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                grade_id,
                grade_name
            FROM grades
            ORDER BY grade_id
        """)

        grades = cursor.fetchall()

    finally:
        connection.close()

    if not grades:
        print("\nNo grades found.")
        return

    for number, grade in enumerate(grades, start=1):
        print(
            f"{number}. {grade['grade_name']}"
        )

    grade_choice = input(
        "\nSelect new grade: "
    ).strip()

    if not grade_choice.isdigit():
        print("\nInvalid grade selection.")
        return

    grade_number_choice = int(grade_choice)

    if (
        grade_number_choice < 1
        or grade_number_choice > len(grades)
    ):
        print("\nInvalid grade selection.")
        return

    new_grade = grades[
        grade_number_choice - 1
    ]

    # --------------------------------------------------------------
    # SELECT NEW SUBJECT
    # --------------------------------------------------------------

    # Determine the phase of the new grade.
    new_phase = get_phase_for_grade(
        new_grade["grade_name"]
    )

    if new_phase is None:
        if new_grade["grade_name"] == "Old Curriculum":
            print(
                "\nOld Curriculum does not have a phase mapping."
            )
            return

        print(
            f"\nUnable to determine the phase for "
            f"Grade {new_grade['grade_name']}."
        )
        return

    print(
        f"\n===== SELECT NEW SUBJECT ====="
    )
    print(
        f"Available subjects for "
        f"Grade {new_grade['grade_name']} "
        f"({new_phase}):"
    )

    # Get subjects belonging to the new grade's phase.
    subjects = get_subjects_for_phase_db(
        new_phase
    )

    if not subjects:
        print(
            f"\nNo subjects configured for {new_phase}."
        )
        return

    for number, subject in enumerate(subjects, start=1):
        print(
            f"{number}. {subject['subject_name']}"
        )

    subject_choice = input(
        "\nSelect new subject: "
    ).strip()

    if not subject_choice.isdigit():
        print("\nInvalid subject selection.")
        return

    subject_number_choice = int(subject_choice)

    if (
        subject_number_choice < 1
        or subject_number_choice > len(subjects)
    ):
        print("\nInvalid subject selection.")
        return

    new_subject = subjects[
        subject_number_choice - 1
    ]

    # --------------------------------------------------------------
    # SHOW THE NEW ASSIGNMENT
    # --------------------------------------------------------------
    print("\n===== NEW ASSIGNMENT =====")
    print(
        f"Teacher: {new_teacher['teacher_name']}"
    )
    print(
        f"Subject: {new_subject['subject_name']}"
    )
    print(
        f"Grade: {new_grade['grade_name']}"
    )

    # Ask for confirmation before changing the database.
    confirmation = input(
        "\nConfirm this change? (yes/no): "
    ).strip().lower()

    if confirmation != "yes":
        print("\nAssignment edit cancelled.")
        return

    # --------------------------------------------------------------
    # UPDATE THE DATABASE
    # --------------------------------------------------------------
    try:
        edit_teacher_subject_db(
            current_assignment[
                "teacher_subject_id"
            ],
            new_teacher[
                "teacher_number"
            ],
            new_subject[
                "subject_name"
            ],
            new_grade[
                "grade_name"
            ]
        )

        print("\n===== ASSIGNMENT UPDATED =====")
        print(
            f"Teacher: {new_teacher['teacher_name']}"
        )
        print(
            f"Subject: {new_subject['subject_name']}"
        )
        print(
            f"Grade: {new_grade['grade_name']}"
        )
        print("\nAssignment updated successfully!\n")

    except ValueError as error:
        print(f"\n{error}\n")



def delete_student():
    """
    Allow the administrator to permanently delete a student.

    The administrator first selects a student from the list.
    The student's details are displayed before deletion.

    Because the database uses ON DELETE CASCADE for the
    student's related records, deleting the student will
    also remove related records such as:
        - Attendance
        - Fee payments
        - Homework submissions
        - Marks
        - Student documents
        - Student-subject assignments
        - Guardian-student relationships

    The guardian record itself is NOT deleted.
    """

    # Get all students from the database.
    students = get_all_students_db()

    # Make sure there are students to display.
    if not students:
        print("\nNo students found.")
        return

    print("\n===== DELETE STUDENT =====")
    print("Select the student you want to delete:\n")

    # Display the students with a number beside each one.
    for number, student in enumerate(students, start=1):
        print(
            f"{number}. "
            f"{student['student_number']} - "
            f"{student['student_name']}"
        )

    # Ask the administrator to select a student.
    selection = input(
        "\nEnter student number from the list (or 0 to cancel): "
    ).strip()

    # Allow the administrator to cancel.
    if selection == "0":
        print("Delete cancelled.")
        return

    # Validate that the selection is a number.
    if not selection.isdigit():
        print("Invalid selection.")
        return

    selection = int(selection)

    # Make sure the selected number exists.
    if selection < 1 or selection > len(students):
        print("Invalid student selection.")
        return

    # Get the selected student.
    student = students[selection - 1]

    print("\n===== STUDENT TO DELETE =====")
    print(f"Student Number: {student['student_number']}")
    print(f"Student Name:   {student['student_name']}")
    print(f"Grade:          {student['grade_name']}")
    print(f"Classroom:      {student['classroom']}")

    # Warn the administrator about the permanent deletion.
    print("\nWARNING:")
    print("This action will permanently delete this student")
    print("and the student's related database records.")

    # Ask for confirmation.
    confirmation = input(
        "\nAre you sure you want to delete this student? (yes/no): "
    ).strip().lower()

    if confirmation != "yes":
        print("Delete cancelled.")
        return

    try:
        # Delete the student from the database.
        deleted_student = delete_student_db(
            student['student_number']
        )

        print("\nStudent deleted successfully.")
        print(
            f"Deleted: {deleted_student['student_number']} - "
            f"{deleted_student['student_name']}"
        )

    except ValueError as error:
        print(f"\nError: {error}")

    except Exception as error:
        print(f"\nUnexpected error: {error}")



def delete_teacher():
    """
    Allow the administrator to permanently delete a teacher.

    The administrator selects a teacher, reviews the teacher's
    details, and confirms the deletion.

    The database will automatically handle related records
    according to the teacher foreign-key rules.
    """

    # Get all teachers from the database.
    teachers = get_all_teachers_db()

    # Check whether there are any teachers.
    if not teachers:
        print("\nNo teachers found.")
        return

    print("\n===== DELETE TEACHER =====")
    print("Select the teacher you want to delete:\n")

    # Display all teachers with a selection number.
    for number, teacher in enumerate(teachers, start=1):
        print(
            f"{number}. "
            f"{teacher['teacher_number']} - "
            f"{teacher['teacher_name']}"
        )

    # Ask the administrator to select a teacher.
    selection = input(
        "\nEnter teacher number from the list (or 0 to cancel): "
    ).strip()

    # Allow the administrator to cancel.
    if selection == "0":
        print("Delete cancelled.")
        return

    # Make sure the selection is numeric.
    if not selection.isdigit():
        print("Invalid selection.")
        return

    selection = int(selection)

    # Make sure the selected number exists.
    if selection < 1 or selection > len(teachers):
        print("Invalid teacher selection.")
        return

    # Get the selected teacher.
    teacher = teachers[selection - 1]

    print("\n===== TEACHER TO DELETE =====")
    print(f"Teacher Number: {teacher['teacher_number']}")
    print(f"Teacher Name:   {teacher['teacher_name']}")
    print(f"Email:          {teacher['email_address']}")
    print(f"Status:         {teacher['status']}")

    # Warn the administrator before the permanent deletion.
    print("\nWARNING:")
    print("This action will permanently delete this teacher")
    print("and the teacher's related database records.")

    # Ask for confirmation.
    confirmation = input(
        "\nAre you sure you want to delete this teacher? (yes/no): "
    ).strip().lower()

    # Anything other than "yes" cancels the deletion.
    if confirmation != "yes":
        print("Delete cancelled.")
        return

    try:
        # Delete the teacher from the database.
        deleted_teacher = delete_teacher_db(
            teacher['teacher_number']
        )

        print("\nTeacher deleted successfully.")
        print(
            f"Deleted: {deleted_teacher['teacher_number']} - "
            f"{deleted_teacher['teacher_name']}"
        )

    except ValueError as error:
        print(f"\nError: {error}")

    except Exception as error:
        print(f"\nUnexpected error: {error}")




def delete_admin(current_admin):
    """
    Allow the Principal to permanently delete an administrator.

    Safety protection:
        The currently logged-in administrator cannot delete
        their own account.

    The database function also checks whether student documents
    reference the administrator before allowing deletion.
    """

    # Get all administrators from the database.
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                admin_id,
                admin_name,
                category,
                email_address,
                status
            FROM admins
            ORDER BY admin_id
        """)

        admins = [dict(row) for row in cursor.fetchall()]

    finally:
        # Always close the database connection.
        connection.close()

    # Check whether any administrators exist.
    if not admins:
        print("\nNo administrators found.")
        return

    print("\n===== DELETE ADMINISTRATOR =====")
    print("Select the administrator you want to delete:\n")

    # Display all administrators.
    for number, admin in enumerate(admins, start=1):
        print(
            f"{number}. "
            f"{admin['admin_id']} - "
            f"{admin['admin_name']} "
            f"({admin['category']})"
        )

    # Ask the Principal to select an administrator.
    selection = input(
        "\nEnter administrator number from the list "
        "(or 0 to cancel): "
    ).strip()

    # Allow cancellation.
    if selection == "0":
        print("Delete cancelled.")
        return

    # Make sure the selection is numeric.
    if not selection.isdigit():
        print("Invalid selection.")
        return

    selection = int(selection)

    # Make sure the selected number exists.
    if selection < 1 or selection > len(admins):
        print("Invalid administrator selection.")
        return

    # Get the selected administrator.
    admin = admins[selection - 1]

    # ---------------------------------------------------------
    # SAFETY CHECK: Prevent the logged-in administrator
    # from deleting their own account.
    # ---------------------------------------------------------
    if admin["admin_id"] == current_admin["admin_id"]:
        print("\nYou cannot delete the administrator account")
        print("that you are currently logged in with.")
        print("Please use another administrator account to")
        print("delete this account.")
        return

    print("\n===== ADMINISTRATOR TO DELETE =====")
    print(f"Admin ID:       {admin['admin_id']}")
    print(f"Admin Name:     {admin['admin_name']}")
    print(f"Category:       {admin['category']}")
    print(f"Email:          {admin['email_address']}")
    print(f"Status:          {admin['status']}")

    # Warn before permanent deletion.
    print("\nWARNING:")
    print("This action will permanently delete this administrator.")

    # Explain what happens to school news.
    print(
        "School news created by this administrator will also "
        "be removed."
    )

    # Ask for confirmation.
    confirmation = input(
        "\nAre you sure you want to delete this administrator? "
        "(yes/no): "
    ).strip().lower()

    # Anything other than "yes" cancels the operation.
    if confirmation != "yes":
        print("Delete cancelled.")
        return

    try:
        # Delete the administrator from the database.
        deleted_admin = delete_admin_db(
            admin["admin_id"]
        )

        print("\nAdministrator deleted successfully.")
        print(
            f"Deleted: {deleted_admin['admin_id']} - "
            f"{deleted_admin['admin_name']}"
        )

    except ValueError as error:
        print(f"\nError: {error}")

    except Exception as error:
        print(f"\nUnexpected error: {error}")


  
  
# this func is for registering teacher
def register_teacher():
        print("===== PYTHON SCHOOL =====")
        print("Please fill in the form below to create your teacher's account.\n")

        teacher_name = input("1. Enter your name: ")
        
        id_number = input("2. Enter your ID or Passport number: ")
        
        gender = input("3. Enter your gender(Make/Female): ")
        
        nationality = input("4. Enter your nationality: ")
        
        password = input("5. Choose your password: ")

        salt = secrets.token_bytes(16)

        password_hash = hashlib.sha256(
            password.encode() + salt
        ).hexdigest()
        password_salt = salt.hex()
        
        email_address = input("6. Enter your email address: ")
        
        
        try:

            # Send the admin's information to the database function.
            teacher_number = register_teacher_db(
                teacher_name,
                id_number,
                gender,
                nationality,
                password_hash,
                password_salt,
                email_address
            )

            print("Teacher Number:", teacher_number)
            print()

            print("Registration successful!\n")
            print(f"Your Teacher Number is: {teacher_number}\n")
            
            # we call the admin menu func so that aftet registering we dont go back to main menu 
            teacher_menu(teacher_number)

        except sqlite3.IntegrityError:
            print("Teacher already exists")  

def teacher_menu(current_user):
  while True:
    current_term = get_current_school_term_db()

    if current_term:
                            
        print("\n===== CURRENT SCHOOL TERM =====")
        print("School Year:", current_term["school_year"])
        print("Term:", current_term["term_number"])
        print("Start Date:", current_term["start_date"])
        print("End Date:", current_term["end_date"])
        print("--------------------------------------\n")
        
    else:
        print("\nNo active school term found.\n")
        
    
    print("\n===== TEACHER PANEL =====\n")
    menu3 = ["Enter marks","Record attendance","Assign homework","change password","View Homework Submissions","log out"]

    for number, item in enumerate(menu3,start=1):
      print(number, item)
    try:
      choice3 = int(input("Choose from the menu: "))
      if choice3 == 1:
          
        while True:
                print("1. Exam Marks: ")
                print("2. Homework marks: ")
                print("3. Back")
                choice = input("Select option: ")
                
                if choice == "1":
                    
                        # ----------------------------------------------------------
                        # ENTER MARKS
                        # ----------------------------------------------------------

                        try:
                            # Ask the teacher for the student's number.
                            student_number = int(input("Enter student number: "))

                            # ------------------------------------------------------
                            # Find the student in SQLite.
                            # ------------------------------------------------------

                            connection = get_connection()
                            cursor = connection.cursor()

                            cursor.execute("""
                                SELECT
                                    s.student_number,
                                    s.student_name,
                                    s.grade_id,
                                    g.grade_name
                                FROM students s
                                JOIN grades g
                                    ON s.grade_id = g.grade_id
                                WHERE s.student_number = ?
                            """, (student_number,))

                            student = cursor.fetchone()

                            # Close the database connection.
                            connection.close()

                            # ------------------------------------------------------
                            # Check whether the student exists.
                            # ------------------------------------------------------

                            if student is None:
                                print("Student not found.\n")
                                continue

                            # Display the student information.
                            print("\n===== STUDENT FOUND =====")
                            print(f"Student Number : {student['student_number']}")
                            print(f"Name           : {student['student_name']}")
                            print(f"Grade          : {student['grade_name']}")
                            print()

                            # ------------------------------------------------------
                            # Get subjects assigned to this teacher for this grade.
                            # ------------------------------------------------------

                            teacher_number = current_user["teacher_number"]

                            assigned_subjects = get_teacher_subjects_for_grade(
                                teacher_number,
                                student["grade_name"]
                            )

                            # Check whether this teacher teaches this student's grade.
                            if not assigned_subjects:
                                print(
                                    "You are not assigned to teach any subject "
                                    "for this student's grade.\n"
                                )
                                continue

                            # ------------------------------------------------------
                            # Display the teacher's available subjects.
                            # ------------------------------------------------------

                            print("===== YOUR SUBJECTS =====")

                            for number, subject in enumerate(assigned_subjects, start=1):
                                print(
                                    f"{number}. {subject['subject_name']}"
                                )

                            print()

                            # Ask the teacher to select a subject.
                            subject_choice = int(
                                input("Choose the subject: ")
                            )

                            # Make sure the choice is valid.
                            if subject_choice < 1 or subject_choice > len(assigned_subjects):
                                print("Invalid subject choice.\n")
                                continue

                            # Get the selected subject from the list.
                            selected_subject = assigned_subjects[subject_choice - 1]

                            subject_id = selected_subject["subject_id"]

                            # ------------------------------------------------------
                            # Enter the mark.
                            # ------------------------------------------------------

                            mark_value = float(
                                input("Enter Mark: ")
                            )

                            # Ask for the maximum possible mark.
                            total_possible = float(
                                input("Enter Total Possible Mark: ")
                            )

                            # Ask for the exam/test date.
                            exam_date = input(
                                "Enter Exam/Test Date (YYYY-MM-DD): "
                            )

                            # ------------------------------------------------------
                            # Save the mark to SQLite.
                            # ------------------------------------------------------

                            record_mark_db(
                                student_number,
                                subject_id,
                                teacher_number,
                                mark_value,
                                total_possible,
                                exam_date
                            )

                            print("\nMark saved successfully!")
                            print(f"Student : {student['student_name']}")
                            print(f"Subject : {selected_subject['subject_name']}")
                            print(f"Mark    : {mark_value:g}/{total_possible:g}")
                            print()

                        except ValueError as error:
                            # Handle invalid numbers and database validation errors.
                            print(f"\nError: {error}\n")
                
                
                elif choice == "2":

                        # ----------------------------------------------------------
                        # HOMEWORK MARKS
                        # ----------------------------------------------------------

                        try:

                            # ------------------------------------------------------
                            # Ask the teacher for the student's number.
                            # ------------------------------------------------------

                            student_number = int(
                                input("Enter student number: ")
                            )

                            # ------------------------------------------------------
                            # Find the student and their grade.
                            # ------------------------------------------------------

                            connection = get_connection()
                            cursor = connection.cursor()

                            cursor.execute("""
                                SELECT
                                    s.student_number,
                                    s.student_name,
                                    s.grade_id,
                                    g.grade_name
                                FROM students s
                                JOIN grades g
                                    ON s.grade_id = g.grade_id
                                WHERE s.student_number = ?
                            """, (student_number,))

                            student = cursor.fetchone()

                            connection.close()

                            # ------------------------------------------------------
                            # Check whether the student exists.
                            # ------------------------------------------------------

                            if student is None:
                                print("\nStudent not found.\n")
                                continue

                            # ------------------------------------------------------
                            # Display the student information.
                            # ------------------------------------------------------

                            print("\n===== STUDENT FOUND =====")
                            print(
                                f"Student Number : {student['student_number']}"
                            )
                            print(
                                f"Name           : {student['student_name']}"
                            )
                            print(
                                f"Grade          : {student['grade_name']}"
                            )
                            print()

                            # ------------------------------------------------------
                            # Get the teacher's number.
                            # ------------------------------------------------------

                            teacher_number = current_user["teacher_number"]

                            # ------------------------------------------------------
                            # Get subjects assigned to this teacher for this grade.
                            # ------------------------------------------------------

                            assigned_subjects = get_teacher_subjects_for_grade(
                                teacher_number,
                                student["grade_name"]
                            )

                            # ------------------------------------------------------
                            # Check whether the teacher teaches this grade.
                            # ------------------------------------------------------

                            if not assigned_subjects:

                                print(
                                    "You are not assigned to teach any subject "
                                    "for this student's grade.\n"
                                )

                                continue

                            # ------------------------------------------------------
                            # Display the teacher's subjects.
                            # ------------------------------------------------------

                            print("===== YOUR SUBJECTS =====")

                            for number, subject in enumerate(
                                assigned_subjects,
                                start=1
                            ):

                                print(
                                    f"{number}. {subject['subject_name']}"
                                )

                            print()

                            # ------------------------------------------------------
                            # Ask the teacher to choose a subject.
                            # ------------------------------------------------------

                            subject_choice = int(
                                input("Choose the subject: ")
                            )

                            # ------------------------------------------------------
                            # Validate the subject choice.
                            # ------------------------------------------------------

                            if (
                                subject_choice < 1
                                or subject_choice > len(assigned_subjects)
                            ):

                                print("Invalid subject choice.\n")
                                continue

                            # ------------------------------------------------------
                            # Get the selected subject.
                            # ------------------------------------------------------

                            selected_subject = assigned_subjects[
                                subject_choice - 1
                            ]

                            subject_id = selected_subject["subject_id"]

                            # ------------------------------------------------------
                            # Find homework for:
                            #
                            # 1. This teacher
                            # 2. This student's grade
                            # 3. The selected subject
                            #
                            # This prevents the teacher from seeing unrelated
                            # homework.
                            # ------------------------------------------------------

                            connection = get_connection()
                            cursor = connection.cursor()

                            cursor.execute("""
                                SELECT
                                    h.homework_id,
                                    h.title,
                                    h.description,
                                    h.due_date
                                    FROM homework h
                                WHERE h.teacher_number = ?
                                AND h.grade_id = ?
                                AND h.subject_id = ?
                                ORDER BY h.due_date DESC,
                                        h.homework_id DESC
                            """, (
                                teacher_number,
                                student["grade_id"],
                                subject_id
                            ))

                            homework_list = cursor.fetchall()

                            connection.close()

                            # ------------------------------------------------------
                            # Check whether this teacher has posted homework
                            # for this subject and grade.
                            # ------------------------------------------------------

                            if not homework_list:

                                print(
                                    "\nNo homework found for this subject "
                                    "and grade.\n"
                                )

                                continue

                            # ------------------------------------------------------
                            # Display the homework list.
                            # ------------------------------------------------------

                            print("\n===== HOMEWORK =====")

                            for number, homework in enumerate(
                                homework_list,
                                start=1
                            ):

                                print(
                                    f"{number}. {homework['title']}"
                                )

                                print(
                                    f"   Due Date: {homework['due_date']}"
                                )

                            print()

                            # ------------------------------------------------------
                            # Ask the teacher to choose the homework.
                            # ------------------------------------------------------

                            homework_choice = int(
                                input("Choose the homework: ")
                            )

                            # ------------------------------------------------------
                            # Validate the homework choice.
                            # ------------------------------------------------------

                            if (
                                homework_choice < 1
                                or homework_choice > len(homework_list)
                            ):

                                print("Invalid homework choice.\n")
                                continue

                            # ------------------------------------------------------
                            # Get the selected homework.
                            # ------------------------------------------------------

                            selected_homework = homework_list[
                                homework_choice - 1
                            ]

                            homework_id = selected_homework["homework_id"]

                            # ------------------------------------------------------
                            # Find this student's submission.
                            # ------------------------------------------------------

                            connection = get_connection()
                            cursor = connection.cursor()

                            cursor.execute("""
                                SELECT
                                    submission_id,
                                    submission_text,
                                    file_path,
                                    submitted_date,
                                    status,
                                    marked_date,
                                    mark,
                                    total_possible
                                FROM homework_submissions
                                WHERE homework_id = ?
                                AND student_number = ?
                            """, (
                                homework_id,
                                student_number
                            ))

                            submission = cursor.fetchone()

                            connection.close()

                            # ------------------------------------------------------
                            # Check whether the student submitted the homework.
                            # ------------------------------------------------------

                            if submission is None:

                                print(
                                    "\nThis student has not submitted "
                                    "this homework yet.\n"
                                )

                                continue

                            # ------------------------------------------------------
                            # Display submission information.
                            # ------------------------------------------------------

                            print("\n===== SUBMISSION =====")

                            print(
                                f"Status         : {submission['status']}"
                            )

                            print(
                                f"Submitted Date : {submission['submitted_date']}"
                            )

                            if submission["file_path"]:

                                print(
                                    f"PDF File       : {submission['file_path']}"
                                )

                            if submission["submission_text"]:

                                print(
                                    f"Submission Text : "
                                    f"{submission['submission_text']}"
                                )

                            print()

                            # ------------------------------------------------------
                            # If the student submitted a PDF, give the teacher
                            # the option to open it.
                            # ------------------------------------------------------

                            if submission["file_path"]:

                                open_pdf = input(
                                    "Open student's PDF? (y/n): "
                                ).lower()

                                if open_pdf == "y":

                                    open_homework_pdf(
                                        submission["file_path"]
                                    )

                            # ------------------------------------------------------
                            # Enter the homework mark.
                            # ------------------------------------------------------

                            mark_value = float(
                                input("\nEnter Mark: ")
                            )

                            total_possible = float(
                                input("Enter Total Possible Mark: ")
                            )
    
                            # ------------------------------------------------------
                            # Validate the mark.
                            # ------------------------------------------------------

                            if total_possible <= 0:

                                print(
                                    "Total Possible Mark must be greater than 0.\n"
                                )

                                continue

                            if mark_value < 0:

                                print(
                                    "Mark cannot be negative.\n"
                                )

                                continue

                            if mark_value > total_possible:

                                print(
                                    "Mark cannot be greater than "
                                    "the Total Possible Mark.\n"
                                )

                                continue

                            # ------------------------------------------------------
                            # Ask the teacher for the homework status.
                            # ------------------------------------------------------

                            print("\n===== HOMEWORK STATUS =====")
                            print("1. Completed")
                            print("2. Not Completed")

                            status_choice = input(
                                "Choose status: "
                            )

                            if status_choice == "1":

                                status = "Completed"

                            elif status_choice == "2":

                                status = "Not Completed"

                            else:

                                print("Invalid status choice.\n")
                                continue

                            # ------------------------------------------------------
                            # Save the mark in SQLite.
                            # ------------------------------------------------------

                            success = mark_homework_submission_db(
                                submission["submission_id"],
                                teacher_number,
                                mark_value,
                                total_possible,
                                status
                            )

                            # ------------------------------------------------------
                            # Display the result.
                            # ------------------------------------------------------

                            if success:

                                print("\n===== HOMEWORK MARKED =====")

                                print(
                                    f"Student : {student['student_name']}"
                                )

                                print(
                                    f"Subject : "
                                    f"{selected_subject['subject_name']}"
                                )

                                print(
                                    f"Homework: {selected_homework['title']}"
                                )

                                print(
                                    f"Mark    : "
                                    f"{mark_value:g}/{total_possible:g}"
                                )

                                print(
                                    f"Status  : {status}"
                                )

                                print()

                        except ValueError as error:

                            # Handle invalid numbers entered by the teacher.
                            print(
                                f"\nError: {error}\n"
                            )

                        except Exception as error:

                            # Handle unexpected errors without crashing
                            # the entire teacher program.
                            print(
                                f"\nError: {error}\n"
                            )
                
                elif choice == "3":
                    break
            
      elif choice3 == 2:

            # ----------------------------------------------------------
            # RECORD ATTENDANCE
            # ----------------------------------------------------------

            try:
                # Ask the teacher for the student's number.
                student_number = int(
                    input("Enter student number: ")
                )

                # ------------------------------------------------------
                # Find the student in SQLite.
                # ------------------------------------------------------

                connection = get_connection()
                cursor = connection.cursor()

                cursor.execute("""
                    SELECT
                        s.student_number,
                        s.student_name,
                        s.grade_id,
                        g.grade_name
                    FROM students s

                    JOIN grades g
                        ON s.grade_id = g.grade_id

                    WHERE s.student_number = ?
                """, (student_number,))

                student = cursor.fetchone()

                # Close the database connection.
                connection.close()

                # ------------------------------------------------------
                # Check whether the student exists.
                # ------------------------------------------------------

                if student is None:
                    print("Student not found.\n")
                    continue

                # ------------------------------------------------------
                # Display the student information.
                # ------------------------------------------------------

                print("\n===== STUDENT FOUND =====")
                print(f"Student Number : {student['student_number']}")
                print(f"Name           : {student['student_name']}")
                print(f"Grade          : {student['grade_name']}")
                print()

                # ------------------------------------------------------
                # Get the teacher's number.
                # ------------------------------------------------------

                teacher_number = current_user["teacher_number"]

                # ------------------------------------------------------
                # Find subjects this teacher teaches for this grade.
                #
                # IMPORTANT:
                # Your teacher_subjects table uses grade_name,
                # not grade_id.
                # ------------------------------------------------------

                assigned_subjects = get_teacher_subjects_for_grade(
                    teacher_number,
                    student["grade_name"]
                )

                # ------------------------------------------------------
                # Check whether the teacher teaches this grade.
                # ------------------------------------------------------

                if not assigned_subjects:
                    print(
                        "You are not assigned to teach any subject "
                        "for this student's grade.\n"
                    )
                    continue

                # ------------------------------------------------------
                # Display the teacher's subjects.
                # ------------------------------------------------------

                print("===== YOUR SUBJECTS =====")

                for number, subject in enumerate(
                    assigned_subjects,
                    start=1
                ):
                    print(
                        f"{number}. {subject['subject_name']}"
                    )

                print()

                # ------------------------------------------------------
                # Ask the teacher to select a subject.
                # ------------------------------------------------------

                subject_choice = int(
                    input("Choose the subject: ")
                )

                # Make sure the choice is valid.
                if (
                    subject_choice < 1
                    or subject_choice > len(assigned_subjects)
                ):
                    print("Invalid subject choice.\n")
                    continue

                # Get the selected subject.
                selected_subject = assigned_subjects[
                    subject_choice - 1
                ]

                # Get the subject ID from the subjects table.
                subject_id = selected_subject["subject_id"]

                # ------------------------------------------------------
                # Choose attendance status.
                # ------------------------------------------------------

                attendance_list = [
                    "Present",
                    "Absent"
                ]

                print("\n===== ATTENDANCE =====")

                for number, status in enumerate(
                    attendance_list,
                    start=1
                ):
                    print(f"{number}. {status}")

                attendance_choice = int(
                    input("Choose attendance status: ")
                )

                # Make sure the attendance choice is valid.
                if (
                    attendance_choice < 1
                    or attendance_choice > len(attendance_list)
                ):
                    print("Invalid attendance choice.\n")
                    continue

                # Get the selected attendance status.
                attendance_status = attendance_list[
                    attendance_choice - 1
                ]

                # ------------------------------------------------------
                # Get the attendance date.
                # ------------------------------------------------------

                attendance_date = input(
                    "Enter Attendance Date (YYYY-MM-DD): "
                )

                # ------------------------------------------------------
                # Save attendance to SQLite.
                # ------------------------------------------------------

                record_attendance_db(
                    student_number,
                    subject_id,
                    teacher_number,
                    attendance_status,
                    attendance_date
                )

                # ------------------------------------------------------
                # Tell the teacher that the attendance was saved.
                # ------------------------------------------------------

                print("\nAttendance saved successfully!")
                print(f"Student : {student['student_name']}")
                print(f"Subject : {selected_subject['subject_name']}")
                print(f"Status  : {attendance_status}")
                print(f"Date    : {attendance_date}")
                print()

            except ValueError as error:
                # Handle invalid numbers and database errors.
                print(f"\nError: {error}\n")
        
        
      elif choice3 == 3:

            # ----------------------------------------------------------
            # ASSIGN HOMEWORK
            # ----------------------------------------------------------

            try:
                # ------------------------------------------------------
                # Get the teacher's number.
                # ------------------------------------------------------
                teacher_number = current_user["teacher_number"]

                # ------------------------------------------------------
                # Show the grades that this teacher teaches.
                # ------------------------------------------------------

                connection = get_connection()
                cursor = connection.cursor()

                cursor.execute("""
                    SELECT DISTINCT
                        ts.grade_name,
                        g.grade_id
                    FROM teacher_subjects ts

                    JOIN grades g
                        ON ts.grade_name = g.grade_name

                    WHERE ts.teacher_number = ?

                    ORDER BY g.grade_id
                """, (teacher_number,))

                teacher_grades = cursor.fetchall()

                # Close the database connection.
                connection.close()

                # ------------------------------------------------------
                # Check whether the teacher has any assignments.
                # ------------------------------------------------------

                if not teacher_grades:
                    print(
                        "You are not assigned to teach any grades.\n"
                    )
                    continue

                # ------------------------------------------------------
                # Display the teacher's grades.
                # ------------------------------------------------------

                print("\n===== YOUR GRADES =====")

                for number, grade in enumerate(
                    teacher_grades,
                    start=1
                ):
                    print(
                        f"{number}. Grade {grade['grade_name']}"
                    )

                print()

                # ------------------------------------------------------
                # Ask the teacher to choose a grade.
                # ------------------------------------------------------

                grade_choice = int(
                    input("Choose the grade: ")
                )

                # Make sure the choice is valid.
                if (
                    grade_choice < 1
                    or grade_choice > len(teacher_grades)
                ):
                    print("Invalid grade choice.\n")
                    continue

                # Get the selected grade.
                selected_grade = teacher_grades[
                    grade_choice - 1
                ]

                grade_id = selected_grade["grade_id"]
                grade_name = selected_grade["grade_name"]

                # ------------------------------------------------------
                # Find the subjects this teacher teaches for
                # the selected grade.
                # ------------------------------------------------------

                assigned_subjects = get_teacher_subjects_for_grade(
                    teacher_number,
                    grade_name
                )

                # ------------------------------------------------------
                # Check whether there are subjects.
                # ------------------------------------------------------

                if not assigned_subjects:
                    print(
                        "You are not assigned to any subject "
                        "for this grade.\n"
                    )
                    continue

                # ------------------------------------------------------
                # Display the subjects.
                # ------------------------------------------------------

                print("\n===== YOUR SUBJECTS =====")

                for number, subject in enumerate(
                    assigned_subjects,
                    start=1
                ):
                    print(
                        f"{number}. {subject['subject_name']}"
                    )

                print()

                # ------------------------------------------------------
                # Ask the teacher to choose a subject.
                # ------------------------------------------------------

                subject_choice = int(
                    input("Choose the subject: ")
                )

                # Make sure the choice is valid.
                if (
                    subject_choice < 1
                    or subject_choice > len(assigned_subjects)
                ):
                    print("Invalid subject choice.\n")
                    continue

                # Get the selected subject.
                selected_subject = assigned_subjects[
                    subject_choice - 1
                ]

                subject_id = selected_subject["subject_id"]

                # ------------------------------------------------------
                # Enter homework information.
                # ------------------------------------------------------

                title = input(
                    "Enter Homework Title: "
                )

                description = input(
                    "Enter Homework Description: "
                )

                due_date = input(
                    "Enter Due Date (YYYY-MM-DD): "
                )

                # ------------------------------------------------------
                # Get today's date for date_posted.
                # ------------------------------------------------------

                date_posted = str(date.today())

                # ------------------------------------------------------
                # Save the homework in SQLite.
                # ------------------------------------------------------

                homework_id = assign_homework_db(
                    title,
                    description,
                    due_date,
                    date_posted,
                    grade_id,
                    subject_id,
                    teacher_number
                )

                # ------------------------------------------------------
                # Tell the teacher the homework was saved.
                # ------------------------------------------------------

                print("\nHomework assigned successfully!")
                print(f"Homework ID : {homework_id}")
                print(f"Grade       : {grade_name}")
                print(f"Subject     : {selected_subject['subject_name']}")
                print(f"Title       : {title}")
                print(f"Due Date    : {due_date}")
                print()

            except ValueError as error:
                # Handle invalid numbers and database validation errors.
                print(f"\nError: {error}\n")
        
        
      elif choice3 == 4: 
        old_pas = int(input("Enter old password: "))
        if old_pas == current_user.password:
          new_pas = int(input("Enter new password: "))
          conf_pas = int(input("Confirm new password: "))
          if new_pas == conf_pas:
            current_user.password = new_pas
            save_teachers()
            print("password changed succefull\n")
          else:
            print("password dont mutch\n")
        else:
          print("Wrong password\n")
          
      elif choice3 == 5:

            # ----------------------------------------------------------
            # VIEW HOMEWORK SUBMISSIONS
            # ----------------------------------------------------------
            #
            # This section is ONLY for viewing submissions.
            #
            # Teachers mark homework from:
            #
            # Enter Marks
            # 
            # 2. Homework marks
            #
            # This prevents having two different places where homework
            # can be marked.
            # ----------------------------------------------------------

            # Get the teacher's number from the logged-in teacher.
            teacher_number = current_user["teacher_number"]

            # Get all homework submissions belonging to this teacher.
            submissions = get_teacher_homework_submissions_db(
                teacher_number
            )

            print("\n===== HOMEWORK SUBMISSIONS =====\n")

            # ----------------------------------------------------------
            # CHECK WHETHER THERE ARE ANY SUBMISSIONS
            # ----------------------------------------------------------

            if not submissions:

                print("No homework submissions found.\n")

            else:

                # ------------------------------------------------------
                # DISPLAY EVERY SUBMISSION
                # ------------------------------------------------------

                for number, submission in enumerate(
                    submissions,
                    start=1
                ):

                    print(
                        f"{number}. {submission['title']}"
                    )

                    print(
                        f"   Subject : "
                        f"{submission['subject_name']}"
                    )

                    print(
                        f"   Student : "
                        f"{submission['student_name']}"
                    )

                    print(
                        f"   Student No. : "
                        f"{submission['student_number']}"
                    )

                    print(
                        f"   Submitted : "
                        f"{submission['submitted_date']}"
                    )

                    print(
                        f"   Status : "
                        f"{submission['status']}"
                    )

                    # --------------------------------------------------
                    # Display the mark if one has been entered.
                    # --------------------------------------------------

                    if submission["mark"] is not None:

                        print(
                            f"   Mark : "
                            f"{submission['mark']:g}/"
                            f"{submission['total_possible']:g}"
                        )

                    else:

                        print(
                            "   Mark : Not marked"
                        )

                    print("------------------------------")

                print("0. Back")

                # ------------------------------------------------------
                # LET THE TEACHER SELECT A SUBMISSION
                # ------------------------------------------------------

                try:

                    submission_choice = int(
                        input(
                            "\nSelect submission: "
                        )
                    )

                    # Return to the teacher menu.
                    if submission_choice == 0:
                        continue

                    # Check that the selected number is valid.
                    if (
                        submission_choice < 1
                        or submission_choice > len(submissions)
                    ):

                        print(
                            "\nInvalid submission choice."
                        )

                        continue

                    # Get the selected submission.
                    selected_submission = submissions[
                        submission_choice - 1
                    ]

                    # --------------------------------------------------
                    # SUBMISSION MENU
                    # --------------------------------------------------

                    while True:

                        print(
                            "\n===== SELECTED SUBMISSION =====\n"
                        )

                        print(
                            f"Homework : "
                            f"{selected_submission['title']}"
                        )

                        print(
                            f"Subject  : "
                            f"{selected_submission['subject_name']}"
                        )

                        print(
                            f"Student  : "
                            f"{selected_submission['student_name']}"
                        )

                        print(
                            f"Student No. : "
                            f"{selected_submission['student_number']}"
                        )

                        print(
                            f"Status   : "
                            f"{selected_submission['status']}"
                        )

                        # --------------------------------------------------
                        # Display the saved mark.
                        # --------------------------------------------------

                        if selected_submission["mark"] is not None:

                            print(
                                f"Mark     : "
                                f"{selected_submission['mark']:g}/"
                                f"{selected_submission['total_possible']:g}"
                            )

                        else:

                            print(
                                "Mark     : Not marked"
                            )

                        # Display the date when the teacher marked it.
                        if selected_submission["marked_date"]:

                            print(
                                f"Marked   : "
                                f"{selected_submission['marked_date']}"
                            )

                        print()

                        # --------------------------------------------------
                        # Submission options
                        # --------------------------------------------------

                        print("1. Open PDF")
                        print("0. Back")

                        submission_option = input(
                            "\nChoose option: "
                        )

                        # --------------------------------------------------
                        # OPEN PDF
                        # --------------------------------------------------

                        if submission_option == "1":

                            # Make sure a PDF exists.
                            if selected_submission["file_path"]:

                                open_homework_pdf(
                                    selected_submission["file_path"]
                                )

                            else:

                                print(
                                    "\nNo PDF file was submitted."
                                )

                        # --------------------------------------------------
                        # BACK TO SUBMISSION LIST
                        # --------------------------------------------------

                        elif submission_option == "0":

                            break

                        else:

                            print(
                                "\nInvalid option."
                            )

                except ValueError:

                    print(
                        "\nPlease enter numbers only."
                    )
          
      elif choice3 == 6:
        print("You logged out\n")
        break
    except ValueError:
      print("Numbers only allowed\n")
      
      

# this func is for registering Admin
def register_admin():
        print("===== PYTHON SCHOOL =====")
        print("Please fill in the form below to create your admin's account.\n")

        admin_name = input("1. Enter your name: ")
        
        password = input("2. Choose your password: ")

        salt = secrets.token_bytes(16)

        password_hash = hashlib.sha256(
            password.encode() + salt
        ).hexdigest()
        password_salt = salt.hex()
        
        category = input("3. Enter your position: ")
        email_address = input("4. Enter your email address: ")
        
        
        try:

            # Send the admin's information to the database function.
            admin_id = register_admin_db(
                admin_name,
                password_hash,
                password_salt,
                category,
                email_address
            )

            print("Admin Number:", admin_id)
            print()

            print("Registration successful!\n")
            print(f"Your Admin Number is: {admin_id}\n")
            
            
            # FETCH the full admin row/dictionary using the new ID
            admin_data, error = login_admin(admin_id)
            
            # Pass the full data dictionary to the menu, NOT just the ID number!
            if admin_data:
                admin_menu(admin_data)

             

        except sqlite3.IntegrityError:
            print("Admin already exists")
            
            


def admin_menu(current_admin):

    print("Logged in as:", current_admin["admin_name"])
    print("Role:", current_admin["category"])

    while True:
        current_term = get_current_school_term_db()

        if current_term:
                            
            print("\n===== CURRENT SCHOOL TERM =====")
            print("School Year:", current_term["school_year"])
            print("Term:", current_term["term_number"])
            print("Start Date:", current_term["start_date"])
            print("End Date:", current_term["end_date"])
            print("--------------------------------------\n")
        
        else:
            print("\nNo active school term found.\n")

        print("\n===== ADMIN PANEL =====\n")

        print("1. View All Students")
        print("2. View All Teachers")
        print("3. View Students Owing Fees")
        print("4. View Students By Grade")
        print("5. View Results By Grade")
        print("6. School Statistics")
        print("7. Student Profile")
        print("8. View Audit_log")
        print("9. Change Password")

        if current_admin["category"] == "Principal":
            print("10. Timetable Management")
            print("11. School Fee Structure")
            print("12. Record Student Fee Payment")
            print("13. Register Admin")
            print("14. Register Student")
            print("15. Register Teacher")
            print("16. Unblock Admin")
            print("17. Unblock Student")
            print("18. Unblock Teacher")
            print("19. Manage Subject")
            print("20. Assign Subject to a teacher")
            print("21. Post School News")
            print("22. Manage school Terms")
            print("23. Register Gardian")
            print("24. Link Guardian to Student")
            print("25. Unblock Guardian")
            print("26. Upload Student Document")
            print("27. Delete Student")
            print("28. Delete Teacher")
            print("29. Delete Admin")
            
            logout_option = "30"
            
        elif current_admin["category"] == "Accounts":
              print("10. School Fee Structure")
              print("11. Record Student Fee Payment")
              print("12. Register Student")
              print("13. Unblock Student")
              print("14. Register Guardian")
              print("15. Link Guardian to Student")
              print("16. Unblock Guardian")
            
              logout_option = "17"  

        else:
            logout_option = "10"

        print(f"{logout_option}. Logout")


        choice = input("Select option: ")
                        
        if choice == "1":
            # Get the latest student information directly from SQLite.
            all_students = get_all_students_db()

            print("==============================")
            print("       PYTHON SCHOOL STUDENTS")
            print("==============================")
            print()

            if not all_students:
                print("No students registered.\n")

            else:
                for student in all_students:

                    print(f"Student No : {student['student_number']}")
                    print(f"Name       : {student['student_name']}")
                    print(f"Grade      : {student['grade_name']}")
                    print(f"Classroom  : {student['classroom']}")
                    print(f"Nationality: {student['nationality']}")
                    print(f"ID Number  : {student['id_number']}")
                    print("------------------------------")
                    print()

        elif choice == "2":
            # Get the latest teacher information directly from SQLite.
            all_teachers = get_all_teachers_db()

            print("==============================")
            print("       PYTHON SCHOOL TEACHERS")
            print("==============================")
            print()

            if not all_teachers:
                print("No teachers registered.\n")

            else:

                for teacher in all_teachers:

                    print(f"Teacher No : {teacher['teacher_number']}")
                    print(f"Name       : {teacher['teacher_name']}")
                    print(f"ID Number  : {teacher['id_number']}")
                    print(f"Gender     : {teacher['gender']}")
                    print(f"Nationality: {teacher['nationality']}")
                    print(f"Email      : {teacher['email_address']}")
                    print(f"Status     : {teacher['status']}")

                    print("Subject / Grade:")

                    if teacher["subjects_and_grades"]:

                        for assignment in teacher["subjects_and_grades"]:

                            print(
                                f"  {assignment['subject_name']}"
                                f" - Grade {assignment['grade_name']}"
                            )

                    else:
                        print("  No subjects or grades assigned.")

                    print("------------------------------")
                    print()

        elif choice == "3":

            # ---------------------------------------------------------
            # STUDENT FEE REPORT
            # ---------------------------------------------------------
            #
            # This menu allows the administrator to:
            #
            # 1. View the whole school's fee report.
            # 2. View the fee report for one grade.
            # 3. Go back.
            #
            # All calculations come from the SQLite database.
            # ---------------------------------------------------------

            while True:

                print("\n===== STUDENT FEE REPORT =====\n")

                print("1. View Whole School Fee Report")
                print("2. View Grade Fee Report")
                print("3. Back")

                fee_choice = input(
                    "\nSelect option: "
                ).strip()

                # =====================================================
                # OPTION 1: WHOLE SCHOOL FEE REPORT
                # =====================================================

                if fee_choice == "1":

                    report = get_school_fee_report_db()

                    if report is None:
                        print("\nNo active school term found.\n")
                        continue

                    print("\n===== WHOLE SCHOOL FEE REPORT =====\n")

                    print(
                        f"School Year        : "
                        f"{report['school_year']}"
                    )

                    print(
                        f"Current Term       : "
                        f"{report['current_term']}"
                    )

                    print(
                        f"Total Students     : "
                        f"{report['total_students']}"
                    )

                    print(
                        f"Students Who Paid  : "
                        f"{report['students_who_paid']}"
                    )

                    print(
                        f"Students Owing     : "
                        f"{report['students_owing']}"
                    )

                    print()

                    print(
                        f"Total Fee Expected  : "
                        f"R{report['total_fee_expected']:,.2f}"
                    )

                    print(
                        f"Total Paid          : "
                        f"R{report['total_paid']:,.2f}"
                    )

                    print(
                        f"Total Outstanding   : "
                        f"R{report['total_outstanding']:,.2f}"
                    )

                    print(
                        "\n----------------------------"
                    )

                    input(
                        "\nPress Enter to return..."
                    )

                # =====================================================
                # OPTION 2: GRADE FEE REPORT
                # =====================================================

                elif fee_choice == "2":

                    # -------------------------------------------------
                    # GRADE FEE REPORT
                    # -------------------------------------------------
                    #
                    # First ask the administrator which grade
                    # they want to inspect.
                    # -------------------------------------------------

                    grade = input(
                        "\nEnter Grade: "
                    ).strip()

                    # -------------------------------------------------
                    # Give the administrator a choice of term.
                    # -------------------------------------------------

                    while True:

                        print(
                            f"\n===== GRADE {grade} FEE REPORT =====\n"
                        )

                        print("1. Term 1")
                        print("2. Term 2")
                        print("3. Term 3")
                        print("4. Term 4")
                        print("5. Back")

                        term_choice = input(
                            "\nSelect option: "
                        ).strip()

                        # -------------------------------------------------
                        # OPTION 5: GO BACK
                        # -------------------------------------------------

                        if term_choice == "5":
                            break

                        # -------------------------------------------------
                        # Convert the menu choice into a term number.
                        # -------------------------------------------------

                        if term_choice in ["1", "2", "3", "4"]:

                            selected_term = int(term_choice)

                        else:

                            print("\nInvalid option.")
                            continue

                        # -------------------------------------------------
                        # Get the current school year.
                        #
                        # We use the current year because the Principal
                        # manages the current school's fee records.
                        # -------------------------------------------------

                        school_year = datetime.now().year

                        # -------------------------------------------------
                        # Get the fee report for this grade and term.
                        # -------------------------------------------------

                        report = get_grade_term_fee_report_db(
                            grade,
                            school_year,
                            selected_term
                        )

                        # -------------------------------------------------
                        # Check whether the grade exists / has students.
                        # -------------------------------------------------

                        if report["total_students"] == 0:

                            print(
                                f"\nNo students found in "
                                f"Grade {grade}.\n"
                            )

                            continue

                        # -------------------------------------------------
                        # Display the selected term's report.
                        # -------------------------------------------------

                        print(
                            f"\n===== GRADE {grade} - "
                            f"TERM {selected_term} FEE REPORT =====\n"
                        )

                        print(
                            f"School Year        : "
                            f"{report['school_year']}"
                        )

                        print(
                            f"Term               : "
                            f"{report['term_number']}"
                        )

                        print(
                            f"Total Students     : "
                            f"{report['total_students']}"
                        )

                        print(
                            f"Students Who Paid  : "
                            f"{report['students_paid']}"
                        )

                        print(
                            f"Students Owing     : "
                            f"{report['students_owing']}"
                        )

                        print()

                        print(
                            f"Fee Expected       : "
                            f"R{report['total_fee_expected']:,.2f}"
                        )

                        print(
                            f"Total Paid         : "
                            f"R{report['total_paid']:,.2f}"
                        )

                        print(
                            f"Outstanding        : "
                            f"R{report['total_outstanding']:,.2f}"
                        )

                        # -------------------------------------------------
                        # Display the students who still owe money
                        # for the selected term.
                        # -------------------------------------------------

                        print(
                            "\n===== STUDENTS OWING FOR "
                            f"TERM {selected_term} =====\n"
                        )

                        found = False

                        for student in report["students"]:

                            if student["balance"] > 0:

                                found = True

                                print(
                                    f"Student Number : "
                                    f"{student['student_number']}"
                                )

                                print(
                                    f"Name           : "
                                    f"{student['student_name']}"
                                )

                                print(
                                    f"Grade          : "
                                    f"{student['grade_name']}"
                                )

                                print(
                                    f"Classroom      : "
                                    f"{student['classroom']}"
                                )

                                print(
                                    f"Term Fee       : "
                                    f"R{student['term_fee']:,.2f}"
                                )

                                print(
                                    f"Paid           : "
                                    f"R{student['amount_paid']:,.2f}"
                                )

                                print(
                                    f"Owing          : "
                                    f"R{student['balance']:,.2f}"
                                )

                                print(
                                    "----------------------------"
                                )

                        if not found:

                            print(
                                "No students owing fees "
                                "for this term."
                            )

                        input(
                            "\nPress Enter to return to "
                            "the term menu..."
                        )

                # =====================================================
                # OPTION 3: BACK
                # =====================================================

                elif fee_choice == "3":

                    break

                else:

                    print(
                        "\nInvalid option."
                    )

        elif choice == "4":
            # Ask the administrator which grade to view.
            grade = input("Enter Grade: ").strip()

            # Get students directly from the SQLite database.
            grade_students = get_students_by_grade_db(grade)

            print(f"\n===== GRADE {grade} STUDENTS =====\n")

            if not grade_students:
                print("No students found in this grade.\n")

            else:
                for student in grade_students:

                    print(
                        f"Student Number : "
                        f"{student['student_number']}"
                    )

                    print(
                        f"Name           : "
                        f"{student['student_name']}"
                    )

                    print(
                        f"ID Number      : "
                        f"{student['id_number']}"
                    )

                    print(
                        f"Nationality    : "
                        f"{student['nationality']}"
                    )

                    print(
                        f"Gender         : "
                        f"{student['gender']}"
                    )

                    print(
                        f"Age            : "
                        f"{student['age']}"
                    )

                    print(
                        f"Grade          : "
                        f"{student['grade_name']}"
                    )

                    print(
                        f"Classroom      : "
                        f"{student['classroom']}"
                    )

                    print(
                        f"Fees Balance   : "
                        f"R{student['fees_balance']:,.2f}"
                    )

                    print("-------------------------------")
                    print()
        elif choice == "5":
            grade = input("Enter Grade: ").strip()
            subject = input("Enter Subject: ").strip()

            results = get_results_by_grade_db(grade, subject)

            print(f"\n===== GRADE {grade} {subject} RESULTS =====\n")

            if not results:
                print("No results found.\n")

            else:
                for result in results:

                    # Calculate the percentage from the mark obtained
                    # and the total possible mark.
                    if result["total_possible"] > 0:
                        percentage = (
                            result["mark_value"]
                            / result["total_possible"]
                        ) * 100
                    else:
                        percentage = 0

                    print(f"Student Number : {result['student_number']}")
                    print(f"Name           : {result['student_name']}")
                    print(f"Subject        : {result['subject_name']}")
                    print(
                        f"Mark           : "
                        f"{result['mark_value']:.1f}"
                        f" / "
                        f"{result['total_possible']:.1f}"
                    )
                    print(f"Percentage     : {percentage:.1f}%")
                    print(f"Exam Date      : {result['exam_date']}")
                    print("----------------------------")
                    print()
        elif choice == "6":
            statistics = get_school_statistics_db()

            print("\n========================================")
            print("           SCHOOL STATISTICS")
            print("========================================\n")


            # ============================================================
            # SCHOOL OVERVIEW
            # ============================================================

            print("SCHOOL OVERVIEW")
            print("----------------------------------------")
            print(
                f"Total Students       : "
                f"{statistics['total_students']}"
            )
            print(
                f"Total Teachers       : "
                f"{statistics['total_teachers']}"
            )
            print(
                f"Total Grades         : "
                f"{statistics['total_grades']}"
            )


            # ============================================================
            # STUDENTS BY GRADE
            # ============================================================

            print("\nSTUDENTS BY GRADE")
            print("----------------------------------------")

            for grade in statistics["students_by_grade"]:
                print(
                    f"Grade {grade['grade_name']:<15}"
                    f": {grade['student_count']}"
                )


            # ============================================================
            # ACADEMIC STATISTICS
            # ============================================================

            print("\nACADEMIC STATISTICS")
            print("----------------------------------------")
            print(
                f"Total Marks Recorded : "
                f"{statistics['total_marks']}"
            )
            print(
                f"Average Mark         : "
                f"{statistics['average_percentage']:.1f}%"
            )
            print(
                f"Highest Mark         : "
                f"{statistics['highest_percentage']:.1f}%"
            )
            print(
                f"Lowest Mark          : "
                f"{statistics['lowest_percentage']:.1f}%"
            )


            # ============================================================
            # ATTENDANCE STATISTICS
            # ============================================================

            print("\nATTENDANCE")
            print("----------------------------------------")
            print(
                f"Total Records        : "
                f"{statistics['total_attendance']}"
            )
            print(
                f"Present              : "
                f"{statistics['present_count']}"
            )
            print(
                f"Absent               : "
                f"{statistics['absent_count']}"
            )
            print(
                f"Attendance Rate      : "
                f"{statistics['attendance_percentage']:.1f}%"
            )


            # ============================================================
            # HOMEWORK STATISTICS
            # ============================================================

            print("\nHOMEWORK")
            print("----------------------------------------")
            print(
                f"Total Homework       : "
                f"{statistics['total_homework']}"
            )
            print(
                f"Submissions          : "
                f"{statistics['total_submissions']}"
            )
            print(
                f"Completed            : "
                f"{statistics['completed_count']}"
            )
            print(
                f"Not Completed        : "
                f"{statistics['not_completed_count']}"
            )
            print(
                f"Average HW Mark      : "
                f"{statistics['average_homework_percentage']:.1f}%"
            )


            # ============================================================
            # FEE STATISTICS
            # ============================================================

            print("\nFEES")
            print("----------------------------------------")
            print(
                f"Total Payments Made  : "
                f"R{statistics['total_fees_paid']:,.2f}"
            )


            print("\n========================================")

        elif choice == "7":

                # Ask the administrator which student profile
                # they want to view.
                try:
                    student_number = int(
                        input("Enter student number: ")
                    )

                except ValueError:

                    print("\nStudent number must be a number.")
                    continue

                # --------------------------------------------------
                # GET STUDENT PROFILE FROM SQLITE
                # --------------------------------------------------

                # This function gets:
                # - Student information
                # - Guardian information
                # - Fee information
                profile = get_student_profile_db(student_number)

                # Check whether the student exists.
                if profile is None:

                    print("\nStudent not found.")
                    continue

                # Separate the three sections of the profile.
                student = profile["student"]
                guardians = profile["guardians"]
                fee_status = profile["fee_status"]

                # --------------------------------------------------
                # DISPLAY STUDENT INFORMATION
                # --------------------------------------------------

                print("\n===== PYTHON SCHOOL STUDENT PROFILE =====\n")

                print(
                    f"Student Number : "
                    f"{student['student_number']}"
                )

                print(
                    f"Name           : "
                    f"{student['student_name']}"
                )

                print(
                    f"ID Number      : "
                    f"{student['id_number']}"
                )

                print(
                    f"Nationality    : "
                    f"{student['nationality']}"
                )

                print(
                    f"Grade          : "
                    f"{student['grade_name']}"
                )

                print(
                    f"Classroom      : "
                    f"{student['classroom']}"
                )

                print(
                    f"Age            : "
                    f"{student['age']}"
                )

                print(
                    f"Gender         : "
                    f"{student['gender']}"
                )

                # --------------------------------------------------
                # DISPLAY FEE INFORMATION
                # --------------------------------------------------

                print("\n--------- FEES ---------\n")

                print(
                    f"Annual Fee       : "
                    f"R{fee_status['annual_fee']:.2f}"
                )

                print(
                    f"Current Term     : "
                    f"Term {fee_status['current_term']}"
                )

                print(
                    f"Previous Balance : "
                    f"R{fee_status['previous_balance']:.2f}"
                )

                print(
                    f"Current Term Due : "
                    f"R{fee_status['current_term_balance']:.2f}"
                )

                print(
                    f"Total Paid       : "
                    f"R{fee_status['total_paid']:.2f}"
                )

                print(
                    f"Total Amount Due : "
                    f"R{fee_status['total_due']:.2f}"
                )

                print(
                    f"Status           : "
                    f"{fee_status['status']}"
                )

                # --------------------------------------------------
                # DISPLAY PARENT / GUARDIAN INFORMATION
                # --------------------------------------------------

                print("\n------ PARENT / GUARDIAN ------\n")

                if not guardians:

                    print("No guardian registered.")

                else:

                    # A student can have more than one guardian.
                    for guardian in guardians:

                        print(
                            f"Name         : "
                            f"{guardian['first_name']} "
                            f"{guardian['last_name']}"
                        )

                        print(
                            f"Relationship : "
                            f"{guardian['relationship']}"
                        )

                        print(
                            f"Phone        : "
                            f"{guardian['phone_number']}"
                        )

                        print(
                            f"Email        : "
                            f"{guardian['email']}"
                        )

                        print(
                            f"Address      : "
                            f"{guardian['address']}"
                        )
                        
                # --------------------------------------------------
                # DISPLAY SUBJECTS
                # --------------------------------------------------
                        
                print("\n--------- SUBJECTS ---------\n")
                
                # Get the student's subjects from the profile data.
                subjects = profile["subjects"]
                
                if not subjects:

                    print("No subjects registered.")

                else:

                    for number, subject in enumerate(subjects, start=1):

                        print(
                            f"{number}. {subject['subject_name']}"
                        )
                        
                # --------------------------------------------------
                # DISPLAY HOMEWORK
                # --------------------------------------------------
                        
                print("\n--------- HOMEWORK ---------\n")

                # Get the homework summary from the profile data.
                homework = profile["homework"]

                # Check whether any homework has been assigned.
                if not homework:

                    print("No homework registered.")
                
                else:

                    # Display the total number of homework assignments.
                    print(
                        f"Total Homework Assigned : "
                        f"{homework['total_assigned']}"
                    )

                    # Display how many were submitted.
                    print(
                        f"Submitted               : "
                        f"{homework['submitted']}"
                    )

                    # Display how many were not submitted.
                    print(
                        f"Not Submitted           : "
                        f"{homework['not_submitted']}"
                    )
                
                # --------------------------------------------------
                # DISPLAY RESULTS
                # --------------------------------------------------

                print("\n--------- RESULTS ---------\n")

                # Get the student's results from the profile data.
                results = profile["results"]

                # Check whether the student has any results.
                if not results:

                    print("No results available.")

                else:

                    # Display each result.
                    for result in results:

                        print(f"Subject      : {result['subject_name']}")
                        print(
                            f"Mark         : "
                            f"{result['mark_value']}/{result['total_possible']}"
                        )
                        print(f"Exam Date    : {result['exam_date']}")
                        print(f"Teacher      : {result['teacher_name']}")
                        
                        
                # --------------------------------------------------
                # DISPLAY ATTENDANCES 
                # --------------------------------------------------

                print("\n--------- ATTENDANCE ---------\n")

                # Get the student's results from the profile data.
                attendance = profile["attendance"]

                # Check whether the student has any attendance.
                if not attendance:

                    print("No attendance available.")

                else:

                    # Display each attendance.
                    for attend in attendance:

                        print(f"Date      : {attend['attendance_Date']}")
                        print(f"Subject   : {attend['subject_name']}")
                        print(f"Status    : {attend['status']}")
                        print(f"Teacher   : {attend['teacher_name']}")
                        
                # --------------------------------------------------
                # DISPLAY TIMETABLE
                # --------------------------------------------------

                print("\n--------- TIMETABLE ---------\n")

                # Get the student's timetable from the profile data.
                timetable = profile["timetable"]

                # Check whether the student has a timetable.
                if not timetable:

                    print("No timetable available.")

                else:

                    # Display each timetable entry.
                    for item in timetable:

                        print(f"Day        : {item['day']}")
                        print(
                            f"Time         : "
                            f"{item['start_time']} - {item['end_time']}"
                        )
                        print(f"Subject    : {item['subject_name']}")
                        print(f"Teacher    : {item['teacher_name']}")
                        print("------------------------------")                       

                print("------------------------------")

        elif choice == "8":
            # Get audit logs directly from SQLite.
            logs = get_admin_logs_db()

            print("\n========================================")
            print("             ADMIN AUDIT LOG")
            print("========================================\n")

            if not logs:
                print("No audit logs found.\n")

            else:
                for log in logs:

                    print("---------------------------")
                    print("Log ID   :", log["log_id"])
                    print("Admin    :", log["admin_name"])
                    print("Role     :", log["category"])
                    print("Action   :", log["action"])
                    print("Date     :", log["action_time"])

                    # Show the student involved when the log
                    # is related to a student.
                    if log["student_number"] is not None:
                        print(
                            "Student  :",
                            log["student_number"]
                        )

                    # Show the teacher involved when the log
                    # is related to a teacher.
                    if log["teacher_number"] is not None:
                        print(
                            "Teacher  :",
                            log["teacher_number"]
                        )

                    print("---------------------------")
                    print()

        elif choice == "9":

            print("\n========================================")
            print("           CHANGE PASSWORD")
            print("========================================\n")

            # Ask for the administrator's current password.
            current_password = input(
                "Enter current password: "
            )

            # Ask for the new password.
            new_password = input(
                "Enter new password: "
            )

            # Ask the administrator to confirm the new password.
            confirm_password = input(
                "Confirm new password: "
            )

            # Make sure both new passwords match before sending
            # them to the database function.
            if new_password != confirm_password:

                print("\nNew passwords do not match.\n")

            else:

                success, message = change_admin_password_db(
                    current_user["admin_id"],
                    current_password,
                    new_password
                )

                if success:
                    print(f"\n{message}\n")
                else:
                    print(f"\nPassword change failed: {message}\n")
        
        elif choice == "10":
            if current_admin["category"] == "Principal":
            
                while True:
                    menu = ["Add Timetable","View Timetable","Edit Timetable","Delet Timetable","Back"]
                    for number, item in enumerate(menu, start = 1):
                        print(number, item)
                    try:
                        choice = int(input("Select your choice: "))
                        print()
                        if choice == 1:

                            # Ask the Principal for the timetable information.
                            grade = input("Enter Grade: ")
                            classroom = input("Enter Classroom: ")
                            day = input("Enter Day: ")
                            start_time = input("Enter Start Time: ")
                            end_time = input("Enter End Time: ")
                            subject = input("Enter Subject: ")

                            # Teacher number is unique, so we use the ID
                            # instead of the teacher's name.
                            teacher_number = int(input("Enter Teacher ID: "))

                            # Save the timetable directly into SQLite.
                            add_timetable_db(
                                grade,
                                classroom,
                                day,
                                start_time,
                                end_time,
                                subject,
                                teacher_number
                            )
                            
                        elif choice == 2:

                            # Get all timetable records from SQLite.
                            timetable = view_timetable_admin()

                            print("\n===== SCHOOL TIMETABLE =====\n")

                            # Check whether there are any timetable records.
                            if not timetable:
                                print("No timetable available.\n")

                            else:

                                # Display each timetable record.
                                for lesson in timetable:

                                    print(f"Timetable ID : {lesson['timetable_id']}")
                                    print(f"Grade        : {lesson['grade_name']}")
                                    print(f"Classroom    : {lesson['classroom']}")
                                    print(f"Day          : {lesson['day']}")
                                    print(
                                        f"Time         : "
                                        f"{lesson['start_time']} - {lesson['end_time']}"
                                    )
                                    print(f"Subject      : {lesson['subject_name']}")
                                    print(f"Teacher ID   : {lesson['teacher_number']}")
                                    print(f"Teacher      : {lesson['teacher_name']}")
                                    print("------------------------------")
                            
                        elif choice == 3:
                            edit_timetable_db()
                            
                        elif choice == 4:
                            delete_timetable_db()
                            
                        elif choice == 5:
                            break            
                    except ValueError:
                        print("Numbers only") 
                        
            elif current_admin["category"] == "Accounts":
                     
                    # -------------------------------------------------
                    # OPTION 1: VIEW FEES STRUCTURE
                    # -------------------------------------------------

                    fees = get_fees_structure_db()

                    print("\n===== SCHOOL FEE STRUCTURE =====\n")

                    if not fees:
                       print("No fee structure found.")

                    else:

                       for fee in fees:

                          print(
                                f"Grade {fee['grade_name']} : "
                                f"R{fee['amount']:,.2f}"
                          )
                        
        elif choice == "11":

            # Only the Principal can manage the school fee structure.
            if current_admin["category"] == "Principal":

                while True:

                    print("\n======= SCHOOL FEES STRUCTURE =======\n")

                    print("1. View Fees Structure")
                    print("2. Update Fees Structure")
                    print("3. Back")

                    choice4 = input("\nSelect your Choice: ").strip()

                    # -------------------------------------------------
                    # OPTION 1: VIEW FEES STRUCTURE
                    # -------------------------------------------------
                    if choice4 == "1":

                        fees = get_fees_structure_db()

                        print("\n===== SCHOOL FEE STRUCTURE =====\n")

                        if not fees:
                            print("No fee structure found.")

                        else:

                            for fee in fees:

                                print(
                                    f"Grade {fee['grade_name']} : "
                                    f"R{fee['amount']:,.2f}"
                                )

                    # -------------------------------------------------
                    # OPTION 2: UPDATE FEES STRUCTURE
                    # -------------------------------------------------
                    elif choice4 == "2":

                        print("\n===== UPDATE SCHOOL FEE =====\n")

                        grade = input(
                            "Enter Grade: "
                        ).strip()

                        # Ask for the new fee.
                        try:
                            new_fee = float(
                                input("Enter New Fee: R").strip()
                            )

                        except ValueError:
                            print("\nInvalid fee amount.")
                            print("Please enter a number.")
                            continue

                        # Prevent negative fees.
                        if new_fee < 0:
                            print("\nFee cannot be negative.")
                            continue

                        # Update the database.
                        update_grade_fee_db(
                            grade,
                            new_fee
                        )

                    # -------------------------------------------------
                    # OPTION 3: BACK
                    # -------------------------------------------------
                    elif choice4 == "3":

                        break

                    else:

                        print("\nInvalid option.")  
                        
            elif current_admin["category"]  == "Accounts":
            
                  student_number = int(input("Enter Student Number: "))  
                  if student_number in students:
                      student = students[student_number] 
                      print("---------------------------\n")
                      print(f"Name: {student.name}")
                      print(f"ID: {student.id_number}")
                      print(f"Grade: {student.grade}")
                      print(f"Fees Balance: {student.fees_balance:.2f}")
                      print("---------------------------\n")
                      
                      print(f"Current Balance: R{student.fees_balance:.2f}")
                      amount_paid = float(input("Enter Amount paid: ")) 
                      
                      if amount_paid > student.fees_balance:
                        print("Amount paid cannot be greater than the outstanding balance.")
                      elif amount_paid <= 0:
                        print("Amount must be greater than zero.")  
                      else:
                        previous_balance = student.fees_balance
                        student.fees_balance -= amount_paid
                        save_students()
                        

                        print("\n===== PAYMENT RECEIPT =====")
                        print(f"Student Number   : {student.student_number}")
                        print(f"Student Name     : {student.name}")
                        print(f"Previous Balance : R{previous_balance:.2f}")
                        print(f"Amount Paid      : R{amount_paid:.2f}")
                        print(f"New Balance      : R{student.fees_balance:.2f}")
                        print("===========================\n")
                        print("Payment recorded successfully.\n")
                        
                  else:
                     print("Student not found")             
                        
        elif choice == "12":
            if current_admin["category"] == "Principal": 
                # ========================================================
                # OPTION 12: RECORD OFFICE STUDENT FEE PAYMENT
                # ========================================================
                #
                # This option is used when a student/parent comes to the
                # school office and makes a fee payment in person.
                #
                # Only the Principal can record office fee payments.
                #
                # The payment is saved in the SQLite fee_payments table.
                # We do NOT change students.fees_balance directly.
                # ========================================================
            
                # --------------------------------------------------------
                # Only the Principal may record office payments.
                # --------------------------------------------------------
                if current_admin["category"] != "Principal":
                    print(
                        "\nOnly the Principal can record office "
                        "fee payments.\n"
                    )
            
                else:
                    print("\n========================================")
                    print("       RECORD OFFICE FEE PAYMENT")
                    print("========================================\n")
            
                    # ----------------------------------------------------
                    # Ask for the student's number.
                    # ----------------------------------------------------
                    try:
                        student_number = int(
                            input("Enter Student Number: ").strip()
                        )
            
                    except ValueError:
                        print("\nInvalid student number.\n")
            
                    else:
                        # ------------------------------------------------
                        # Find the student in SQLite.
                        # ------------------------------------------------
                        connection = get_connection()
                        cursor = connection.cursor()
            
                        try:
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
            
                        finally:
                            connection.close()
            
                        # ------------------------------------------------
                        # Check if the student exists.
                        # ------------------------------------------------
                        if student is None:
                            print("\nStudent not found.\n")
            
                        else:
                            # --------------------------------------------
                            # Get the current active school term.
                            # --------------------------------------------
                            current_school_term = (
                                get_current_school_term_db()
                            )
            
                            if current_school_term is None:
                                print(
                                    "\nNo active school term found.\n"
                                )
            
                            else:
                                # ----------------------------------------
                                # Get the school year and term number.
                                # ----------------------------------------
                                school_year = (
                                    current_school_term["school_year"]
                                )
            
                                current_term = (
                                    current_school_term["term_number"]
                                )
            
                                # ----------------------------------------
                                # Get the student's complete fee status.
                                #
                                # IMPORTANT:
                                # get_student_total_fee_due_db() returns
                                # a dictionary containing all fee details.
                                # ----------------------------------------
                                fee_status = (
                                    get_student_total_fee_due_db(
                                        student_number,
                                        school_year,
                                        current_term
                                    )
                                )
            
                                # ----------------------------------------
                                # Get the actual outstanding balance.
                                #
                                # "remaining_balance" is the final balance
                                # after previous-term and current-term
                                # payment allocation.
                                # ----------------------------------------
                                current_balance = (
                                    fee_status["remaining_balance"]
                                )
            
                                # ----------------------------------------
                                # Display student's information.
                                # ----------------------------------------
                                print("---------------------------")
                                print(
                                    f"Student Number : "
                                    f"{student['student_number']}"
                                )
                                print(
                                    f"Name           : "
                                    f"{student['student_name']}"
                                )
                                print(
                                    f"ID             : "
                                    f"{student['id_number']}"
                                )
                                print(
                                    f"Grade          : "
                                    f"{student['grade_name']}"
                                )
                                print(
                                    f"School Year    : "
                                    f"{school_year}"
                                )
                                print(
                                    f"Current Term   : "
                                    f"{current_term}"
                                )
                                print(
                                    f"Fees Balance   : "
                                    f"R{current_balance:,.2f}"
                                )
                                print("---------------------------\n")
            
                                # ----------------------------------------
                                # Ask for the payment amount.
                                # ----------------------------------------
                                try:
                                    amount_paid = float(
                                        input(
                                            "Enter Amount Paid: "
                                        ).strip()
                                    )
            
                                except ValueError:
                                    print(
                                        "\nInvalid payment amount.\n"
                                    )
            
                                else:
                                    # ------------------------------------
                                    # Validate the payment amount.
                                    # ------------------------------------
                                    if amount_paid <= 0:
                                        print(
                                            "\nAmount must be "
                                            "greater than zero.\n"
                                        )
            
                                    elif amount_paid > current_balance:
                                        print(
                                            "\nAmount paid cannot be "
                                            "greater than the outstanding "
                                            "balance.\n"
                                        )
            
                                    else:
                                        # --------------------------------
                                        # Record the payment in SQLite.
                                        # --------------------------------
                                        (
                                            success,
                                            message,
                                            payment
                                        ) = record_student_fee_payment_db(
                                            student_number,
                                            amount_paid
                                        )
            
                                        # --------------------------------
                                        # Payment failed.
                                        # --------------------------------
                                        if not success:
                                            print(
                                                f"\n{message}\n"
                                            )
            
                                        else:
                                            # ----------------------------
                                            # Print payment receipt.
                                            # ----------------------------
                                            print(
                                                "\n===== PAYMENT RECEIPT ====="
                                            )
            
                                            print(
                                                f"Student Number   : "
                                                f"{payment['student_number']}"
                                            )
            
                                            print(
                                                f"Student Name     : "
                                                f"{payment['student_name']}"
                                            )
            
                                            print(
                                                f"ID Number        : "
                                                f"{payment['id_number']}"
                                            )
            
                                            print(
                                                f"Grade            : "
                                                f"{payment['grade_name']}"
                                            )
            
                                            print(
                                                f"School Year      : "
                                                f"{payment['school_year']}"
                                            )
            
                                            print(
                                                f"Term             : "
                                                f"{payment['term_number']}"
                                            )
            
                                            print(
                                                f"Previous Balance : "
                                                f"R{payment['previous_balance']:,.2f}"
                                            )
            
                                            print(
                                                f"Amount Paid      : "
                                                f"R{payment['amount_paid']:,.2f}"
                                            )
            
                                            print(
                                                f"New Balance      : "
                                                f"R{payment['new_balance']:,.2f}"
                                            )
            
                                            print(
                                                "===========================\n"
                                            )
            
                                            print(
                                                "Payment recorded "
                                                "successfully.\n"
                                            )
                     
            elif current_admin["category"] == "Accounts":
                register_student(current_user)
            
        elif choice == "13":
            
            if current_admin["category"] == "Principal": 
                  register_admin()
                  
            elif current_admin["category"] == "Accounts":
                try:

                    student_number = int(
                        input("Enter student Number: ")
                    )

                    success, message = unlock_student_account(
                        student_number
                    )
                    if success:
                        save_admin_log(
                        current_admin,
                        "Unlocked students account",
                        teacher_number
                    )

                    print(message)

                except ValueError:
                    print("Numbers only.")
                      
        elif choice == "14":
            
            if current_admin["category"] == "Principal":
                register_student()
                
                
            elif current_admin["category"] == "Accounts":
                register_guardian()
                
        elif choice == "15": 
            if current_admin["category"] == "Principal":
                 
              register_teacher()  
              
            elif current_admin["category"] == "Accounts":
                link_guardian_to_student() 
              
        elif choice == "16":
            if current_admin["category"] == "Principal":  
                try:

                    admin_id = int(
                        input("Enter Admin ID: ")
                    )

                    success, message = unlock_admin_account(
                        admin_id
                    )
                    if success:
                        save_admin_log(
                            admin_name=current_admin["admin_name"], # Pass the string username, not the dictionary
                            action="Unlocked Admin account",
                            teacher_number=None,
                            student_number=None,                      # Set to None since there is no student
                            admin_id=admin_id                             # Set to None since there is no target admin ID
                        )

                    print(message)

                except ValueError:
                  print("Numbers only.")
                  
            elif current_admin["category"] == "Accounts":
                unlock_guardian_account()      
              
        elif choice == "17" and current_admin["category"] == "Principal":  
              try:

                    student_number = int(
                        input("Enter student Number: ")
                    )

                    success, message = unlock_student_account(
                        student_number
                    )
                    if success:
                        save_admin_log(
                            admin_name=current_admin["admin_name"], # Pass the string username, not the dictionary
                            action="Unlocked teacher account",
                            teacher_number=None,
                            student_number=student_number,                      # Set to None since there is no student
                            admin_id=None                             # Set to None since there is no target admin ID
                        )

                    print(message)

              except ValueError:
                  print("Numbers only.")
                                                    
        elif choice == "18" and current_admin["category"] == "Principal":  
              try:

                    teacher_number = int(
                        input("Enter Teacher Number: ")
                    )

                    success, message = unlock_teacher_account(
                        teacher_number
                    )
                    if success:
                        save_admin_log(
                            admin_name=current_admin["admin_name"], # Pass the string username, not the dictionary
                            action="Unlocked teacher account",
                            teacher_number=teacher_number,
                            student_number=None,                      # Set to None since there is no student
                            admin_id=None                             # Set to None since there is no target admin ID
                        )

                    print(message)

              except ValueError:
                  print("Numbers only.")
              
        elif choice == "19" and current_admin["category"] == "Principal":  
            while True:
                print("1. Add Subject: ")
                print("2. Delete Subject: ")
                print("3. Back")
                choice = input("Select option: ")
                
                if choice == "1":
                    add_subject()  
                    
                elif choice == "2":
                    delete_subject()     
                
                elif choice == "3":
                    break 
                    
        elif choice == "20" and current_admin["category"] == "Principal":  
            while True:
                print("1. Assign Subject to a teacher: ")
                print("2. Edit assigned Subject: ")
                print("3. Back")
                choice = input("Select option: ")
                
                if choice == "1":
                     assign_subject_teacher()
                    
                elif choice == "2":
                    edit_assigned_subject()    
                
                elif choice == "3":
                    break  
                    
        elif choice == "21" and current_admin["category"] == "Principal":

                print("\n===== POST SCHOOL NEWS =====\n")

                # Ask the administrator for the news information.
                title = input("Enter News Title: ")
                content = input("Enter News Content: ")
                category = input("Enter News Category: ")

                # Get the ID of the administrator who is currently logged in.
                admin_id = current_admin["admin_id"]

                # For now, we are posting general school news.
                # Later we can add grade-specific news.
                grade_id = None

                # Save the news into the SQLite database.
                post_school_news_db(
                    title,
                    content,
                    category,
                    admin_id,
                    grade_id
                )
                
        elif choice == "22" and current_admin["category"] == "Principal":
            while True:
                print("\n===== SCHOOL TERM DATES =====")
                print("1. Set Term One Dates")
                print("2. Set Term Two Dates")
                print("3. Set Term Three Dates")
                print("4. Set Term Four Dates")
                print("5. Back")

                choice = input("\nSelect option: ")

                # Decide which term the Principal wants to manage
                if choice == "1":
                    term_number = 1
                elif choice == "2":
                    term_number = 2
                elif choice == "3":
                    term_number = 3
                elif choice == "4":
                    term_number = 4
                elif choice == "5":
                    break
                else:
                    print("\nInvalid option.")
                    continue

                # Use the current year as the school year
                current_year = datetime.now().year

                print(f"\n===== SET TERM {term_number} DATES =====")
                print(f"School Year: {current_year}")

                # Ask the Principal for the term dates
                start_date = input(
                    "\nEnter start date (YYYY-MM-DD): "
                ).strip()

                end_date = input(
                    "Enter end date (YYYY-MM-DD): "
                ).strip()

                # Check that both dates use the correct format
                try:
                    start = datetime.strptime(start_date, "%Y-%m-%d")
                    end = datetime.strptime(end_date, "%Y-%m-%d")

                except ValueError:
                    print("\nInvalid date format.")
                    print("Please use YYYY-MM-DD.")
                    continue

                # Make sure the end date is not before the start date
                if end < start:
                    print("\nError: End date cannot be before the start date.")
                    continue

                # Save the dates in the school_terms table
                set_school_term_dates_db(
                    current_year,
                    term_number,
                    start_date,
                    end_date
                )
        elif choice == "23" and current_admin["category"] == "Principal":
            register_guardian()
            
        elif choice == "24" and current_admin["category"] == "Principal":
            link_guardian_to_student()
            
        elif choice == "25" and current_admin["category"] == "Principal":
            unlock_guardian_account()  
            
        elif choice == "26" and current_admin["category"] == "Principal":

            print("\n==========================================")
            print("       UPLOAD STUDENT DOCUMENT")
            print("==========================================")

            # ------------------------------------------------------
            # STEP 1 - ASK FOR STUDENT NUMBER
            # ------------------------------------------------------

            try:

                student_number = int(
                    input("\nEnter student number: ").strip()
                )

            except ValueError:

                print("\nStudent number must be a number.")
                continue


            # ------------------------------------------------------
            # STEP 2 - CHECK THAT THE STUDENT EXISTS
            # ------------------------------------------------------

            profile = get_student_profile_db(student_number)

            if profile is None:

                print("\nStudent not found.")
                continue


            student = profile["student"]

            print("\nStudent found.")
            print(
                f"Student Number : {student['student_number']}"
            )
            print(
                f"Student Name   : {student['student_name']}"
            )
            print(
                f"Grade          : {student['grade_name']}"
            )
            print(
                f"Classroom      : {student['classroom']}"
            )


            # ------------------------------------------------------
            # STEP 3 - CHOOSE DOCUMENT TYPE
            # ------------------------------------------------------

            print("\n===== DOCUMENT TYPE =====")
            print("1. Report Card")
            print("2. Circular")
            print("3. Progress Report")
            print("4. Notice")
            print("5. Other")

            document_type_choice = input(
                "\nSelect document type: "
            ).strip()


            # ------------------------------------------------------
            # CONVERT THE MENU CHOICE INTO THE DATABASE TYPE
            # ------------------------------------------------------
            #
            # We keep "Report" in the database because your existing
            # documents already use document_type = "Report".
            #
            # We display "Report Card" to the administrator.
            # ------------------------------------------------------

            document_types = {
                "1": "Report",
                "2": "Circular",
                "3": "Progress Report",
                "4": "Notice",
                "5": "Other"
            }


            if document_type_choice not in document_types:

                print("\nInvalid document type.")
                continue


            document_type = document_types[
                document_type_choice
            ]


            # ------------------------------------------------------
            # STEP 4 - ASK FOR DOCUMENT TITLE
            # ------------------------------------------------------

            document_title = input(
                "\nEnter document title: "
            ).strip()


            if not document_title:

                print("\nDocument title cannot be empty.")
                continue


            # ------------------------------------------------------
            # STEP 5 - SELECT SCHOOL TERM
            # ------------------------------------------------------
            #
            # ONLY Report Card and Progress Report need a term.
            #
            # Circular, Notice and Other documents do NOT need
            # Term 1, Term 2, Term 3 or Term 4.
            # ------------------------------------------------------

            term_number = None


            if document_type in ("Report", "Progress Report"):

                print("\n===== SELECT SCHOOL TERM =====")
                print("1. Term 1")
                print("2. Term 2")
                print("3. Term 3")
                print("4. Term 4")

                term_choice = input(
                    "\nSelect term: "
                ).strip()


                if term_choice not in ("1", "2", "3", "4"):

                    print("\nInvalid term.")
                    continue


                term_number = int(term_choice)


            # ------------------------------------------------------
            # STEP 6 - OPEN ANDROID PDF PICKER
            # ------------------------------------------------------
            #
            # This is your existing working student-document picker.
            #
            # IMPORTANT:
            # We do NOT use the homework PDF picker.
            # ------------------------------------------------------

            selected_pdf = select_student_document_from_android()


            if selected_pdf is None:

                print("\nDocument upload cancelled.")
                continue


            # ------------------------------------------------------
            # STEP 7 - SAVE PDF AND DATABASE RECORD
            # ------------------------------------------------------

            upload_success = upload_student_document_db(
                student_number,
                document_title,
                document_type,
                current_admin["admin_id"],
                selected_pdf,
                term_number
            )


            # ------------------------------------------------------
            # STEP 8 - DISPLAY RESULT
            # ------------------------------------------------------

            if upload_success:

                print("\n==========================================")
                print(" DOCUMENT UPLOADED SUCCESSFULLY")
                print("==========================================")

                print(
                    f"Student        : "
                    f"{student['student_name']}"
                )

                print(
                    f"Student Number : "
                    f"{student_number}"
                )

                print(
                    f"Title          : "
                    f"{document_title}"
                )

                # --------------------------------------------------
                # Display "Report Card" instead of the database
                # value "Report".
                # --------------------------------------------------

                if document_type == "Report":

                    display_type = "Report Card"

                else:

                    display_type = document_type


                print(
                    f"Type           : "
                    f"{display_type}"
                )


                # --------------------------------------------------
                # Show the term only when the document uses a term.
                # --------------------------------------------------

                if term_number is not None:

                    print(
                        f"Term           : "
                        f"{term_number}"
                    )

                else:

                    print(
                        "Term           : Not applicable"
                    )


                print("==========================================")


            else:

                print(
                    "\nThe document upload was not completed."
                )

        elif choice == "27":
            delete_student()
            
        elif choice == "28":
            delete_teacher()
        
        elif choice == "29":
            delete_admin(current_admin)
                   
        elif choice == logout_option:

            print("Logging out...")
            break

        else:
            print("Invalid option")




def register_guardian():
        print("===== PYTHON SCHOOL =====")
        print("Please fill in the form below to create your guardians's account.\n")

        first_name = input("1. Enter your first name: ")
        
        last_name = input("2. Enter your last name: ")
        
        phone_number = input("3. Enter your phone number: ")
        
        email = input("4. Enter your email_address: ")
        
        address = input("5. Enter your home address: ")
        
        password = input("6. Choose your password: ")

        salt = secrets.token_bytes(16)

        password_hash = hashlib.sha256(
            password.encode() + salt
        ).hexdigest()
        password_salt = salt.hex()
        
        
        try:

            # Send the admin's information to the database function.
            guardian_id = register_guardian_db(
                first_name,
                last_name,
                phone_number,
                email,
                address,
                password_hash,
                password_salt,
            )

            print("Guardian Number:", guardian_id)
            print()

            print("Registration successful!\n")
            print(f"Your Guardian Number is: {guardian_id}\n")
            
            
            # 2. FETCH the full admin row/dictionary using the new ID
            guardian_data, error = login_guardian(guardian_id)
            
            # 3. Pass the full data dictionary to the menu, NOT just the ID number!
            if guardian_data:
                guardian_menu(guardian_data)

             

        except sqlite3.IntegrityError:
            print("Guardian already exists")




def guardian_menu(current_user):
  while True:
    current_term = get_current_school_term_db()

    if current_term:
                            
        print("\n===== CURRENT SCHOOL TERM =====")
        print("School Year:", current_term["school_year"])
        print("Term:", current_term["term_number"])
        print("Start Date:", current_term["start_date"])
        print("End Date:", current_term["end_date"])
        print("--------------------------------------\n")
        
    else:
        print("\nNo active school term found.\n")
    
    print("\n===== GUARDIAN PANEL =====\n")
    menu = ["View your Child","View your child's attendance", "View your Child's Homework", "Print your Child's Report Card", "View your child's Timetable", "View your child's School News", "View your Child's Fees Statement", "Make Fee Payment for your Child","View your Child's Payment History","Change your Password","View your Child's Submitted Homework","Logout\n"]

    for number, item in enumerate(menu, start=1):
      print(number, item)
    try:
      choice = int(input("Choose from the menu: "))
      
      # ==================================================
      # OPTION 1 - VIEW CHILDREN
      # ==================================================
      if choice == 1:

             # --------------------------------------------------
             # current_user contains the Guardian Number of the
             # person who successfully logged in.
             #
             # We do NOT ask the guardian to enter a Guardian ID.
             # This prevents them from trying to view another
             # guardian's children.
             # --------------------------------------------------

             guardian_id = current_user["guardian_id"]

             view_guardian_children(
                 guardian_id
             )
      elif choice == 2:
            guardian_id = current_user["guardian_id"]
            view_guardian_child_attendance(guardian_id)
      
      elif choice == 3:
          guardian_id = current_user["guardian_id"]
          view_guardian_child_homework(guardian_id) 
      
      elif choice == 4:
          guardian_id = current_user["guardian_id"]
          print_guardian_child_report_card(guardian_id)  
          
      elif choice == 5:
          guardian_id = current_user["guardian_id"]
          view_guardian_child_timetable(guardian_id)        
      
      elif choice == 6:
        guardian_id = current_user["guardian_id"]
        view_guardian_child_school_news(guardian_id) 
        
      elif choice == 7:
        guardian_id = current_user["guardian_id"]
        view_guardian_child_fees_statement(guardian_id) 
      
      elif choice == 8:
        guardian_id = current_user["guardian_id"]
        make_guardian_child_fee_payment(guardian_id) 
        
      elif choice == 9:
        guardian_id = current_user["guardian_id"]
        view_guardian_child_payment_history(guardian_id)
      
      elif choice == 10:
        guardian_id = current_user["guardian_id"]
        change_guardian_password(guardian_id)
      
      elif choice == 11:
        guardian_id = current_user["guardian_id"]
        view_guardian_child_submitted_homework(guardian_id)
        
      elif choice == 12:
        print("You logged out\n")
        break
    except ValueError:
      print("Numbers only allowed\n")    
          
          





            
def make_fee_payment(student_number):
    # Display the payment heading.
    print("\n===== MAKE FEE PAYMENT =====")

    # Ask the student how much they want to pay.
    amount = float(input("Enter payment amount: R"))

    # Get today's date automatically from the computer.
    payment_date = date.today().isoformat()

    try:
        # Send the payment to the database.
        # record_fee_payment() will automatically determine
        # the school year and term from the payment date.
        new_balance = record_fee_payment(
            student_number,
            amount,
            payment_date
        )

        # Tell the student that the payment was successful.
        print("\nPayment successful!")
        print(f"Payment amount: R{amount:.2f}")
        print(f"Payment date: {payment_date}")
        print(f"New fee balance: R{new_balance:.2f}")

    except ValueError as error:
        # Display an error if the payment fails.
        print(f"\nPayment failed: {error}")
  
  
  
# this function is for the student menu
def student_menu(current_user):
  while True:
    current_term = get_current_school_term_db()

    if current_term:
                            
        print("\n===== CURRENT SCHOOL TERM =====")
        print("School Year:", current_term["school_year"])
        print("Term:", current_term["term_number"])
        print("Start Date:", current_term["start_date"])
        print("End Date:", current_term["end_date"])
        print("--------------------------------------\n")
        
    else:
        print("\nNo active school term found.\n")
    
    print("\n===== STUDENT PANEL =====\n")
    menu2 = ["View Results","View your attendance", "View Homework", "View School Documents", "View Timetable", "View School News", "Fees Statement", "Make Fee Payment","Payment History","Change Password","Submit Homework","Logout\n"]

    for number, item in enumerate(menu2, start=1):
      print(number, item)
    try:
      choice2 = int(input("Choose from the menu: "))
      if choice2 == 1:
          while True:
                print("1. Exam Results: ")
                print("2. Homework Results: ")
                print("3. Back")
                choice = input("Select option: ")
                
                if choice == "1":
                    
                    # ----------------------------------------------------------
                    # Get this student's results from the SQLite database.
                    #
                    # Only results belonging to this student and their
                    # registered subjects will be returned.
                    # ----------------------------------------------------------
                    results = get_student_results_db(
                        current_user["student_number"]
                    )

                    print("\n===== YOUR EXAM RESULTS =====\n")

                    # ----------------------------------------------------------
                    # Check whether the student has any results.
                    # ----------------------------------------------------------
                    if not results:

                        print("No results available.\n")

                    else:

                        # ------------------------------------------------------
                        # Display each result.
                        # ------------------------------------------------------
                        for result in results:

                            print(f"Subject : {result['subject_name']}")
                            print(
                                f"Mark    : "
                                f"{result['mark_value']:.0f} / "
                                f"{result['total_possible']:.0f}"
                            )
                            print(f"Date    : {result['exam_date']}")
                            print(f"Teacher : {result['teacher_name']}")
                            print("----------------------")
                
                
                elif choice == "2":

                    # --------------------------------------------------
                    # HOMEWORK RESULTS
                    # --------------------------------------------------

                    # Get the student's homework and submission information.
                    homework_results = get_student_homework_for_submission_db(
                        current_user["student_number"]
                    )

                    print("\n===== YOUR HOMEWORK RESULTS =====\n")

                    if not homework_results:
                        print("No homework results found.\n")

                    else:

                        for homework in homework_results:

                            # homework[10] = mark
                            # homework[11] = total_possible
                            # homework[12] = marked_date

                            print(f"Homework : {homework['title']}")
                            print(f"Subject  : {homework['subject_name']}")

                            # Check whether the teacher has marked it.
                            if homework["mark"] is not None:

                                print(
                                    f"Mark     : "
                                    f"{homework['mark']} / "
                                    f"{homework['total_possible']}"
                                )

                                print(
                                    f"Status   : "
                                    f"{homework['status']}"
                                )

                                print(
                                    f"Marked   : "
                                    f"{homework['marked_date']}"
                                )

                            else:

                                print("Mark     : Not marked")
                                print(
                                    f"Status   : "
                                    f"{homework['status']}"
                                )

                            print(
                                f"Teacher  : "
                                f"{homework['teacher_name']}"
                            )

                            print("------------------------------")

                    input("\nPress Enter to return...")


                
                elif choice == "3":
                    break
        
        # this is python way for testing
        #print(current_user.results)
        #print()
      elif choice2 == 2:

            # ----------------------------------------------------------
            # Get this student's attendance from the SQLite database.
            #
            # The database function returns attendance only for
            # subjects assigned to this student.
            # ----------------------------------------------------------
            attendance_list = get_student_attendance_db(
                current_user["student_number"]
            )

            print("\n===== ATTENDANCE =====\n")

            # ----------------------------------------------------------
            # Check whether the student has any attendance records.
            # ----------------------------------------------------------
            if not attendance_list:

                print("No attendance records found.")

            else:

                # ------------------------------------------------------
                # Display each attendance record.
                # ------------------------------------------------------
                for attendance in attendance_list:

                    print(f"Date    : {attendance['attendance_date']}")
                    print(f"Subject : {attendance['subject_name']}")
                    print(f"Status  : {attendance['status']}")
                    print(f"Teacher : {attendance['teacher_name']}")
                    print("----------------------")
                    
            
        # this is python way for testing
        #print(current_user.attendance)
        #print()
      elif choice2 == 3:

            # ----------------------------------------------------------
            # Get this student's homework from the SQLite database.
            #
            # The database function only returns homework for:
            #
            # 1. The student's grade
            # 2. Subjects assigned to that student
            # ----------------------------------------------------------
            homework_list = get_student_homework_db(
                current_user["student_number"]
            )

            print("\n===== MY HOMEWORK =====\n")

            # ----------------------------------------------------------
            # Check whether the student has any homework.
            # ----------------------------------------------------------
            if not homework_list:

                print("You currently have no homework.")

            else:

                # ------------------------------------------------------
                # Display each homework assignment.
                # ------------------------------------------------------
                for homework in homework_list:

                    print(f"Subject   : {homework['subject_name']}")
                    print(f"Homework  : {homework['title']}")

                    # Show the description if one was provided.
                    if homework["description"]:
                        print(f"Description: {homework['description']}")

                    print(f"Due Date  : {homework['due_date']}")
                    print(f"Posted By : {homework['teacher_name']}")
                    print("----------------------")
                    
                    
      elif choice2 == 4:
            student_school_documents_menu(
                current_user["student_number"]
            )
                    
      elif choice2 == 5:

            # Get the student's number from the logged-in user.
            student_number = current_user["student_number"]

            # Get this student's timetable directly from SQLite.
            timetable = get_student_timetable_db(student_number)

            print("\n===== PYTHON SCHOOL TIMETABLE =====\n")

            # Check whether the student has any timetable records.
            if not timetable:
                print("No timetable available.\n")

            else:
                # Display every timetable lesson found for the student.
                for lesson in timetable:

                    print(f"Day        : {lesson['day']}")
                    print(
                        f"Time       : "
                        f"{lesson['start_time']} - {lesson['end_time']}"
                    )
                    print(f"Subject    : {lesson['subject_name']}")
                    print(f"Teacher    : {lesson['teacher_name']}")
                    print("---------------------------")
                    
      elif choice2 == 6:

            # Get all school news from the SQLite database.
            news = get_student_school_news_db()

            print("\n===== SCHOOL NEWS =====\n")

            # Check whether there is any news available.
            if not news:
                print("No school news available.\n")

            else:
                # Display each news announcement.
                for item in news:

                    print(f"Title     : {item['title']}")
                    print(f"News      : {item['content']}")
                    print(f"Posted By : {item['admin_name']}")
                    print(f"Date      : {item['date_posted']}")
                    print(f"Category  : {item['category']}")
                    print("----------------------")
      
      # chacking for fees balance
      elif choice2 == 7:
          
            # ----------------------------------------------------------
            # OPTION 7 - FEES STATEMENT
            # ----------------------------------------------------------

            # Get the student number of the person who is currently
            # logged in.
            #
            # current_user contains the logged-in student's information.
            student_number = current_user["student_number"]

            # Display the student's complete fees statement.
            #
            # The function will automatically determine:
            # - School year
            # - Current term
            # - Previous term balances
            # - Current term fee
            # - Payments
            # - Total amount still outstanding
            show_student_fees_statement(student_number)
      
      elif choice2 == 8:
            
            student_number = current_user["student_number"]
            
            # Open the fee payment function for the logged-in student.
            make_fee_payment(student_number)
            
      elif choice2 == 9:
          
        student_number = current_user["student_number"]

        # Show all payments made by this student.
        show_payment_history(student_number)
                  
      # chamging password
      elif choice2 == 10:
        old_pas = int(input("Enter old password: "))
        if old_pas == current_user.password:
          new_pas = int(input("Enter new password: "))
          conf_pas = int(input("Confirm new password: "))
          if new_pas == conf_pas:
            current_user.password = new_pas
            save_students()
            print("password changed succefull\n")
          else:
            print("password dont mutch\n")
        else:
          print("Wrong password\n")
          
      elif choice2 == 11:

                    # --------------------------------------------------
                    # GET HOMEWORK AVAILABLE FOR SUBMISSION
                    # --------------------------------------------------

                    homework_list = get_student_homework_for_submission_db(
                        current_user["student_number"]
                    )

                    print("\n===== SUBMIT HOMEWORK =====\n")

                    # Check whether the student has any homework.
                    if not homework_list:

                        print("You currently have no homework to submit.")

                    else:

                        # Display every homework assignment.
                        for number, homework in enumerate(
                            homework_list,
                            start=1
                        ):

                            print(
                                f"{number}. "
                                f"{homework['title']}"
                            )

                            print(
                                f"   Subject : "
                                f"{homework['subject_name']}"
                            )

                            print(
                                f"   Due     : "
                                f"{homework['due_date']}"
                            )

                            # Check whether this homework has
                            # already been submitted.
                            if homework["submission_id"] is not None:

                                print(
                                    "   Status  : Submitted"
                                )

                                print(
                                    f"   File    : "
                                    f"{homework['file_path']}"
                                )

                            else:

                                print(
                                    "   Status  : Not Submitted"
                                )

                            print("----------------------")

                        print("0. Back")

                        # Ask the student which homework they want
                        # to submit.
                        try:

                            homework_choice = int(
                                input(
                                    "\nSelect homework to submit: "
                                )
                            )

                            # Allow the student to return to the
                            # student menu.
                            if homework_choice == 0:

                                continue

                            # Check that the selected number is valid.
                            if (
                                homework_choice < 1
                                or homework_choice > len(homework_list)
                            ):

                                print(
                                    "\nInvalid homework selection."
                                )

                                continue

                            # Get the selected homework record.
                            selected_homework = homework_list[
                                homework_choice - 1
                            ]

                            # Check whether the homework was
                            # already submitted.
                            if selected_homework["submission_id"] is not None:

                                print(
                                    "\nYou have already submitted "
                                    "this homework."
                                )

                                continue

                            # Open the Android file picker.
                            # The student can select the PDF they created.
                            pdf_path = select_pdf_from_android()

                            # If the student cancelled the file picker,
                            # return to the student menu.
                            if pdf_path is None:

                                continue

                            # Save the PDF and record the submission.
                            save_student_homework_pdf(
                                selected_homework["homework_id"],
                                current_user["student_number"],
                                pdf_path,
                                selected_homework["title"]
                            )

                        except ValueError:

                            print(
                                "\nPlease enter a number."
                            ) 
           
      elif choice2 == 12:
        print("You logged out\n")
        break
    except ValueError:
      print("Numbers only allowed\n")
    



      

while True:
  
  print("======= PYTHON SCHOOL =======")
  menu = ["Student Login","Teacher Login","Admin Login","Guardian Login","Exit"]
  
  for number, item in enumerate(menu, start=1):
    print(number, item)

  try:
    choice = int(input("Choose from the menu: "))
    
    if choice == 1:
        student_number = int(input("Enter your Student Number: "))

        # if current_user:
        current_user, message = log_in(student_number)

        if current_user is None:
               print(message)
        else:  
            # Track the number of password entry attempts in this session
            attempts = 0
            max_attempts = 3

            # 2. Start a loop that runs up to 3 times
            while attempts < max_attempts:  

                
            
                    password = input("Enter your password: ")

                    # 1. Call the function and catch BOTH the success status and the message
                    success, message = login_3timespassword_block(student_number, password)

                    # 2. ONLY log them in if success is True
                    if success:
                        # Fetch the current user data (make sure current_user is loaded correctly here)
                        print(f"=== Welcome {current_user['student_name']} ===")
                        print("status:",current_user["status"])
                        print()
                        student_menu(current_user)
                        break
                    else:
                        # If the database says the account is completely locked out
                        if "locked" in message.lower():
                            print(f"Login Failed: {message}")
                            break # Kick them out to the main menu immediately
            
                        # Otherwise, it was just a normal wrong password
                        attempts += 1
                        remaining = max_attempts - attempts
                        print(f"Login Failed: {message}")
            
                        if remaining > 0:
                            print(f"You have {remaining} attempts left.\n")
                        else:
                            print("Too many wrong attempts in this session.\n")

                        # If they loop 3 times and never get it right, they return to the main menu
              
    elif choice == 2:
        teacher_number = int(input("Enter your teacher number: "))
        current_user, message = login_teacher(teacher_number)

        if current_user is None:
               print(message)
        else:  
            # Track the number of password entry attempts in this session
            attempts = 0
            max_attempts = 3

            # 2. Start a loop that runs up to 3 times
            while attempts < max_attempts:  

                
            
                    password = input("Enter your password: ")

                    # 1. Call the function and catch BOTH the success status and the message
                    success, message = login_3timespassword_block_teacher(teacher_number, password)

                    # 2. ONLY log them in if success is True
                    if success:
                        # Fetch the current user data (make sure current_user is loaded correctly here)
                        print(f"=== Welcome {current_user['teacher_name']} ===")
                        print("status:",current_user["status"])
                        print()
                        teacher_menu(current_user)
                        break
                    else:
                        # If the database says the account is completely locked out
                        if "locked" in message.lower():
                            print(f"Login Failed: {message}")
                            break # Kick them out to the main menu immediately
            
                        # Otherwise, it was just a normal wrong password
                        attempts += 1
                        remaining = max_attempts - attempts
                        print(f"Login Failed: {message}")
            
                        if remaining > 0:
                            print(f"You have {remaining} attempts left.\n")
                        else:
                            print("Too many wrong attempts in this session.\n")

                        # If they loop 3 times and never get it right, they return to the main menu
                        
    elif choice == 3:
        admin_id = input("Enter admin ID: ")
        current_user, message = login_admin(admin_id)

        if current_user is None:
               print(message)
        else:  
            # Track the number of password entry attempts in this session
            attempts = 0
            max_attempts = 3

            # 2. Start a loop that runs up to 3 times
            while attempts < max_attempts:  

                
            
                    password = input("Enter your password: ")

                    # 1. Call the function and catch BOTH the success status and the message
                    success, message = login_3timespassword_block_admin(admin_id, password)

                    # 2. ONLY log them in if success is True
                    if success:
                        # Fetch the current user data (make sure current_user is loaded correctly here)
                        print(f"=== Welcome {current_user['admin_name']} you logged in as {current_user['category']} ===")
                        print("status:",current_user["status"])
                        print()
                        admin_menu(current_user)
                        break
                    else:
                        # If the database says the account is completely locked out
                        if "locked" in message.lower():
                            print(f"Login Failed: {message}")
                            break # Kick them out to the main menu immediately
            
                        # Otherwise, it was just a normal wrong password
                        attempts += 1
                        remaining = max_attempts - attempts
                        print(f"Login Failed: {message}")
            
                        if remaining > 0:
                            print(f"You have {remaining} attempts left.\n")
                        else:
                            print("Too many wrong attempts in this session.\n")

                        # If they loop 3 times and never get it right, they return to the main menu
    
    elif choice == 4:
        guardian_id = input("Enter Guardian ID: ")
        current_user, message = login_guardian(guardian_id)

        if current_user is None:
               print(message)
        else:  
            # Track the number of password entry attempts in this session
            attempts = 0
            max_attempts = 3

            # 2. Start a loop that runs up to 3 times
            while attempts < max_attempts:  

                
            
                    password = input("Enter your password: ")

                    # 1. Call the function and catch BOTH the success status and the message
                    success, message = login_3timespassword_block_guardian(guardian_id, password)

                    # 2. ONLY log them in if success is True
                    if success:
                        # Fetch the current user data (make sure current_user is loaded correctly here)
                        print(f"=== Welcome {current_user['first_name']} ===")
                        print("status:",current_user["status"])
                        print()
                        guardian_menu(current_user)
                        break
                    else:
                        # If the database says the account is completely locked out
                        if "locked" in message.lower():
                            print(f"Login Failed: {message}")
                            break # Kick them out to the main menu immediately
            
                        # Otherwise, it was just a normal wrong password
                        attempts += 1
                        remaining = max_attempts - attempts
                        print(f"Login Failed: {message}")
            
                        if remaining > 0:
                            print(f"You have {remaining} attempts left.\n")
                        else:
                            print("Too many wrong attempts in this session.\n")                   
                        
    elif choice == 5:
      print("Thank you for visiting Python school")
      break
  except ValueError:
    print("Nimbers only allowed")
    
