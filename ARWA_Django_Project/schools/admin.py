from django.contrib import admin

from django import forms

from .forms import (
    TermForm,
    SchoolForm,
)

# Import all of our school structure and staff models.
from .models import (
    Country,
    Currency,
    ExchangeRate,
    SchoolCurrency,
    Language,
    SchoolLanguage,
    UserLanguagePreference,
    EducationSystem,
    Phase,
    School,
    SchoolType,
    StaffProfile,
    DirectorSchool,
    StaffRole,
    AcademicLevel,
    SchoolAcademicLevel,
    SchoolAcademicLevelSubject,
    Classroom,
    StudentNumberSequence,
    Student,
    Subject,
    SchoolSubject,
    TeacherSubjectClass,
    AcademicYear,
    Term,
    Assessment,
    StudentAssessmentResult,
    ExaminationResult,
    GuardianNumberSequence,
    StaffNumberSequence,
    Guardian,
    StudentGuardian,
    SchoolEvent,
    StudentEnrollment,
    StudentEnrollmentSubject,
    AcademicStructure,
    AcademicStructureSchoolType,
    FeeItem,
    Programme,
    Course,
    SchoolCourse,
    FeeStructure,
    FeeStructureItem,
    StaffSchoolTypeResponsibility,
    EducationSystemSchoolTypeLevel,
    SchoolPhase,
    EducationSystemSchoolTypePhase, 
)


# Register the Education System model so it appears in Django Admin.
admin.site.register(EducationSystem)


# Register the School Type model so it appears in Django Admin.
admin.site.register(SchoolType)


# Register subjects so they can be managed from Django Admin.
admin.site.register(Subject)

# Register school-specific subject offerings.
admin.site.register(SchoolSubject)

# Register teacher, subject, and classroom assignments.
admin.site.register(TeacherSubjectClass)

# Register the student-guardian relationship
# so we can connect students with their guardians
# through the Django Admin site.
admin.site.register(StudentGuardian)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = (
        "flag",
        "name",
        "code",
    )

    search_fields = (
        "name",
        "code",
    )

    ordering = (
        "name",
    )


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    # Show the important language information
    # directly in the Django Admin list.
    list_display = (
        "name",
        "code",
        "django_code",
        "is_active",
        "is_available",
    )
    
    # Allow administrators to edit language availability
    # directly from the language list.
    list_editable = (
        "is_available",
    )

    # Allow administrators to filter languages
    # by their catalogue and translation availability.
    list_filter = (
        "is_active",
        "is_available",
    )

    # Allow administrators to search by language
    # name, ISO code, or Django locale code.
    search_fields = (
        "name",
        "code",
        "django_code",
    )
    
    def save_model(self, request, obj, form, change):
        # Run Django's model validation before saving.
        # This makes sure an available language has
        # a valid Django locale code.
        obj.full_clean()

        # Save the language only after validation succeeds.
        super().save_model(request, obj, form, change)
        

@admin.register(SchoolLanguage)
class SchoolLanguageAdmin(admin.ModelAdmin):

    # Make the language field searchable instead of
    # displaying thousands of languages in a dropdown.
    autocomplete_fields = (
        "language",
    )

    list_display = (
        "school",
        "language",
        "is_active",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "school",
        "language",
        "is_active",
    )

    search_fields = (
        "school__name",
        "language__name",
        "language__code",
    )
    
# Register the School model with its custom Admin configuration.
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    # Use our custom SchoolForm.
    form = SchoolForm

    class Media:
        # Load JavaScript specifically for the School form.
        js = (
            "schools/js/school_form.js",
        )
        

@admin.register(UserLanguagePreference)
class UserLanguagePreferenceAdmin(admin.ModelAdmin):

    # Use a searchable field instead of loading
    # thousands of languages into a dropdown.
    autocomplete_fields = (
        "language",
    )

    list_display = (
        "user",
        "language",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "language__name",
        "language__code",
    )        
        

