# Import path to define URL patterns.
from django.urls import path

# Import the dashboard view.
from . import views


# Define the URLs for the schools application.
urlpatterns = [
    # Display the dashboard at the application's home URL.
    # Main ARWA dashboard.
    path("", views.dashboard, name="dashboard"),
    
    # Student registration.
    # This URL will receive the student registration form.
    path(
        "students/register/",
        views.student_register,
        name="student_register"
    ),    
]