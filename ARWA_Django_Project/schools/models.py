from django.db import models

# Import transaction tools so student-number generation
# can be performed safely as one database operation.
from django.db import transaction


class Country(models.Model):
    # Store the country's official name.
    name = models.CharField(max_length=100)

    # Store the country's short code, such as ZA or UG.
    code = models.CharField(max_length=2)
    unique=True
    
    def save(self, *args, **kwargs):
        # Automatically convert the country code to uppercase.
        self.code = self.code.upper()

        # Save the country normally.
        super().save(*args, **kwargs)

    def __str__(self):
        # Show the country name when Django displays this object.
        return self.name


class EducationSystem(models.Model):
    # The name of the education system or curriculum.
    name = models.CharField(max_length=200)

    # Connect this education system to the country where it is used.
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE
    )

    def __str__(self):
        # Show the education system name in Django Admin.
        return self.name
        


class Phase(models.Model):
    # Connect this phase to the education system that defines it.
    education_system = models.ForeignKey(
        EducationSystem,
        on_delete=models.PROTECT
    )

    # Store the official name of the phase.
    # Example: Foundation Phase, Primary, Secondary.
    name = models.CharField(
        max_length=100
    )

    # Store a short code for the phase.
    # Example: FOUNDATION, PRIMARY, SECONDARY.
    code = models.CharField(
        max_length=30
    )

    # Store the order in which phases should be displayed.
    # Example: 1 = Foundation, 2 = Intermediate, 3 = Senior.
    order = models.PositiveIntegerField()

    # Store optional information about the phase.
    description = models.TextField(
        blank=True,
        null=True
    )

    # Control whether this phase is currently available.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    # Store the current status of the phase.
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    def __str__(self):
        # Display the phase name in Django Admin.
        return self.name
        


class AcademicLevel(models.Model):
    # Connect this academic level to the phase it belongs to.
    # Example: Grade 1 belongs to the Foundation Phase.
    phase = models.ForeignKey(
        Phase,
        on_delete=models.PROTECT
    )

    # Store the official name of the academic level.
    # Example: Grade 1, Grade 2, Primary One, Senior 1.
    name = models.CharField(
        max_length=100
    )

    # Store a short code for the academic level.
    # Example: G1, G2, P1, S1.
    code = models.CharField(
        max_length=30
    )

    # Store the order in which academic levels should appear
    # within their phase.
    # Example: Grade 1 = 1, Grade 2 = 2, Grade 3 = 3.
    order = models.PositiveIntegerField()

    # Store optional information about this academic level.
    description = models.TextField(
        blank=True,
        null=True
    )

    # Control whether this academic level is currently available.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    # Store the current status of the academic level.
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    def __str__(self):
        # Display the academic level name in Django Admin.
        return self.name
                


class SchoolType(models.Model):
    # The name of the type of institution.
    name = models.CharField(max_length=100)

    def __str__(self):
        # Show the school type name in Django Admin.
        return self.name


class School(models.Model):
    # The official name of the school.
    name = models.CharField(max_length=200)
    
    # Store the school's unique short code.
    # Example: ARWA, SUM, KIS.
    # This code will later be used when generating student numbers.
    school_code = models.CharField(
        max_length=20,
        unique=True
    )
    
    # Store the school's official registration number.
    registration_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # Connect the school to the country where it is located.
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT
    )

    # Connect the school to its education system or curriculum.
    education_system = models.ForeignKey(
        EducationSystem,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    
    # Connect the school to its type of institution.
    school_type = models.ForeignKey(
        SchoolType,
        on_delete=models.PROTECT
    )

    # Store the school's physical street or postal address.
    address = models.TextField()
    
    
    # Store the city or town where the school is located.
    city = models.CharField(
        max_length=100
    )
    
    # Store the province, state, or region where the school is located.
    state_province = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    
    # Store the school's postal or ZIP code.
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    # Store the school's official email address.
    email = models.EmailField() 
    
    # Store the school's website address.
    website = models.URLField(
        blank=True,
        null=True
    )
    
    # Store the school's main hotline number.
    hotline = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )
    
    # Store the school's main mobile phone number.
    mobile = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )
    
    # Available statuses for a registered school.
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ACTIVE", "Active"),
        ("SUSPENDED", "Suspended"),
    ]
    
    # Store the current status of the school.
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )
    
    # Automatically store when the school was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    # Automatically update whenever the school is changed.
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    
    def __str__(self):
        # This controls how a School appears when Django displays it.
        return self.name
        
        
        
        
        
