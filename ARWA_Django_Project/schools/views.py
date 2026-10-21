
# render() displays our HTML template.
# get_object_or_404() safely finds a database object
# or returns a 404 error if the object does not exist.
from django.shortcuts import (
    render,
    get_object_or_404,
    redirect,
)

from django.utils import timezone

from django.db.models import Q

from django.contrib.auth import authenticate, login, logout

# Converts a date string from the HTML form
# into a Python date object.
from django.utils.dateparse import parse_date

# Protect pages that require an authenticated user.
from django.contrib.auth.decorators import login_required

from django.core.exceptions import PermissionDenied

# HttpResponse is temporarily used to display
# the information received from the registration form.
from django.http import HttpResponse


from .forms import UserLanguagePreferenceForm
from .models import UserLanguagePreference

from datetime import datetime, timedelta

# Import the secure student registration service.
from .services import register_student

from .authorization import (
    can_manage_currency,
    can_manage_currency_in_school_type,
    require_authorization,
    require_school_type_authorization,
)


from .models import (
    Country,
    School,
    SchoolType,
    SchoolAcademicLevel,
    SchoolAcademicLevelSubject,  # Grade-to-subject offerings
    StudentEnrollmentSubject,
    StudentEnrollment,
    EducationSystemSchoolTypePhase,
    EducationSystemSchoolTypeLevel,
    Classroom,
    Student,
    StaffProfile,
    DirectorSchool,
    TeacherSubjectClass,
    AcademicYear,
    Guardian,
    StudentGuardian,
    SchoolEvent,
    Attendance,
    StaffSchoolTypeResponsibility,
    FeeStructure,
    FeeItem,
)  


def home(request):
    # If the user is not logged in,
    # send them to the ARWA login page.
    if not request.user.is_authenticated:
        return redirect("login")

    # Find the dashboard belonging to this user's role.
    dashboard_name = get_user_dashboard(request.user)

    # If the account is not configured for ARWA,
    # log the user out and send them to the login page.
    if dashboard_name is None:
        logout(request)

        return redirect("login")

    # Send the user to the correct dashboard.
    return redirect(dashboard_name)



# Require users to log in before opening the dashboard.
@login_required(login_url="login")
# Display the ARWA School Management Platform dashboard.
def dashboard(request):

    # Get all countries stored in the ARWA database.
    countries = Country.objects.all()

    # Get only active schools available for selection.
    schools = School.objects.filter(status="ACTIVE")

    # Read the selected school from the URL query parameters.
    selected_school_id = request.GET.get("school")

    # Start with no school selected.
    school = None

    # Find the selected active school, if one was provided.
    if selected_school_id:
        school = get_object_or_404(
            School,
            id=selected_school_id,
            status="ACTIVE"
        )

    # Start with empty querysets until a school is selected.
    academic_levels = SchoolAcademicLevel.objects.none()
    classrooms = Classroom.objects.none()
    subject_offerings = SchoolAcademicLevelSubject.objects.none()

    # Load school-specific information only for the selected school.
    if school:

        # Load the active grades offered by this school.
        academic_levels = SchoolAcademicLevel.objects.filter(
            school=school,
            status="ACTIVE"
        ).select_related("academic_level")

        # Load active classrooms belonging to this school.
        classrooms = Classroom.objects.filter(
            school=school,
            status="ACTIVE"
        )

        # Load active subjects configured for active grades
        # at this school. Never mix offerings from other schools.
        subject_offerings = (
            SchoolAcademicLevelSubject.objects.filter(
                school_academic_level__school=school,
                school_academic_level__status="ACTIVE",
                school_subject__school=school,
                school_subject__status="ACTIVE",
                status="ACTIVE",
            )
            .select_related(
                "school_academic_level",
                "school_subject__subject",
            )
            .order_by(
                "school_academic_level",
                "school_subject__subject__name",
            )
        )

    # Send the data to the dashboard template.
    return render(
        request,
        "schools/school.html",
        {
            "schools": schools,
            "countries": countries,
            "academic_levels": academic_levels,
            "classrooms": classrooms,
            "subject_offerings": subject_offerings,
            "selected_school": school,
        }
    )