# Customize how StaffProfile records appear in Django Admin.
@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):

    # Display these fields in the Staff Profile list.
    list_display = (
        "staff_number",
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
    
    
@admin.register(StaffSchoolTypeResponsibility)
class StaffSchoolTypeResponsibilityAdmin(admin.ModelAdmin):

    # Show the staff member, school type,
    # and current responsibility status.
    list_display = (
        "staff_profile",
        "school_type",
        "status",
    )

    # Allow filtering responsibilities by status
    # and school type.
    list_filter = (
        "status",
        "school_type",
    )

    # Allow searching by staff member's name,
    # staff number, and school name.
    search_fields = (
        "staff_profile__user__first_name",
        "staff_profile__user__last_name",
        "staff_profile__staff_number",
        "staff_profile__school__name",
    )    
    
    
 # Register AcadamicLevel with Django Admin.   
# Customize how AcademicLevel records appear in Django Admin.
@admin.register(AcademicLevel)
class AcademicLevelAdmin(admin.ModelAdmin):

    # Display these fields in the Academic Levels list.
    list_display = (
        "education_system",
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
        "education_system",
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
    
    
# Register Student with Django Admin.
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    # Show important student information
    # directly in the Student list.
    list_display = (
        "student_number",
        "first_name",
        "last_name",
        "nationality",
        "school",
        "academic_level",
        "classroom",
        "status",
    )

    # Allow administrators to search
    # for students quickly.
    search_fields = (
        "student_number",
        "first_name",
        "last_name",
        "id_or_passport",
        "school__name",
    )

    # Add useful filters to the Student list.
    list_filter = (
        "school",
        "status",
        "academic_level",
        "classroom",
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


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):

    # Show these fields in the Academic Year list.
    list_display = (
        "school",
        "year",
        "status",
    )

    # Allow the administrator to filter
    # academic years by school and status.
    list_filter = (
        "school",
        "status",
    )

    # Allow searching by school name or year.
    search_fields = (
        "school__name",
        "year",
    )
    
    

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):

    # Use our custom academic-period form.
    form = TermForm

    # Columns displayed in Django Admin.
    list_display = (
        "academic_year",
        "period_type",
        "period_number",
        "name",
        "start_date",
        "end_date",
        "status",
    )

    # Control the order in which periods appear.
    ordering = (
        "academic_year",
        "period_type",
    )

    class Media:

        # Load our JavaScript file on the
        # Term add/edit pages in Django Admin.
        js = (
            "schools/js/term_form.js",
        )
        
    
@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):

    # Show important assessment information
    # directly in the Admin list.
    list_display = (
        "title",
        "school",
        "academic_year",
        "term",
        "teacher",
        "school_subject",
        "classroom",
        "assessment_type",
        "assessment_date",
        "total_possible",
        "status",
    )

    # Allow the administrator to filter
    # assessments using these fields.
    list_filter = (
        "school",
        "academic_year",
        "term",
        "assessment_type",
        "status",
    )

    # Allow the administrator to search
    # for assessments quickly.
    search_fields = (
        "title",
        "teacher__user__first_name",
        "teacher__user__last_name",
        "school_subject__subject__name",
        "classroom__name",
    )

    # Display newest assessments first.
    ordering = (
        "-assessment_date",
        "-created_at",
    )    
    

@admin.register(StudentAssessmentResult)
class StudentAssessmentResultAdmin(admin.ModelAdmin):

    # Show the most important result information
    # directly in the Admin list.
    list_display = (
        "student",
        "assessment",
        "mark",
        "entered_by",
        "created_at",
        "updated_at",
    )

    # Allow administrators to filter results
    # by assessment.
    list_filter = (
        "assessment",
    )

    # Allow administrators to search for
    # students and assessments.
    search_fields = (
        "student__first_name",
        "student__last_name",
        "assessment__title",
    )

    # Display the newest results first.
    ordering = (
        "-created_at",
    )   
    
    
    