class StaffProfile(models.Model):
    # Connect this staff member to their Django login account.
    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE
    )

    # Connect the staff member to the school where they work.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE
    )

    # Store the staff member's identification number.
    id_or_passport = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    # Connect the staff member to their official staff role.
    role = models.ForeignKey(
        "StaffRole",
        on_delete=models.PROTECT
    )

    # Store the staff member's work phone number.
    phone_number = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    def __str__(self):
        # Show the staff member's name from the Django User account.
        return f"{self.user.first_name} {self.user.last_name}"        
        


class StudentNumberSequence(models.Model):
    # Connect this sequence to the school that owns it.
    # Each school will have its own student-number counter.
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE
    )

    # Store the next numeric value that ARWA should issue.
    # Example: 100001.
    next_number = models.PositiveIntegerField(
        default=100001
    )

    # Automatically record when this sequence was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever the sequence changes.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        # Show the school and its next available number.
        return f"{self.school.name} - Next: {self.next_number}"        
        
        
        
class StaffRole(models.Model):
    # Store the name of the staff role.
    name = models.CharField(
        max_length=100,
        unique=True
    )

    # Store a short description explaining what this role is responsible for.
    description = models.TextField(
        blank=True,
        null=True
    )

    # Automatically store when this role was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever this role is changed.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        # Show the role name when Django displays this object.
        return self.name        
        
        

class SchoolAcademicLevel(models.Model):
    # Connect this record to the school offering the academic level.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE
    )

    # Connect this record to the official academic level.
    academic_level = models.ForeignKey(
        AcademicLevel,
        on_delete=models.PROTECT
    )

    # Allow the school to use its own display name if needed.
    # If blank, the official academic level name can be used.
    display_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # Control whether the school currently offers this level.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Automatically record when this connection is created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update when this connection is changed.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # Prevent a school from adding the same academic level twice.
        unique_together = ("school", "academic_level")

    def __str__(self):
        # Show the school's name and the chosen academic level.
        level_name = self.display_name or self.academic_level.name
        return f"{self.school.name} - {level_name}" 
        
        


class Classroom(models.Model):
    # Connect this classroom to the school that owns it.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE
    )

    # Connect this classroom to the academic level it belongs to.
    # Example: Grade 7.
    academic_level = models.ForeignKey(
        SchoolAcademicLevel,
        on_delete=models.PROTECT
    )

    # Store the classroom name.
    # Example: 7A, 7B, Grade 7 Blue, etc.
    name = models.CharField(
        max_length=100
    )

    # Store an optional classroom code.
    # Example: 7A or G7-A.
    code = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    # Control whether this classroom is currently being used.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Automatically record when the classroom was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever the classroom is changed.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        # Show the school and classroom name in Django Admin.
        return f"{self.school.name} - {self.name}"        
        
        

