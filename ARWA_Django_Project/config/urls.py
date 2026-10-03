"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# Now we need to connect the schools app URLs to the main Django project.
# Import Django's admin site.
from django.contrib import admin

# Import path and include so we can connect application URLs.
from django.urls import path, include


# Main URL configuration for the ARWA Django project.
urlpatterns = [

    # Django administration area.
    path("admin/", admin.site.urls),

    # Send the website's root URL to the schools application.
    path("", include("schools.urls")),
]
