# render() displays our HTML template.
# get_object_or_404() safely finds a database object
# or returns a 404 error if the object does not exist.
from django.shortcuts import render, get_object_or_404

# Converts a date string from the HTML form
# into a Python date object.
from django.utils.dateparse import parse_date

# HttpResponse is temporarily used to display
# the information received from the registration form.
from django.http import HttpResponse

from django.http import HttpResponse

# Import the secure student registration service.
from .services import register_student

from .models import Country, School, SchoolAcademicLevel,Classroom, Student


# Display the ARWA School Management Platform dashboard.
def dashboard(request):

    # Get all countries stored in the ARWA database.
    countries = Country.objects.all()
    
    # Get all active schools that can be selected during registration.
    schools = School.objects.filter(
        status="ACTIVE"
    )

    # Get our test school.
    # Later, the logged-in school will determine this automatically.
    school = School.objects.get(
        school_code="ARWA"
    )

    # Get only the academic levels that belong to this school.
    academic_levels = SchoolAcademicLevel.objects.filter(
        school=school,
        status="ACTIVE"
    )
    
    # Get only the active classrooms that belong to this school.
    classrooms = Classroom.objects.filter(
        school=school,
        status="ACTIVE"
    )

    # Send the countries and academic levels to the HTML template.
    return render(
        request,
        "schools/school.html",
        {   
            "schools": schools,
            "countries": countries,
            "academic_levels": academic_levels,
            "classrooms": classrooms,
        }
    )


def student_register(request):

    # Check whether the browser sent the form using POST.
    if request.method == "POST":

        # Get the school selected by the person registering the student.
        school_id = request.POST.get("school")

        # Find the selected school, but only if it is ACTIVE.
        school = get_object_or_404(
            School,
            id=school_id,
            status="ACTIVE"
        )
        
        # Get the academic level selected in the registration form.
        academic_level_id = request.POST.get("academic_level")
        
        # Find the academic level selected by the user.
        academic_level = get_object_or_404(
            SchoolAcademicLevel,
            id=academic_level_id
        )
        
        # Get the classroom selected in the registration form.
        classroom_id = request.POST.get("classroom")
        
        # Find the classroom selected by the user.
        classroom = get_object_or_404(
            Classroom,
            id=classroom_id
        )
        
        # Get the nationality selected in the registration form.
        nationality_id = request.POST.get("nationality")
        
        # Find the country selected by the user.
        nationality = get_object_or_404(
            Country,
            id=nationality_id
        )
        
        # Read the student's information from the submitted form.
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        id_or_passport = request.POST.get("id_or_passport")
        
        # Make sure the required student information
        # was actually submitted to the server.
        if not first_name or not last_name or not id_or_passport:
            return HttpResponse(
                "First name, surname, and ID/passport are required."
            )
        
        # Check whether this ID/passport is already registered
        # at the selected school.
        if Student.objects.filter(
            school=school,
            id_or_passport=id_or_passport
        ).exists():

            # Stop registration and display a clear message.
            return HttpResponse(
                "This ID or passport number is already registered "
                "at this school."
            )
        
        # Get the date entered in the registration form.
        # The browser sends it as text, so we convert it
        # into a proper Python date object.
        date_of_birth = parse_date(request.POST.get("date_of_birth"))
        
        # Make sure the date of birth is valid.
        if date_of_birth is None:
            return HttpResponse(
                "Please enter a valid date of birth."
            )
            
        gender = request.POST.get("gender")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        
        # Make sure all the remaining required fields
        # were actually submitted to the server.
        if not gender or not nationality or not academic_level or not classroom or not password:
            return HttpResponse(
                "Gender, nationality, academic level, classroom, "
                "and password are required."
            )
        
        # Make sure the two passwords entered by the user match.
        if password != confirm_password:
            return HttpResponse(
                "The passwords do not match."
            )
            
        # Make sure the password is long enough
        # to provide basic protection for the student's account.
        if len(password) < 8:
            return HttpResponse(
                "Password must be at least 8 characters long."
            )     
            
        try:
            # Register the student using the secure registration service.
            student, user = register_student(
                school=school,
                first_name=first_name,
                last_name=last_name,
                id_or_passport=id_or_passport,
                nationality=nationality,
                gender=gender,
                date_of_birth=date_of_birth,
                academic_level=academic_level,
                classroom=classroom,
                password=password,
            )
        
        except ValueError as error:
        
            # Display the security/validation error without creating
            # an incomplete student registration.
            return HttpResponse(
                f"Registration rejected: {error}"
            )    

        # Show the proper registration-success page.
        # Pass the newly created student to the template
        # so the page can display the saved information.
        return render(
            request,
            "schools/student_registered.html",
            {
                "student": student,
            }
        )

    # If someone visits the registration URL directly,
    # show the normal ARWA dashboard.
    return render(
        request,
        "schools/school.html"
    )