# Require users to log in before registering a student.
@login_required(login_url="login")
def student_register(request):

    # Check whether the browser sent the form using POST.
    if request.method == "POST":

        # Get the authenticated staff member's profile.
        staff_profile = get_object_or_404(
            StaffProfile,
            user=request.user
        )
        
        # Get the school assigned to that staff member.
        # We do NOT trust the school ID sent by the browser.
        school = get_object_or_404(
            School,
            id=staff_profile.school_id,
            status="ACTIVE"
        )
        
        # Get the academic level selected in the registration form.
        academic_level_id = request.POST.get("academic_level")
        
        # Find the academic level only if it belongs
        # to the authenticated staff member's school.
        academic_level = get_object_or_404(
            SchoolAcademicLevel,
            id=academic_level_id,
            school=school,
            status="ACTIVE"
        )
        
        # Get the classroom selected in the registration form.
        classroom_id = request.POST.get("classroom")
        
        # Find the classroom only if it belongs
        # to the authenticated staff member's school.
        classroom = get_object_or_404(
            Classroom,
            id=classroom_id,
            school=school,
            status="ACTIVE"
        )
        
        
        # Read every subject offering selected in the registration form.
        # getlist() is necessary because a student can select multiple subjects.
        selected_subject_ids = request.POST.getlist(
            "school_academic_level_subjects"
        )

        # Find only active subject offerings for this school
        # and the academic level selected for the student.
        valid_offerings = SchoolAcademicLevelSubject.objects.filter(
            id__in=selected_subject_ids,
            school_academic_level=academic_level,
            school_academic_level__school=school,
            school_academic_level__status="ACTIVE",
            school_subject__school=school,
            school_subject__status="ACTIVE",
        )

        # Count the valid offerings to detect invalid or tampered IDs.
        valid_subject_ids = set(
            str(subject_id)
            for subject_id in valid_offerings.values_list("id", flat=True)
        )

        submitted_subject_ids = set(selected_subject_ids)

        # Reject the registration if any submitted subject is invalid.
        if submitted_subject_ids != valid_subject_ids:
            return HttpResponse(
                "One or more selected subjects are invalid. "
                "Please refresh the registration form and try again."
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
            
            # Get the student's active enrollment for the academic year
            # created by the registration service.
            enrollment = StudentEnrollment.objects.get(
                student=student,
                academic_year=AcademicYear.objects.get(
                    school=school,
                    status="ACTIVE"
                )
            )

            # Save every subject selected during registration
            # against this student's annual enrollment.
            for offering in valid_offerings:
                StudentEnrollmentSubject.objects.create(
                    enrollment=enrollment,
                    school_subject=offering.school_subject,
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
        # Show the proper registration-success page.
        # Pass both the newly created student and the exact
        # annual enrollment created during this registration.
        return render(
            request,
            "schools/student_registered.html",
            {
                "student": student,
                "enrollment": enrollment,
            }
        )

    # If someone visits the registration URL directly,
    # show the normal ARWA dashboard.
    return render(
        request,
        "schools/school.html"
    )
    

# ---------------------------------------------------------
# ARWA USER LOGIN
# ---------------------------------------------------------

def login_view(request):

    # Check whether the user submitted the login form.
    if request.method == "POST":

        # Get the username entered on the login page.
        username = request.POST.get("username")

        # Get the password entered on the login page.
        password = request.POST.get("password")

        # Ask Django to verify the username and password.
        user = authenticate(
            request,
            username=username,
            password=password,
        )

        # If Django successfully authenticated the user...
        if user is not None:

            # Create the user's authenticated session.
            login(request, user)
            
            # Find the correct dashboard for this user
            # based on their ARWA profile and role.
            dashboard = get_user_dashboard(user)
            
            # If Django could not identify this account
            # as a recognised ARWA user...
            if dashboard is None:
            
                # Log the user back out so an unrecognised
                # account does not keep an authenticated session.
                logout(request)
            
                # Show a general error message.
                return render(
                    request,
                    "schools/login.html",
                    {
                        "error_message":
                            "This account is not configured for ARWA."
                    }
                )
            
            # Send the authenticated user to the dashboard
            # selected by our role-routing function.
            return redirect(dashboard)

        # If authentication failed, show the login page
        # again with an error message.
        return render(
            request,
            "schools/login.html",
            {
                "error_message":
                    "Invalid username or password."
            }
        )

    # If the page was opened normally with GET,
    # simply display the login page.
    return render(
        request,
        "schools/login.html"
    )
    
    
# ---------------------------------------------------------
# ARWA USER LOGOUT
# ---------------------------------------------------------

def logout_view(request):

    # End the user's authenticated Django session.
    logout(request)

    # After logging out, send the user back to
    # the central ARWA login page.
    return redirect("login")    
    
    
    
# ---------------------------------------------------------
# ARWA ROLE ROUTING
# ---------------------------------------------------------

def get_user_dashboard(user):

    # -----------------------------------------------------
    # CHECK WHETHER THIS USER IS A STUDENT
    # -----------------------------------------------------

    # Look for a Student profile connected to this
    # Django User account.
    student = Student.objects.filter(
        user=user
    ).select_related(
        "school"
    ).first()

    # If a student profile exists, this user is a student.
    if student:

        # Send the student to the future
        # student dashboard.
        return "student_dashboard"
        
    
    # -----------------------------------------------------
    # CHECK WHETHER THIS USER IS A GUARDIAN
    # -----------------------------------------------------

    # Look for a Guardian profile connected to this
    # Django User account.
    guardian = Guardian.objects.filter(
        user=user
    ).select_related(
        "school"
    ).first()

    # If a Guardian profile exists, this user is a guardian.
    if guardian:

        # Send the guardian to the Guardian dashboard.
        return "guardian_dashboard"    


    # -----------------------------------------------------
    # CHECK WHETHER THIS USER IS A STAFF MEMBER
    # -----------------------------------------------------

    # Look for a StaffProfile connected to this
    # Django User account.
    staff_profile = StaffProfile.objects.filter(
        user=user
    ).select_related(
        "school",
        "role"
    ).first()

    # If a staff profile exists...
    if staff_profile:

        # Get the staff member's role.
        role = staff_profile.role.name

        # Teacher dashboard.
        if role == "Teacher":
            return "teacher_dashboard"

        # Principal dashboard.
        if role == "Principal":
            return "principal_dashboard"

        # Director dashboard.
        if role == "Director":
            return "director_dashboard"

        # Administrator dashboard.
        if role == "Administrator":
            return "administrator_dashboard"


    # -----------------------------------------------------
    # UNKNOWN USER
    # -----------------------------------------------------

    # If the account is not connected to a recognised
    # ARWA profile, do not give it access to a dashboard.
    return None



# ---------------------------------------------------------
# PRINCIPAL DASHBOARD
# ---------------------------------------------------------

@login_required(login_url="login")
def principal_dashboard(request):

    # Find the StaffProfile belonging to the logged-in user.
    staff_profile = get_object_or_404(
        StaffProfile.objects.select_related(
            "school",
            "role",
        ),
        user=request.user,
    )

    # Make sure this account is actually a Principal.
    if staff_profile.role.name != "Principal":
        return HttpResponseForbidden(
            "You do not have permission to access the Principal Dashboard."
        )

    # Get all countries stored in the ARWA database.
    countries = Country.objects.all()

    # The principal should only work with their own school.
    school = staff_profile.school
    
    # ---------------------------------------------------------
    # CURRENT ACADEMIC YEAR
    # ---------------------------------------------------------
    
    # Get the active academic year belonging to this school.
    current_academic_year = AcademicYear.objects.filter(
        school=school,
        status="ACTIVE",
    ).first()
    
    # ---------------------------------------------------------
    # ACTIVE STUDENT ENROLMENTS FOR THE CURRENT YEAR
    # ---------------------------------------------------------
    
    # Get active student enrolments for the current
    # academic year and this Principal's school.
    active_enrollments = StudentEnrollment.objects.filter(
        school=school,
        academic_year=current_academic_year,
        status="ACTIVE",
    ).select_related(
        "academic_level__academic_level"
    )
    
    # ---------------------------------------------------------
     # EXPECTED LEARNERS BY ACADEMIC LEVEL
    # ---------------------------------------------------------
    
    # Store the number of active learners for each academic level.
    expected_by_grade = {}
    
    for enrollment in active_enrollments:
    
        # Get the name of the academic level.
        grade_name = enrollment.academic_level.academic_level.name
    
        # Create the grade in the dictionary if it does not exist.
        if grade_name not in expected_by_grade:
            expected_by_grade[grade_name] = 0
    
        # Add this learner to the grade's expected total.
        expected_by_grade[grade_name] += 1
        
    # ---------------------------------------------------------
    # TODAY'S ATTENDANCE RECORDS
    # ---------------------------------------------------------
    
    # Get today's date.
    today = timezone.localdate()
    
    # Get the date requested by the Principal.
    # If no date was supplied, use today's date.
    attendance_date_string = request.GET.get(
        "attendance_date"
    )
    
    try:
        attendance_date = (
            datetime.strptime(
                attendance_date_string,
                "%Y-%m-%d"
            ).date()
            if attendance_date_string
            else today
        )
    
    except ValueError:
        # If an invalid date was supplied,
        # safely fall back to today's date.
        attendance_date = today
    
    # Calculate the dates used by the navigation buttons.
    previous_attendance_date = (
        attendance_date - timedelta(days=1)
    )
    
    next_attendance_date = (
        attendance_date + timedelta(days=1)
    )
    
    # Determine whether the selected attendance date
    # is today.
    is_attendance_today = (
        attendance_date == today
    )
    
    # Get attendance records for the selected date.
    today_attendance = Attendance.objects.filter(
        school=school,
        date=attendance_date,
        enrollment__academic_year=current_academic_year,
        enrollment__status="ACTIVE",
    ).select_related(
        "student",
        "enrollment__academic_level__academic_level",
    )
    
    # ---------------------------------------------------------
    # LEARNERS WHO ATTENDED TODAY BY ACADEMIC LEVEL
    # ---------------------------------------------------------
    
    # Store unique learners who attended for each academic level.
    attended_students_by_grade = {}
    
    for attendance in today_attendance:
    
        # PRESENT means the learner attended the lesson.
        # LATE also means the learner attended the lesson.
        if attendance.status not in ["PRESENT", "LATE"]:
            continue
    
        # Get the learner's academic level from the
        # annual enrolment attached to the attendance record.
        grade_name = (
            attendance.enrollment
            .academic_level
            .academic_level
            .name
        )
    
        # Create a set for this grade if it does not exist.
        if grade_name not in attended_students_by_grade:
            attended_students_by_grade[grade_name] = set()
    
        # A set prevents the same learner from being
        # counted more than once, even if they attended
        # several lessons today.
        attended_students_by_grade[grade_name].add(
            attendance.student_id
        )
    
    # ---------------------------------------------------------
    # BUILD DAILY ATTENDANCE SUMMARY BY GRADE
    # ---------------------------------------------------------
    
    # Store the final attendance information for each grade.
    attendance_by_grade = []
    
    for grade_name, expected_count in expected_by_grade.items():
    
        # Get the unique learners who attended this grade.
        attended_count = len(
            attended_students_by_grade.get(
                grade_name,
                set()
            )
        )
    
        # Calculate the attendance percentage.
        if expected_count > 0:
            attendance_percentage = (
                attended_count / expected_count
            ) * 100
        else:
            attendance_percentage = 0
    
        # Add this grade's attendance information.
        attendance_by_grade.append({
            "grade_name": grade_name,
            "attended_count": attended_count,
            "expected_count": expected_count,
            "attendance_percentage": round(
                attendance_percentage,
                1
            ),
        })
    
    # ---------------------------------------------------------
    # PRINCIPAL DASHBOARD STATISTICS
    # ---------------------------------------------------------
    
    # Count students belonging only to this school.
    student_count = Student.objects.filter(
        school=school
    ).count()
    
    # Count staff members belonging only to this school.
    teacher_count = StaffProfile.objects.filter(
        school=school,
        role__name="Teacher"
    ).count()
    
    # Count guardians belonging only to this school.
    guardian_count = Guardian.objects.filter(
        school=school
    ).count()
    
    # Get active school events belonging only to the Principal's school.
    school_events = SchoolEvent.objects.filter(
        school=school,
        is_active=True,
    ).order_by(
        "start_date"
    )
    
    # Prepare school events for JavaScript.
    school_events_data = [
        {
            "title": event.title,
            "description": event.description,
            "event_type": event.get_event_type_display(),
            "start_date": event.start_date.isoformat(),
            "end_date": event.end_date.isoformat(),
        }
        for event in school_events
    ]
    
    # Load active academic levels belonging to this school.
    academic_levels = SchoolAcademicLevel.objects.filter(
        school=school,
        status="ACTIVE",
    ).select_related(
        "academic_level"
    )

    # Load active classrooms belonging to this school.
    classrooms = Classroom.objects.filter(
        school=school,
        status="ACTIVE",
    )

    # Load active subjects configured for this school's
    # academic levels.
    subject_offerings = (
        SchoolAcademicLevelSubject.objects.filter(
            school_academic_level__school=school,
            school_academic_level__status="ACTIVE",
            school_subject__school=school,
            school_subject__status="ACTIVE",
            status="ACTIVE",
        )
        .select_related(
            "school_academic_level",
            "school_subject__subject",
        )
        .order_by(
            "school_academic_level",
            "school_subject__subject__name",
        )
    )

    # Send the existing school dashboard template
    # the data it already expects.
    return render(
        request,
        "schools/principal_dashboard.html",
        {
            "schools": School.objects.filter(
                id=school.id,
                status="ACTIVE",
            ),
            "countries": countries,
            "academic_levels": academic_levels,
            "classrooms": classrooms,
            "subject_offerings": subject_offerings,
            "selected_school": school,
            "staff_profile": staff_profile,
            "school_events": school_events_data,
            "student_count": student_count,
            "teacher_count": teacher_count,
            "guardian_count": guardian_count,
            "attendance_by_grade": attendance_by_grade,
            "attendance_date": attendance_date,
            "previous_attendance_date": previous_attendance_date,
            "next_attendance_date": next_attendance_date,
            "today": today,
            "is_attendance_today": is_attendance_today,
        }
    )

# ---------------------------------------------------------
# ARWA TEACHER DASHBOARD
# ---------------------------------------------------------

@login_required(login_url="login")
def teacher_dashboard(request):

    # Get the staff profile belonging to the
    # currently logged-in Django user.
    staff_profile = get_object_or_404(
        StaffProfile,
        user=request.user
    )

    # Make sure this account is actually a Teacher.
    # We do not rely on the URL to determine the role.
    if staff_profile.role.name != "Teacher":

        # If another staff member tries to access
        # the teacher dashboard, send them back
        # to the main dashboard for now.
        return redirect("dashboard")

    # Get the school belonging to this teacher.
    school = get_object_or_404(
        School,
        id=staff_profile.school_id,
        status="ACTIVE"
    )
    
    # Get all active teaching assignments belonging
    # to the currently logged-in teacher.
    teaching_assignments = TeacherSubjectClass.objects.filter(
        teacher=staff_profile,
        status="ACTIVE"
    ).select_related(
        "school_subject__subject",
        "classroom",
        "classroom__academic_level__academic_level",
    )
    
    
    # Get the academic year belonging to this school
    # that contains the current date.
    current_academic_year = AcademicYear.objects.filter(
        school=school,
        status="ACTIVE",
        year=timezone.localdate().year,
    ).first()

    # Find the current term inside that academic year.
    current_term = None

    if current_academic_year:
        current_term = current_academic_year.current_term()

    # Render the teacher dashboard.
    return render(
        request,
        "schools/teacher_dashboard.html",
        {
            "staff_profile": staff_profile,
            "school": school,
            "teaching_assignments": teaching_assignments,
            "current_academic_year": current_academic_year,
            "current_term": current_term,
        }
    )

# when the teacher taps on my classes it's this page which opens up
@login_required(login_url="login")
def teacher_class(request, assignment_id):

    # Get the teacher profile belonging to the
    # currently logged-in Django user.
    staff_profile = get_object_or_404(
        StaffProfile,
        user=request.user
    )

    # Make sure this account is actually a Teacher.
    if staff_profile.role.name != "Teacher":
        return redirect("dashboard")

    # Find the teaching assignment.
    #
    # IMPORTANT:
    # We filter by BOTH the assignment ID and the
    # logged-in teacher.
    #
    # This prevents a teacher from changing the ID
    # in the URL and viewing another teacher's class.
    assignment = get_object_or_404(
        TeacherSubjectClass.objects.select_related(
            "school_subject__subject",
            "classroom",
            "classroom__academic_level__academic_level",
        ),
        id=assignment_id,
        teacher=staff_profile,
        status="ACTIVE",
    )

    # Get the classroom from the authorised assignment.
    classroom = assignment.classroom

    # Get students who belong to this classroom.
    #
    # We also check the school so that students from
    # another school can never appear here.
    students = Student.objects.filter(
        school=staff_profile.school,
        classroom=classroom,
        status="ACTIVE",
    ).order_by(
        "last_name",
        "first_name",
    )

    # Display the teacher's class page.
    return render(
        request,
        "schools/teacher_class.html",
        {
            "staff_profile": staff_profile,
            "school": staff_profile.school,
            "assignment": assignment,
            "classroom": classroom,
            "students": students,
        },
    )
    
    

# ---------------------------------------------------------
# ARWA STUDENT DASHBOARD
# ---------------------------------------------------------

@login_required(login_url="login")
def student_dashboard(request):

    # Find the Student profile connected to the
    # currently logged-in Django User.
    student = get_object_or_404(
        Student,
        user=request.user
    )

    # Get the school that owns this student's record.
    # Never trust a school ID supplied by the browser.
    school = get_object_or_404(
        School,
        id=student.school_id,
        status="ACTIVE"
    )

    # Load active calendar events belonging only
    # to this student's school.
    school_events = list(
        SchoolEvent.objects.filter(
            school=school,
            is_active=True,
        ).order_by(
            "start_date",
            "title",
        ).values(
            "title",
            "description",
            "event_type",
            "start_date",
            "end_date",
        )
    )

    # Display the Student Dashboard template.
    return render(
        request,
        "schools/student_dashboard.html",
        {
            "student": student,
            "school": school,
            "school_events": school_events,
        }
    )
    

# ---------------------------------------------------------
# ARWA GUARDIAN DASHBOARD
# ---------------------------------------------------------

# Require the guardian to be logged in before
# accessing the Guardian dashboard.
@login_required(login_url="login")
def guardian_dashboard(request):

    # Get the Guardian profile belonging to the
    # currently logged-in Django User.
    guardian = get_object_or_404(
        Guardian,
        user=request.user
    )

    # Get the school belonging to this Guardian.
    #
    # We use the Guardian profile rather than trusting
    # a school ID from the browser.
    school = get_object_or_404(
        School,
        id=guardian.school_id,
        status="ACTIVE"
    )

    # Get all active students connected to this Guardian.
    #
    # StudentGuardian is the relationship table between
    # Guardians and Students.
    #
    # We also verify that the student's school matches
    # the Guardian's school.
    student_guardians = (
        StudentGuardian.objects
        .filter(
            guardian=guardian,
            student__school=school,
            student__status="ACTIVE",
        )
        .select_related(
            "student",
            "student__academic_level",
            "student__classroom",
        )
    )
    
    # -----------------------------------------------------
    # LOAD ACTIVE EVENTS FOR THIS GUARDIAN'S SCHOOL
    # -----------------------------------------------------

    # Retrieve active events belonging to this school.
    school_events = list(
        SchoolEvent.objects.filter(
            school=school,
            is_active=True,
        ).order_by(
            "start_date",
            "title",
        ).values(
            "title",
            "description",
            "event_type",
            "start_date",
            "end_date",
        )
    )
    
    # Render the Guardian dashboard.
    return render(
       request,
       "schools/guardian_dashboard.html",
       {
          "guardian": guardian,
          "school": school,
          "student_guardians": student_guardians,
          "school_events": school_events,
       }
    )
        
    
# The purpose of the view is simple:
# Take the language selected by the 
# logged-in user and save it into their 
# existing UserLanguagePreference record.
@login_required
def language_preference(request):
    """
    Allow a logged-in ARWA user to select
    their preferred interface language.
    """

    # Get the user's existing language preference.
    # If one does not exist yet, create it in memory
    # without saving it to the database immediately.
    preference, created = UserLanguagePreference.objects.get_or_create(
        user=request.user
    )

    # Process the form when the user submits it.
    if request.method == "POST":
        form = UserLanguagePreferenceForm(
            request.POST,
            instance=preference,
        )

        # Make sure the submitted language is valid.
        if form.is_valid():

            # Save the selected language preference.
            form.save()

            # Return the user to their previous page.
            return redirect(request.META.get("HTTP_REFERER", "/"))

    else:
        # Display the user's current language preference.
        form = UserLanguagePreferenceForm(
            instance=preference,
        )

    # Display the language preference page.
    return render(
        request,
        "schools/language_preference.html",
        {
            "form": form,
        },
    )


@login_required
def principal_fee_structure(request):
    """
    Start the Principal Fee Structure process.

    ARWA first checks which school types the logged-in
    Principal is currently responsible for.

    Only ACTIVE responsibilities are allowed.
    """

    # Get the StaffProfile belonging to the
    # currently logged-in user.
    staff_profile = request.user.staffprofile
    
    # Get the active fee items available to this school.
    #
    # ARWA includes:
    # 1. Global fee items shared across the platform.
    # 2. Custom fee items created specifically for this school.
    #
    # Fee items belonging to other schools are never included.
    available_fee_items = (
        FeeItem.objects
        .filter(
            Q(school__isnull=True) |
            Q(school=staff_profile.school),
            status="ACTIVE",
        )
        .order_by("name")
    )

    # Find the active academic year for this school.
    # ARWA uses the school's own academic years,
    # keeping each school's fee structures separate.
    current_academic_year = (
        AcademicYear.objects
        .filter(
            school=staff_profile.school,
            status="ACTIVE",
        )
        .first()
    )

    # Get only the school-type responsibilities that
    # are currently active for this staff member.
    responsibilities = (
        StaffSchoolTypeResponsibility.objects
        .filter(
            staff_profile=staff_profile,
            status="ACTIVE",
        )
        .select_related("school_type")
    )

    # Extract the actual SchoolType objects.
    school_types = [
        responsibility.school_type
        for responsibility in responsibilities
    ]

    # If the Principal has no active responsibility,
    # they should not be allowed to manage Fee Structure.
    if not school_types:
        return render(
            request,
            "schools/principal_fee_structure.html",
            {
                "school_type": None,
                "no_access": True,
            },
        )

    # If the Principal is responsible for only one
    # school type, ARWA already knows which one it is.
    #
    # We therefore do NOT show a school-type selector.
    if len(school_types) == 1:

        # The Principal's single responsible school type.
        school_type = school_types[0]

        # Get the education system selected for this school.
        education_system = staff_profile.school.education_system

        # ARWA's education system determines whether
        # this school uses phases.
        uses_phases = education_system.uses_phases

        # Start with an empty phase list.
        phases = []

        # Only retrieve phases when the education system
        # is configured to use phases.
        if uses_phases:

            # Get the phase mappings that belong to
            # this education system and school type.
            phase_mappings = (
                EducationSystemSchoolTypePhase.objects
                .filter(
                    education_system=education_system,
                    school_type=school_type,
                )
                .select_related("phase")
            )

            # Extract the actual Phase objects from
            # the valid mappings.
            phases = [
                mapping.phase
                for mapping in phase_mappings
            ]

        # Check whether the Principal selected a phase.
        # The phase ID comes from the GET parameter
        # created by the phase selection buttons.
        selected_phase_id = request.GET.get("phase")

        # Start with no selected phase.
        selected_phase = None

        # If the Principal selected a phase,
        # find that phase from the valid phases only.
        if selected_phase_id:

            selected_phase = next(
                (
                    phase
                    for phase in phases
                    if str(phase.id) == selected_phase_id
                ),
                None,
            )

        # Store the academic levels that are valid
        # for the selected school type and phase.
        academic_levels = []

        # Start with no selected academic level.
        #
        # This variable is created before the phase block
        # so it always exists when we send data to the template.
        selected_academic_level = None

        # Start with no fee structure.
        #
        # This variable is also created before the phase block
        # so it always exists when we send data to the template.
        fee_structure = None

        # Only look for academic levels when a phase
        # has actually been selected.
        if selected_phase:

            # Get academic-level mappings for:
            #
            # 1. The school's education system
            # 2. The Principal's school type
            # 3. The selected phase
            #
            # This prevents ARWA from showing academic
            # levels that do not belong to this combination.
            level_mappings = (
                EducationSystemSchoolTypeLevel.objects
                .filter(
                    education_system=education_system,
                    school_type=school_type,
                    academic_level__phase=selected_phase,
                )
                .select_related("academic_level")
            )

            # Extract the actual AcademicLevel objects
            # from the mapping records.
            academic_levels = [
                mapping.academic_level
                for mapping in level_mappings
            ]

            # Read the academic level selected by
            # the Principal from the URL.
            selected_academic_level_id = request.GET.get(
                "academic_level"
            )

            # If an academic level was selected,
            # verify that it is one of the valid levels
            # retrieved above.
            if selected_academic_level_id:

                selected_academic_level = next(
                    (
                        academic_level
                        for academic_level in academic_levels
                        if str(academic_level.id)
                        == selected_academic_level_id
                    ),
                    None,
                )

            # Only search for a fee structure when:
            #
            # 1. A valid academic level was selected.
            # 2. The school has an active academic year.
            if (
                selected_academic_level
                and current_academic_year
            ):

                fee_structure = (
                    FeeStructure.objects
                    .filter(
                        school=staff_profile.school,
                        academic_year=current_academic_year,
                        academic_level=selected_academic_level,
                        status="ACTIVE",
                    )
                    .first()
                )

        # Send all of the verified information to
        # the Fee Structure template.
        return render(
            request,
            "schools/principal_fee_structure.html",
            {
                "school_type": school_type,
                "education_system": education_system,
                "uses_phases": uses_phases,
                "phases": phases,
                "selected_phase": selected_phase,
                "academic_levels": academic_levels,
                "selected_academic_level": selected_academic_level,
                "fee_structure": fee_structure,
                "available_fee_items": available_fee_items,
                "current_academic_year": current_academic_year,
            },
        )

    # If the Principal is responsible for multiple
    # school types, ARWA must allow them to choose
    # which school type they want to manage.
    return render(
        request,
        "schools/principal_fee_structure_select_school_type.html",
        {
            "school_types": school_types,
        },
    )
    
    
    
@login_required(login_url="/login/")
@require_authorization(can_manage_currency)
def director_dashboard(request):
    """
    Director dashboard entry point.

    This view is protected by backend authorization.
    Only an authorized Director can access it.

    The dashboard template will contain the Director's
    executive interface.
    """

    return render(
        request,
        "schools/director_dashboard.html",
    )
    
@login_required
def director_school_oversight(request):
    """
    Display all schools that the authenticated Director
    is authorised to oversee.
    """

    # Get the authenticated user's StaffProfile.
    staff_profile = request.user.staffprofile

    # Get every school assigned to this Director through
    # the DirectorSchool relationship.
    director_schools = DirectorSchool.objects.filter(
        director=staff_profile
    ).select_related("school")

    # Send all assigned schools to the template.
    context = {
        "director_schools": director_schools,
    }

    return render(
        request,
        "schools/director_school_oversight.html",
        context,
    )
    


@login_required
def director_school_oversight_detail(request, school_id):
    """
    Display detailed oversight information for one school.

    The Director can only access a school that has been
    explicitly assigned to them through DirectorSchool.
    """

    # Get the authenticated user's StaffProfile.
    staff_profile = request.user.staffprofile

    # Find the DirectorSchool assignment.

    # This is the security check.
    # If this Director is not assigned to the requested
    # school, Django will return a 404 instead of exposing
    # another school's information.
    assignment = get_object_or_404(
        DirectorSchool.objects.select_related("school"),
        director=staff_profile,
        school_id=school_id,
    )

    # Get the authorised school from the assignment.
    school = assignment.school
    
    """
    Get all active academic levels offered by this school.

    A school may have multiple school types, so each
    academic-level record also carries its school type.

    select_related() loads the related records efficiently
    because we will need their information in the template.
    """
    school_academic_levels = (
        SchoolAcademicLevel.objects
        .filter(
            school=school,
            status="ACTIVE",
        )
        .select_related(
            "school_type",
            "academic_level",
        )
        .order_by(
            "school_type__name",
            "academic_level__phase__order",
            "academic_level__order",
        )
    )
    
    # Group the school's academic levels by school type.
    #
    # This allows the template to display each school type
    # once, with its academic levels grouped underneath it.
    #
    # The queryset above already provides the correct ordering,
    # so we simply preserve that order while creating the groups.
    academic_levels_by_school_type = {}
    
    for school_level in school_academic_levels:
    
        school_type_id = school_level.school_type_id
    
        if school_type_id not in academic_levels_by_school_type:
    
            academic_levels_by_school_type[school_type_id] = {
                "school_type": school_level.school_type,
                "levels": [],
            }
    
        academic_levels_by_school_type[school_type_id]["levels"].append(
            school_level
        )
    
    # Find the school's currently active academic year.
    #
    # This ensures the Director sees the academic year
    # that the school is actually operating in, rather
    # than simply displaying the most recently created year.
    current_academic_year = AcademicYear.objects.filter(
        school=school,
        status="ACTIVE",
    ).first()
    
    # Send the authorised school to the template.
    context = {
        "school": school,
        "current_academic_year": current_academic_year,
        "school_academic_levels": school_academic_levels,
        "academic_levels_by_school_type": (
            academic_levels_by_school_type.values()
        ),
    }
        
    return render(
        request,
        "schools/director_school_oversight_detail.html",
        context,
    )
    
    
    
@login_required(login_url="/login/")
def director_select_school_type(request, school_type_id):
    """
    Select an authorized school-type context for the Director.

    The selected school type must:

        1. Exist.
        2. Belong to the Director's school.
        3. Have an ACTIVE responsibility assigned to the Director.

    Selecting a context does not grant permission for
    individual operations. Sensitive operations must still
    perform their own backend authorization checks.
    """

    # -----------------------------------------------------
    # GET THE DIRECTOR'S STAFF PROFILE
    # -----------------------------------------------------

    staff_profile = getattr(
        request.user,
        "staffprofile",
        None,
    )

    # A valid ARWA staff profile is required.
    if not staff_profile:
        raise PermissionDenied

    # -----------------------------------------------------
    # FIND THE REQUESTED SCHOOL TYPE
    # -----------------------------------------------------

    school_type = SchoolType.objects.filter(
        pk=school_type_id
    ).first()

    # The requested school type must exist.
    if not school_type:
        raise PermissionDenied

    # -----------------------------------------------------
    # CHECK SCHOOL OWNERSHIP
    # -----------------------------------------------------

    if not staff_profile.school.school_types.filter(
        pk=school_type.pk
    ).exists():
        raise PermissionDenied

    # -----------------------------------------------------
    # CHECK ACTIVE RESPONSIBILITY
    # -----------------------------------------------------

    if not staff_profile.school_type_responsibilities.filter(
        school_type=school_type,
        status="ACTIVE",
    ).exists():
        raise PermissionDenied

    # -----------------------------------------------------
    # STORE THE AUTHORIZED CONTEXT
    # -----------------------------------------------------

    request.session["director_school_type_id"] = school_type.id

    return HttpResponse(
        "Director school-type context selected."
    )
    
    
    
    
    
    
    
    
    
    
    