@admin.register(ExaminationResult)
class ExaminationResultAdmin(admin.ModelAdmin):
    
    # Original mark is managed automatically by Django.
    exclude = (
        "original_mark",
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Existing examination results are locked.
        # Corrections must go through the controlled
        # ARWA correction process.
        if obj:
            return (
                "assessment",
                "student",
                "mark",
                "original_mark",
                "entered_by",
                "verified_by",
                "verified_at",
                "reported_problem_by",
                "problem_reason",
                "corrected_by",
                "corrected_at",
                "finalized_by",
                "finalized_at",
                "status",
            )
    
        # New examination results can still be entered.
        return ()

    # Show the most important examination
    # result information in the Admin list.
    list_display = (
        "student",
        "assessment",
        "mark",
        "entered_by",
        "verified_by",
        "reported_problem_by",
        "problem_reason",
        "verified_at",
        "status",
        "finalized_by",
        "finalized_at",
    )

    # Allow Admin users to filter examination
    # results by their current workflow status.
    list_filter = (
        "status",
        "assessment",
    )

    # Allow Admin users to search by student,
    # examination title and staff members.
    search_fields = (
        "student__first_name",
        "student__last_name",
        "assessment__title",
        "entered_by__user__first_name",
        "entered_by__user__last_name",
    )

    # Show the newest examination results first.
    ordering = (
        "-created_at",
    )  
    
@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    """
    Controls how Guardian information is displayed
    and managed in the Django Admin site.
    """
    
    # Show important guardian information
    # directly in the Guardian list page.
    list_display = (
        "guardian_number",
        "first_name",
        "last_name",
        "school",
        "phone_number",
        "email",
    )
    
    
    # Show these fields on the Guardian page.
    fields = (
        "guardian_number",
        "user",
        "school",
        "first_name",
        "last_name",
        "id_or_passport",
        "nationality",
        "phone_number",
        "profile_picture",
        "email",
        "address",
    )

    # Guardian Number is generated automatically by ARWA.
    # It must be visible but cannot be changed manually.
    readonly_fields = (
        "guardian_number",
    )    
    

# Register Guardian Number Sequence with Django Admin.
@admin.register(GuardianNumberSequence)
class GuardianNumberSequenceAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "next_number",
        "created_at",
        "updated_at",
    )
    
    # Prevent administrators from manually changing
    # the Guardian Number Sequence.
    readonly_fields = (
        "school",
        "next_number",
        "created_at",
        "updated_at",
    )

    # Prevent accidental deletion of the sequence.
    def has_delete_permission(self, request, obj=None):
        return False

    search_fields = (
        "school__name",
    )


# Register Staff Number Sequence with Django Admin.
@admin.register(StaffNumberSequence)
class StaffNumberSequenceAdmin(admin.ModelAdmin):
    list_display = (
        "school",
        "next_number",
        "created_at",
        "updated_at",
    )
    
    # Prevent administrators from manually changing
    # the Staff Number Sequence.
    readonly_fields = (
        "school",
        "next_number",
        "created_at",
        "updated_at",
    )

    # Prevent accidental deletion of the sequence.
    def has_delete_permission(self, request, obj=None):
        return False

    search_fields = (
        "school__name",
    )        
# =========================================================
# SCHOOL CALENDAR EVENT ADMIN
# =========================================================

@admin.register(SchoolEvent)
class SchoolEventAdmin(admin.ModelAdmin):

    # Show these columns in the events list.
    list_display = (
        "title",
        "school",
        "event_type",
        "start_date",
        "end_date",
        "is_active",
    )

    # Allow events to be filtered by school and category.
    list_filter = (
        "school",
        "event_type",
        "is_active",
    )

    # Allow administrators to search for events.
    list_display_links = ("title",)

    search_fields = (
        "title",
        "description",
        "school__name",
    )

    # Display upcoming events in date order.
    ordering = ("start_date", "title")


