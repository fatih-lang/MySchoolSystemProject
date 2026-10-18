# Import path to define URL patterns.
from django.urls import path

# Import the dashboard view.
from . import views


# Define the URLs for the schools application.
urlpatterns = [
    # Now we need to tell Django:
    # When someone opens the root URL /, use home() instead of dashboard().
    path("", views.home, name="dashboard"),
    
    # ARWA login page.
    path(
        "login/",
        views.login_view,
        name="login",
    ),
    
    # ARWA logout.
    # This URL receives the logout form from the dashboard.
    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),
    
    # Teacher dashboard.
    # This is the destination for authenticated teachers.
    path(
        "teacher-dashboard/",
        views.teacher_dashboard,
        name="teacher_dashboard",
    ),
    
    path(
        "teacher-class/<int:assignment_id>/",
        views.teacher_class,
        name="teacher_class",
    ),
    
    # Guardian dashboard.
    # This is the destination for authenticated guardians.
    path(
        "guardian-dashboard/",
        views.guardian_dashboard,
        name="guardian_dashboard",
    ),
    
    
    # Student Dashboard.
    # This URL opens the dashboard for the logged-in student.
    path(
        "student-dashboard/",
        views.student_dashboard,
        name="student_dashboard",
    ),
    
    
    # Student registration.
    # This URL will receive the student registration form.
    path(
        "students/register/",
        views.student_register,
        name="student_register"
    ), 
    
    # Principal Dashboard
    path(
        "principal-dashboard/",
        views.principal_dashboard,
        name="principal_dashboard",
    ), 
    
    path(
        "language-preference/",
        views.language_preference,
        name="language_preference",
    ),  
    
    path(
        "principal/fee-structure/",
        views.principal_fee_structure,
        name="principal_fee_structure",
    ),
    
    path(
        "director-dashboard/",
        views.director_dashboard,
        name="director_dashboard",
    ),
    
    path(
        "director/select-school-type/<int:school_type_id>/",
        views.director_select_school_type,
        name="director_select_school_type",
    ),
]