class Student(models.Model):
    
    
    # Connect this student to their Django login account.
    # Django will securely manage the student's password.
    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Connect the student to the school that owns their record.
    # This is essential for keeping different schools' data separated.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE
    )

    # Store the student's first name.
    first_name = models.CharField(
        max_length=100
    )

    # Store the student's surname/last name.
    last_name = models.CharField(
        max_length=100
    )

    # Store the student's identification document number.
    # This can be an ID number or passport number.
    id_or_passport = models.CharField(
        max_length=50
    ) 
    
    # Connect the student's nationality to our Country table.
    # The administrator will select a country instead of typing it.
    nationality = models.ForeignKey(
        Country,
        on_delete=models.PROTECT
    ) 
    
    # The available gender options for a student.
    GENDER_CHOICES = [
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("OTHER", "Other"),
        ("PREFER_NOT_TO_SAY", "Prefer not to say"),
    ]

    # Store the student's selected gender.
    # Django will display the choices as a dropdown in Admin.
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES
    )
    
    # Store the student's date of birth.
    # A DateField is used because we only need the date,
    # not the exact time the student was born.
    date_of_birth = models.DateField()
    
    # Connect the student to the academic level offered by their school.
    # Example: ARWA Demonstration School - Grade 7.
    academic_level = models.ForeignKey(
        SchoolAcademicLevel,
        on_delete=models.PROTECT
    )
    
    # Connect the student to the classroom where they are enrolled.
    # Example: 7A.
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.PROTECT
    )
    
    # The available statuses for a student.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
        ("GRADUATED", "Graduated"),
        ("TRANSFERRED", "Transferred"),
        ("EXPELLED", "Expelled"),
    ]

    # Store the student's current enrollment status.
    # Django will display these options as a dropdown.
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )
    
    class Meta:
        # Prevent the same identification/passport number
        # from being registered twice within one school.
        #
        # The same number can still exist in another school,
        # which is important for ARWA's multi-school architecture.
        constraints = [
            models.UniqueConstraint(
                fields=["school", "id_or_passport"],
                name="unique_student_id_per_school",
            )
        ]
    
    
    # Store the unique student number generated by ARWA.
    # Example: ARWA-100001
    # The school code identifies the school, while the number
    # comes from that school's StudentNumberSequence.
    student_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False
    )  
    
    
    def generate_student_number(self):
        # Make sure this student belongs to a school.
        if not self.school:
            raise ValueError(
                "A student must belong to a school."
            )

        # Use a database transaction so reading and updating
        # the sequence happens safely as one database operation.
        with transaction.atomic():

            # Lock this school's sequence while we generate
            # the next student number.
            sequence = StudentNumberSequence.objects.select_for_update().get(
                school=self.school
            )

            # Build the student number using the school's code
            # and the current sequence number.
            student_number = (
                f"{self.school.school_code}-{sequence.next_number}"
            )

            # Increase the sequence so the next student receives
            # a different number.
            sequence.next_number += 1
            sequence.save()

        # Put the generated number directly into this Student object.
        self.student_number = student_number

        # Return the generated number as well.
        return student_number
    
    
    def save(self, *args, **kwargs):
        # Make number generation and student saving
        # succeed or fail together.
        with transaction.atomic():

            # Generate a number only if this is a new
            # student without an assigned number.
            if not self.student_number:
                self.generate_student_number()

            # Save the student to the database.
            super().save(*args, **kwargs)
        
               
    
    def clean(self):
        # Import Django's validation error class.
        from django.core.exceptions import ValidationError

        # Run Django's normal model validation first.
        super().clean()

        # Make sure the academic level belongs to the same school
        # as the student.
        if (
            self.academic_level
            and self.school
            and self.academic_level.school_id != self.school_id
        ):
            raise ValidationError({
                "academic_level": (
                    "The selected academic level does not belong "
                    "to this school."
                )
            })

        # Make sure the classroom belongs to the same school
        # as the student.
        if (
            self.classroom
            and self.school
            and self.classroom.school_id != self.school_id
        ):
            raise ValidationError({
                "classroom": (
                    "The selected classroom does not belong "
                    "to this school."
                )
            })

        # Make sure the classroom belongs to the same academic level
        # selected for the student.
        if (
            self.classroom
            and self.academic_level
            and self.classroom.academic_level_id != self.academic_level_id
        ):
            raise ValidationError({
                "classroom": (
                    "The selected classroom does not belong "
                    "to the selected academic level."
                )
            })    
                   