class SchoolAcademicLevelSubjectAdminForm(forms.ModelForm):
    # This Admin-only field lets the administrator
    # choose the school first.
    # It is not stored as a separate database field.
    school = forms.ModelChoiceField(
        queryset=School.objects.all(),
        required=True,
        label="School"
    )

    class Meta:
        # This form creates and edits
        # SchoolAcademicLevelSubject records.
        model = SchoolAcademicLevelSubject

        # Show the school first, followed by
        # the academic level, subject, and status.
        fields = (
            "school",
            "school_academic_level",
            "school_subject",
            "status",
        )

    def __init__(self, *args, **kwargs):
        # Initialise the normal Django ModelForm.
        super().__init__(*args, **kwargs)
    
        # Start with no academic levels and no school subjects.
        # We will load the correct ones once we know the school.
        self.fields["school_academic_level"].queryset = (
            SchoolAcademicLevel.objects.none()
        )
    
        self.fields["school_subject"].queryset = (
            SchoolSubject.objects.none()
        )
    
        # First check whether the school was submitted
        # through the form.
        school_id = self.data.get("school")
        
        # If the form has not been submitted yet,
        # check the school ID from the Admin URL.
        if not school_id and hasattr(self, "request"):
            school_id = self.request.GET.get("school")
    
        # If we are editing an existing record and
        # no school was submitted yet, get the school
        # from the existing academic level.
        if not school_id and self.instance.pk:
            school_id = (
                self.instance.school_academic_level.school_id
            )
    
        # If we know the school, load only its data.
        if school_id:
    
            # Show only academic levels belonging
            # to the selected school.
            self.fields["school_academic_level"].queryset = (
                SchoolAcademicLevel.objects.filter(
                    school_id=school_id
                ).order_by("academic_level__order")
            )
    
            # Show only subjects belonging
            # to the selected school.
            self.fields["school_subject"].queryset = (
                SchoolSubject.objects.filter(
                    school_id=school_id
                ).order_by("subject__name")
            )
    
            # When editing an existing record,
            # make sure the School field displays
            # the correct existing school.
            if self.instance.pk:
                self.fields["school"].initial = (
                    self.instance.school_academic_level.school_id
                )
    
    def clean(self):
        # Start with Django's normal form validation.
        cleaned_data = super().clean()
    
        # Get the selected school.
        school = cleaned_data.get("school")
    
        # Get the selected academic level.
        academic_level = cleaned_data.get(
            "school_academic_level"
        )
    
        # Get the selected school subject.
        school_subject = cleaned_data.get(
            "school_subject"
        )
    
        # Make sure the academic level belongs
        # to the selected school.
        if (
            school
            and academic_level
            and academic_level.school_id != school.id
        ):
            self.add_error(
                "school_academic_level",
                "The selected academic level does not belong "
                "to the selected school."
            )
    
        # Make sure the subject belongs
        # to the selected school.
        if (
            school
            and school_subject
            and school_subject.school_id != school.id
        ):
            self.add_error(
                "school_subject",
                "The selected subject does not belong "
                "to the selected school."
            )
    
        # Make sure the academic level and subject
        # belong to the same school.
        if (
            academic_level
            and school_subject
            and academic_level.school_id != school_subject.school_id
        ):
            self.add_error(
                "school_subject",
                "The selected academic level and subject "
                "must belong to the same school."
            )
    
        # Return the validated form data.
        return cleaned_data



# Register SchoolAcademicLevelSubject with Django Admin.
# This allows the administrator to connect a school's
# subject offering to a specific academic level.
@admin.register(SchoolAcademicLevelSubject)
class SchoolAcademicLevelSubjectAdmin(admin.ModelAdmin):
    
    # Use our custom form so the administrator
    # can select the school first.
    form = SchoolAcademicLevelSubjectAdminForm
    
    def get_form(self, request, obj=None, **kwargs):
        # Get the normal Django Admin form.
        Form = super().get_form(request, obj, **kwargs)
    
        # Create a small subclass of our form.
        # This allows us to pass the Admin request
        # into the form.
        class RequestAwareForm(Form):
            def __init__(self, *args, **form_kwargs):
                # Store the Admin request on the form.
                self.request = request
    
                # Continue with the normal form initialisation.
                super().__init__(*args, **form_kwargs)
    
        return RequestAwareForm
    
    class Media:
        # Load the JavaScript file used by
        # the School Academic Level Subject form.
        js = (
            "schools/school_academic_level_subject.js",
        )

    # Show the school, academic level, subject,
    # and current status in the Admin list.
    list_display = (
        "school_academic_level",
        "school_subject",
        "status",
    )

    # Allow administrators to search by school,
    # academic level, and subject name.
    search_fields = (
        "school_academic_level__school__name",
        "school_academic_level__academic_level__name",
        "school_subject__subject__name",
    )

    # Add useful filters.
    list_filter = (
        "status",
        "school_academic_level__school",
        "school_academic_level__academic_level__phase",
    )

    # Display records in a logical order.
    ordering = (
        "school_academic_level__school__name",
        "school_academic_level__academic_level__phase__order",
        "school_academic_level__academic_level__order",
        "school_subject__subject__name",
    )
    


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "school",
        "academic_year",
        "academic_level",
        "classroom",
        "status",
    )

    list_filter = (
        "school",
        "academic_year",
        "status",
    )

    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__student_number",
    )


