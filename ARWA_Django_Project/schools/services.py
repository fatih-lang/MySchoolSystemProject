# This file will eventually contain the business logic for operations such as:
# Register student
     # ↓
# Generate student number
     # ↓
# Create Django login
     # ↓
# Connect login to Student
     # ↓
# Complete registration




# Import Django's transaction tool.
# This will allow the complete registration process
# to succeed or fail as one database operation.
from django.db import transaction

# Import Django's built-in User model.
# This will be used to create the student's login account.
from django.contrib.auth.models import User

# Import the Student model.
# This will allow the registration service
# to create and connect the student's record.
# Import the models needed for student registration.
from .models import (
    Student,
    StudentNumberSequence,
    StudentEnrollment,
    AcademicYear,
)

@transaction.atomic
def register_student(
    school,
    first_name,
    last_name,
    id_or_passport,
    nationality,
    gender,
    date_of_birth,
    academic_level,
    classroom,
    password,
):

    # Make sure the selected academic level belongs
    # to the school registering this student.
    if academic_level.school_id != school.id:
        raise ValueError(
            "The selected academic level does not belong "
            "to this school."
        )
        
    # Make sure the selected classroom belongs
    # to the school registering this student.
    if classroom.school_id != school.id:
        raise ValueError(
            "The selected classroom does not belong "
            "to this school."
        )

    # Make sure the classroom belongs to the
    # academic level selected for this student.
    if classroom.academic_level_id != academic_level.id:
        raise ValueError(
            "The selected classroom does not belong "
            "to the selected academic level."
        )
        
    # Find the active academic years for this school.
    active_academic_years = AcademicYear.objects.filter(
        school=school,
        status="ACTIVE",
    )

    # A student must be registered into exactly one
    # active academic year.
    if active_academic_years.count() != 1:
        raise ValueError(
            "This school must have exactly one active "
            "academic year before students can be registered."
        )

    # Get the school's active academic year.
    academic_year = active_academic_years.first()    
        
    
    # Make sure the student has been given a password.
    if not password:
        raise ValueError(
            "A student password is required."
        )     
        
    # Make sure this school has a student-number sequence.
    # If one already exists, keep using the existing sequence.
    # Otherwise, create one starting at the default number.
    StudentNumberSequence.objects.get_or_create(
        school=school
    )
    
    # Create the Student record first.
    # Student.save() will automatically generate
    # the student's unique student number.
    student = Student(
        school=school,
        first_name=first_name,
        last_name=last_name,
        id_or_passport=id_or_passport,
        nationality=nationality,
        gender=gender,
        date_of_birth=date_of_birth,
        academic_level=academic_level,
        classroom=classroom,
    )

    # Save the student so ARWA generates the student number.
    student.save()
    
    # Create the student's Django login account.
    # The generated student number becomes the username.
    user = User.objects.create_user(
        username=student.student_number,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    
    # Connect the Django login account to the Student record.
    # This allows ARWA to know which login account belongs
    # to this particular student.
    student.user = user

    # Save the connection between the Student and User.
    student.save(update_fields=["user"])
    
    # Create the student's annual enrolment record.
    # This preserves the student's academic placement
    # for the selected academic year.
    enrollment = StudentEnrollment(
        student=student,
        school=school,
        academic_year=academic_year,
        academic_level=academic_level,
        classroom=classroom,
    )

    # Validate the enrolment before saving it.
    # This checks that the school, year, level and
    # classroom belong together.
    enrollment.full_clean()

    # Save the validated annual enrolment.
    enrollment.save()

    # Return both objects created during registration.
    return student, user