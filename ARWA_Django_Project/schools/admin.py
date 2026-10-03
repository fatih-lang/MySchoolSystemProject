from django.contrib import admin

# Import all of our school structure and staff models.
from .models import (
    Country,
    EducationSystem,
    Phase,
    School,
    SchoolType,
    StaffProfile,
    StaffRole,
    AcademicLevel,
    SchoolAcademicLevel,
    Classroom,
    StudentNumberSequence,
    Student,
)


# Register the Country model so it appears in Django Admin.
admin.site.register(Country)


# Register the Education System model so it appears in Django Admin.
admin.site.register(EducationSystem)


# Register the School Type model so it appears in Django Admin.
admin.site.register(SchoolType)


# Register the School model so it appears in Django Admin.
admin.site.register(School)


# Customize how StaffProfile records appear in Django Admin.
@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):

    # Display these fields in the Staff Profile list.
    list_display = (
        "user",
        "school",
        "role",
        "phone_number",
    )

    # Add a search box for finding staff members quickly.
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "school__name",
        "role__name",
    )

    # Add filters to the right side of the Staff Profiles page.
    list_filter = (
        "school",
        "role",
    )
    
    
 # Register AcadamicLevel with Django Admin.   
# Customize how AcademicLevel records appear in Django Admin.
@admin.register(AcademicLevel)
class AcademicLevelAdmin(admin.ModelAdmin):

    # Display these fields in the Academic Levels list.
    list_display = (
        "phase",
        "name",
        "code",
        "order",
        "status",
    )

    # Add a search box for finding academic levels quickly.
    search_fields = (
        "name",
        "code",
        "phase__name",
    )

    # Add filters to the right side of the Academic Levels page.
    list_filter = (
        "phase",
        "status",
    )

    # Display academic levels in their correct order.
    ordering = (
        "phase",
        "order",
    )
    

# Customize how SchoolAcademicLevel records appear in Django Admin.
@admin.register(SchoolAcademicLevel)
class SchoolAcademicLevelAdmin(admin.ModelAdmin):

    # Display these fields in the School Academic Levels list.
    list_display = (
        "school",
        "academic_level",
        "display_name",
        "status",
    )

    # Add a search box to find school academic levels quickly.
    search_fields = (
        "school__name",
        "academic_level__name",
        "academic_level__code",
        "display_name",
    )

    # Add filters to organize the records.
    list_filter = (
        "school",
        "status",
        "academic_level__phase",
    )

    # Sort records by school, then phase and academic level order.
    ordering = (
        "school__name",
        "academic_level__phase__order",
        "academic_level__order",
    )    


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    # Show these columns in the Classroom list.
    list_display = (
        "school",
        "academic_level",
        "name",
        "code",
        "status",
    )

    # Allow us to search for classrooms by these fields.
    search_fields = (
        "school__name",
        "academic_level__academic_level__name",
        "name",
        "code",
    )

    # Add useful filters on the right side.
    list_filter = (
        "school",
        "status",
        "academic_level__academic_level__phase",
    )

    # Display classrooms in a logical order.
    ordering = (
        "school__name",
        "academic_level__academic_level__phase__order",
        "academic_level__academic_level__order",
        "name",
    )



@admin.register(StudentNumberSequence)
class StudentNumberSequenceAdmin(admin.ModelAdmin):
    # Show the school and the next number available.
    list_display = (
        "school",
        "next_number",
        "created_at",
        "updated_at",
    )

    # Allow us to search for a school's sequence.
    search_fields = (
        "school__name",
        "school__school_code",
    )


    

# Register StaffRole with Django Admin.
admin.site.register(StaffRole)


# Register Phase with Django Admin.
admin.site.register(Phase)