@admin.register(StudentEnrollmentSubject)
class StudentEnrollmentSubjectAdmin(admin.ModelAdmin):
    list_display = (
        "enrollment",
        "school_subject",
        "created_at",
    )

    list_filter = (
        "school_subject",
        "enrollment__academic_year",
    )

    search_fields = (
        "enrollment__student__first_name",
        "enrollment__student__last_name",
        "enrollment__student__student_number",
        "school_subject__subject__name",
    )


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    # Show these fields in the Currency list.
    list_display = (
        "code",
        "name",
        "symbol",
        "decimal_places",
        "is_active",
    )

    # Allow the administrator to search currencies
    # by their code or name.
    search_fields = (
        "code",
        "name",
    )

    # Allow filtering between active and inactive currencies.
    list_filter = (
        "is_active",
    )

    # Keep currencies ordered alphabetically by code.
    ordering = (
        "code",
    )
    

@admin.register(AcademicStructure)
class AcademicStructureAdmin(admin.ModelAdmin):

    # Show these fields in the Academic Structure list.
    list_display = (
        "name",
        "code",
        "is_active",
    )

    # Allow the administrator to filter
    # active and inactive structures.
    list_filter = (
        "is_active",
    )

    # Allow the administrator to search
    # by structure name or code.
    search_fields = (
        "name",
        "code",
    ) 
    

@admin.register(AcademicStructureSchoolType)
class AcademicStructureSchoolTypeAdmin(admin.ModelAdmin):

    # Show the academic structure and school type
    # in the Admin list.
    list_display = (
        "academic_structure",
        "school_type",
    )

    # Allow filtering by either side of the relationship.
    list_filter = (
        "academic_structure",
        "school_type",
    )

    # Allow searching by academic structure or
    # school type name.
    search_fields = (
        "academic_structure__name",
        "school_type__name",
    )
    
    
@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):

    # Show these fields in the Programme list.
    list_display = (
        "name",
        "code",
        "status",
    )

    # Allow filtering programmes by status.
    list_filter = (
        "status",
    )

    # Allow searching by programme name or code.
    search_fields = (
        "name",
        "code",
    )  
    
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):

    # Show the important course information
    # in the Django Admin course list.
    list_display = (
        "name",
        "code",
        "credits",
        "status",
    )

    # Allow filtering courses by their current status.
    list_filter = (
        "status",
    )

    # Allow searching by course name or course code.
    search_fields = (
        "name",
        "code",
    ) 
    

@admin.register(SchoolCourse)
class SchoolCourseAdmin(admin.ModelAdmin):

    # Show the school, course and current offering status.
    list_display = (
        "school",
        "course",
        "status",
    )

    # Allow filtering by school and status.
    list_filter = (
        "school",
        "status",
    )

    # Allow searching by school name or course name/code.
    search_fields = (
        "school__name",
        "course__name",
        "course__code",
    ) 
    
    
@admin.register(FeeItem)
class FeeItemAdmin(admin.ModelAdmin):

    # Show the fee name and current status.
    list_display = (
        "name",
        "status",
    )

    # Allow filtering by fee status.
    list_filter = (
        "status",
    )

    # Allow searching by fee name.
    search_fields = (
        "name",
    )    
    
    
@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):

    # Show the school, academic year, academic level,
    # and current status in the Admin list.
    list_display = (
        "school",
        "academic_year",
        "academic_level",
        "status",
    )

    # Allow the administrator to filter fee structures
    # by their current status.
    list_filter = (
        "status",
        "academic_year",
        "academic_level",
    )

    # Allow searching by school name and academic level.
    search_fields = (
        "school__name",
        "academic_level__name",
    )    
    
    
