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
from .models import Student

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
        
    
    # Make sure the student has been given a password.
    if not password:
        raise ValueError(
            "A student password is required."
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

    # Return both objects created during registration.
    return student, user