@admin.register(FeeStructureItem)
class FeeStructureItemAdmin(admin.ModelAdmin):

    # Show the fee structure, selected fee item,
    # and amount charged.
    list_display = (
        "fee_structure",
        "fee_item",
        "amount",
    )

    # Allow filtering by academic year, academic level,
    # and the selected fee item.
    list_filter = (
        "fee_structure__academic_year",
        "fee_structure__academic_level",
        "fee_item",
    )

    # Allow searching by school, academic level,
    # and fee item name.
    search_fields = (
        "fee_structure__school__name",
        "fee_structure__academic_level__name",
        "fee_item__name",
    )    
    
    
    
@admin.register(EducationSystemSchoolTypeLevel)
class EducationSystemSchoolTypeLevelAdmin(admin.ModelAdmin):

    # Show the education system, school type,
    # and academic level in the Admin list.
    list_display = (
        "education_system",
        "school_type",
        "academic_level",
    )

    # Allow filtering by education system,
    # school type, and academic level.
    list_filter = (
        "education_system",
        "school_type",
        "academic_level",
    )

    # Allow searching for the education system,
    # school type, and academic level.
    search_fields = (
        "education_system__name",
        "school_type__name",
        "academic_level__name",
    )    
    
    
@admin.register(SchoolPhase)
class SchoolPhaseAdmin(admin.ModelAdmin):
    # Show the most important configuration
    # information in the Admin list.
    list_display = (
        "school",
        "school_type",
        "phase",
        "status",
    )

    # Allow filtering by school, school type,
    # phase and status.
    list_filter = (
        "school",
        "school_type",
        "phase",
        "status",
    )

    # Allow searching for schools and custom phases.
    search_fields = (
        "school__name",
        "school_type__name",
        "phase__name",
    ) 
    
    
    
@admin.register(EducationSystemSchoolTypePhase)
class EducationSystemSchoolTypePhaseAdmin(admin.ModelAdmin):
    # Show the education system, school type
    # and phase in the Admin list.
    list_display = (
        "education_system",
        "school_type",
        "phase",
    )

    # Allow filtering by the three important
    # configuration fields.
    list_filter = (
        "education_system",
        "school_type",
        "phase",
    )

    # Allow searching for an education system,
    # school type or phase.
    search_fields = (
        "education_system__name",
        "school_type__name",
        "phase__name",
    )    
    
    
    
@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    # Show the important exchange-rate information
    # directly in the Django Admin list.
    list_display = (
        "base_currency",
        "quote_currency",
        "rate",
        "effective_at",
        "source",
        "fetched_at",
    )

    # Allow the administrator to filter exchange rates
    # by currency and source.
    list_filter = (
        "base_currency",
        "quote_currency",
        "source",
    )

    # Allow searching by currency code/name or source.
    search_fields = (
        "base_currency__code",
        "base_currency__name",
        "quote_currency__code",
        "quote_currency__name",
        "source",
    )

    # Display newest effective rates first.
    ordering = (
        "-effective_at",
    ) 
    


@admin.register(SchoolCurrency)
class SchoolCurrencyAdmin(admin.ModelAdmin):
    # Show the school, currency and role directly
    # in the Admin list.
    list_display = (
        "school",
        "currency",
        "role",
        "created_at",
        "updated_at",
    )

    # Allow filtering by school and currency role.
    list_filter = (
        "school",
        "role",
        "currency",
    )

    # Allow searching by school name, currency code
    # and currency name.
    search_fields = (
        "school__name",
        "currency__code",
        "currency__name",
    )

    # Show the newest configurations first.
    ordering = (
        "-created_at",
    )    
    
       
@admin.register(DirectorSchool)
class DirectorSchoolAdmin(admin.ModelAdmin):
    """
    Manage which schools each Director is authorised
    to oversee.
    """

    # Show the Director and school in the admin list.
    list_display = (
        "director",
        "school",
    )

    # Allow the administrator to quickly find
    # a Director or school.
    search_fields = (
        "director__user__first_name",
        "director__user__last_name",
        "school__name",
    )

    # Make it easy to filter assignments by school.
    list_filter = (
        "school",
    )                      