from django.db import models

from django.contrib.auth.models import User

# Import transaction tools so student-number generation
# can be performed safely as one database operation.
from django.db import transaction

from django.utils import timezone

from django.core.exceptions import ValidationError


class Country(models.Model):
    # Store the country's official name.
    name = models.CharField(
        max_length=100
    )

    # Store the country's ISO-style two-letter country code.
    #
    # Examples:
    # ZA = South Africa
    # US = United States
    # GB = United Kingdom
    code = models.CharField(
        max_length=2,
        unique=True,
    )

    def save(self, *args, **kwargs):
        # Automatically convert the country code
        # to uppercase before saving.
        self.code = self.code.upper()

        # Save the country normally.
        super().save(*args, **kwargs)

    @property
    def flag(self):
        # Convert the two-letter country code into
        # its corresponding flag emoji.
        #
        # Example:
        # ZA → 🇿🇦
        # US → 🇺🇸
        # GB → 🇬🇧
        return "".join(
            chr(127397 + ord(letter))
            for letter in self.code
        )

    def __str__(self):
        # Show the country name when Django displays
        # this object.
        return self.name
        

class Language(models.Model):
    # Official ISO 639-3 language name.
    name = models.CharField(max_length=150, unique=True)

    # Official ISO 639-3 three-letter language code.
    # Example: eng, afr, ara, fra.
    code = models.CharField(max_length=3, unique=True)

    # Django translation/locale code.
    # Example: en, af, ar, fr.
    #
    # This is optional because not every language in the
    # global ISO catalogue will necessarily have an ARWA
    # interface translation available.
    django_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
    )

    # Allows ARWA to temporarily disable a language
    # without deleting it from the global catalogue.
    is_active = models.BooleanField(default=True)
    
    # Shows whether ARWA has translated this language
    # and made it available for users to select.
    #
    # A language can remain in the global catalogue
    # while still being unavailable for selection.
    is_available = models.BooleanField(default=False)
    
    @classmethod
    def available_languages(cls):
        """
        Return languages that ARWA currently makes available
        for users and schools to select.
    
        A language must:
        1. Be active in the global catalogue.
        2. Have its ARWA interface translation completed.
        """
        return cls.objects.filter(
            is_active=True,
            is_available=True,
        )
        
    def clean(self):
        """
        Validate language availability before saving.
    
        ARWA can only make a language available when
        Django has a locale code for that language.
        """
        from django.core.exceptions import ValidationError
    
        # An available language must have a Django locale code.
        if self.is_available and not self.django_code:
            raise ValidationError(
                "A language cannot be available without a Django locale code."
            )    

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name



# Its purpose is to create the connection between a specific 
# school and the languages that school uses.
class SchoolLanguage(models.Model):
    # The school that uses this language.
    school = models.ForeignKey(
        "School",
        on_delete=models.CASCADE,
        related_name="school_languages"
    )

    # The language comes from ARWA's global
    # language catalogue.
    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="school_languages"
    )

    # Allows a school to temporarily disable
    # a language without deleting its history.
    is_active = models.BooleanField(
        default=True
    )

    # Store when this language was added to the school.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Store when the relationship was last changed.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # A school cannot have the same language
        # assigned more than once.
        unique_together = (
            "school",
            "language",
        )

    def __str__(self):
        # Show the school and language clearly
        # in Django Admin.
        return (
            f"{self.school.name} - "
            f"{self.language.name}"
        )


class UserLanguagePreference(models.Model):
    # The Django user whose interface language
    # is being configured.
    #
    # This allows the same system to work for
    # students, guardians, teachers, administrators,
    # and other ARWA users.
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="language_preference"
    )

    # The language comes from ARWA's global
    # language catalogue.
    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="user_preferences"
    )

    # Store when the preference was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Store when the preference was last changed.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        # Clearly show the user and selected language
        # in Django Admin.
        return (
            f"{self.user.username} - "
            f"{self.language.name}"
        )
        

class Currency(models.Model):
    # The internationally recognised three-letter
    # ISO 4217 currency code.
    #
    # Examples:
    # ZAR = South African Rand
    # USD = United States Dollar
    # GBP = Pound Sterling
    code = models.CharField(
        max_length=3,
        unique=True,
    )

    # Full official name of the currency.
    #
    # The name does not need to be unique because
    # the ISO three-letter code is the unique identifier.
    name = models.CharField(
        max_length=100,
    )
    
    # Countries that use this currency.
    #
    # A currency can be used by multiple countries,
    # so this is a Many-to-Many relationship.
    #
    # Example:
    # One currency can be associated with several countries.
    countries = models.ManyToManyField(
        "Country",
        related_name="currencies",
        blank=True,
    )

    # Currency symbol used when displaying amounts.
    #
    # Examples:
    # R, $, £, €, ¥
    symbol = models.CharField(
        max_length=10,
    )

    # Number of decimal places normally used
    # by this currency.
    decimal_places = models.PositiveSmallIntegerField(
        default=2,
    )

    # Allows ARWA to disable a currency without
    # deleting historical financial records.
    is_active = models.BooleanField(
        default=True,
    )

    # When the currency was added.
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # When the currency was last changed.
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.code} - {self.name}"
        

# What does one exchange-rate record represent?
# One record should answer:
# “At this particular time, how many units of 
# the quote currency equal 1 unit of the base currency?”
# For example:
# Base currency: ZAR
# Quote currency: USD
# Rate: 0.054
# Effective time: 17 October 2026, 09:00
# That means:
# 1 ZAR = 0.054 USD
# This structure is important because ARWA can then use the 
# same global exchange-rate system for all schools, while 
# each school's fee structure simply chooses its primary and secondary currencies.

class ExchangeRate(models.Model):
    # The currency we are converting FROM.
    #
    # Example:
    # ZAR -> USD
    #
    # In this example, ZAR is the base currency.
    base_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name="base_exchange_rates",
    )

    # The currency we are converting TO.
    #
    # Example:
    # ZAR -> USD
    #
    # In this example, USD is the quote currency.
    quote_currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name="quote_exchange_rates",
    )

    # The exchange rate between the two currencies.
    #
    # Example:
    # 1 ZAR = 0.054 USD
    #
    # We use DecimalField instead of FloatField because
    # exchange rates are financial data and require
    # accurate decimal calculations.
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=12,
    )

    # The date and time when this exchange rate became
    # effective.
    #
    # This is important because exchange rates change
    # over time and ARWA must preserve historical rates.
    effective_at = models.DateTimeField()

    # The source from which ARWA obtained the exchange rate.
    #
    # Examples could include the name of an exchange-rate
    # provider or another trusted financial source.
    source = models.CharField(
        max_length=100,
    )

    # The date and time when ARWA retrieved and stored
    # this exchange-rate record.
    fetched_at = models.DateTimeField(
        auto_now_add=True,
    )

    # The date and time when this database record
    # was last modified.
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def clean(self):
        # Import Django's validation error class.
        from django.core.exceptions import ValidationError

        # A currency cannot be converted into itself.
        #
        # Example:
        # ZAR -> ZAR is not a valid exchange-rate pair.
        if self.base_currency_id == self.quote_currency_id:
            raise ValidationError(
                "Base currency and quote currency must be different."
            )

        # An exchange rate must always be greater than zero.
        if self.rate <= 0:
            raise ValidationError(
                "Exchange rate must be greater than zero."
            )

    def clean(self):
        # Import Django's validation error class.
        from django.core.exceptions import ValidationError

        # A currency cannot be converted into itself.
        #
        # Example:
        # ZAR -> ZAR is not a valid exchange-rate pair.
        if self.base_currency_id == self.quote_currency_id:
            raise ValidationError(
                "Base currency and quote currency must be different."
            )

        # An exchange rate must always be greater than zero.
        if self.rate <= 0:
            raise ValidationError(
                "Exchange rate must be greater than zero."
            )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "base_currency",
                    "quote_currency",
                    "effective_at",
                    "source",
                ],
                name="unique_exchange_rate_record",
            ),
        ]

    def __str__(self):
        # Display the exchange rate in a useful format
        # inside Django Admin and other parts of ARWA.
        return (
            f"{self.base_currency.code}/"
            f"{self.quote_currency.code} = "
            f"{self.rate}"
        )


class EducationSystem(models.Model):
    # The name of the education system or curriculum.
    name = models.CharField(max_length=200)

    # Connect this education system to the country where it is used.
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE
    )

    # Determines whether this education system
    # organizes academic levels using phases.
    #
    # Example:
    # South Africa - CAPS may use phases.
    #
    # Some other education systems may organize
    # levels directly as Year 1, Year 2, Senior 1, etc.
    uses_phases = models.BooleanField(
        default=False
    )

    def __str__(self):
        # Show the education system name in Django Admin.
        return self.name
        

class AcademicStructure(models.Model):
    # The academic structure determines how an institution
    # divides its academic year.
    #
    # Examples:
    # Term System
    # Semester System
    # Trimester System
    # Quarter System
    # Modular / Block System
    name = models.CharField(
        max_length=100,
        unique=True
    )

    # A short code that ARWA can use internally.
    #
    # Examples:
    # TERM
    # SEMESTER
    # TRIMESTER
    # QUARTER
    # MODULAR
    code = models.CharField(
        max_length=20,
        unique=True
    )

    # Only active academic structures should be
    # available when registering a school.
    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):
        # Show the academic structure name
        # in Django Admin.
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
        


"""
EducationSystemSchoolTypePhase is the rule/configuration table 
that tells ARWA which phases are allowed for which school types 
within each education system.
"""
class EducationSystemSchoolTypePhase(models.Model):
    # The education system that defines the phase.
    #
    # Example:
    # CAPS
    # NCDC
    education_system = models.ForeignKey(
        EducationSystem,
        on_delete=models.CASCADE,
        related_name="school_type_phases"
    )

    # The type of school that can use this phase.
    #
    # Example:
    # Primary School
    # Secondary/High School
    school_type = models.ForeignKey(
        "SchoolType",
        on_delete=models.CASCADE,
        related_name="education_system_phases"
    )

    # The phase that is valid for this
    # education system and school type.
    phase = models.ForeignKey(
        Phase,
        on_delete=models.PROTECT,
        related_name="education_system_school_type_phases"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        unique_together = (
            "education_system",
            "school_type",
            "phase",
        )

    def clean(self):
        from django.core.exceptions import ValidationError

        # The phase must belong to the selected
        # education system.
        if (
            self.phase
            and self.phase.education_system
            != self.education_system
        ):
            raise ValidationError({
                "phase": (
                    "This phase does not belong "
                    "to the selected education system."
                )
            })

    def __str__(self):
        return (
            f"{self.education_system.name} - "
            f"{self.school_type.name} - "
            f"{self.phase.name}"
        )
        
        

class AcademicLevel(models.Model):
    # Connect this academic level directly to the
    # education system that defines it.
    #
    # This is important because some education systems
    # do not use phases.
    education_system = models.ForeignKey(
        EducationSystem,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="academic_levels"
    )
    
    # A phase is optional because not every
    # education system organizes academic levels
    # into phases.
    #
    # For systems that use phases, this field
    # connects the academic level to its phase.
    #
    # For systems without phases, this can remain empty.
    phase = models.ForeignKey(
        Phase,
        on_delete=models.PROTECT,
        null=True,
        blank=True
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
    
    def clean(self):
        # If a phase is selected, make sure that phase
        # belongs to the same education system as this
        # academic level.
        if (
            self.phase
            and self.education_system
            and self.phase.education_system
            != self.education_system
        ):
            from django.core.exceptions import ValidationError

            raise ValidationError({
                "phase": (
                    "This phase does not belong to "
                    "the selected education system."
                )
            })

    def __str__(self):
        # Display the academic level name in Django Admin.
        return self.name


                
"""
    The purpose of this model is simple:
    It tells ARWA which academic levels belong to a particular School Type within a particular Education System.
    It does not change SchoolType, AcademicLevel, or Phase.
    For example:
    South African Education System
            │
            ├── Primary School
            │      ├── Grade 1
            │      ├── Grade 2
            │      └── Grade 3
            │
            └── Secondary School
                ├── Grade 7
                ├── Grade 8
                └── Grade 9
    Another education system can have completely different mappings.
"""
class EducationSystemSchoolTypeLevel(models.Model):
    # Connect this record to the education system.
    #
    # This is important because the same School Type
    # can contain different academic levels in different
    # countries or education systems.
    education_system = models.ForeignKey(
        EducationSystem,
        on_delete=models.CASCADE,
        related_name="school_type_levels"
    )

    # Identify the type of institution.
    #
    # Example:
    # Primary School
    # Secondary/High School
    # College
    # University
    school_type = models.ForeignKey(
        "SchoolType",
        on_delete=models.CASCADE,
        related_name="education_system_levels"
    )

    # Identify the academic level that belongs
    # to this school type within this education system.
    #
    # Example:
    # Grade 1
    # Grade 2
    # Year 1
    # Form 1
    academic_level = models.ForeignKey(
        AcademicLevel,
        on_delete=models.PROTECT,
        related_name="school_type_mappings"
    )

    # Automatically record when this mapping is created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever this mapping changes.
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    def clean(self):
        from django.core.exceptions import ValidationError
    
        # Make sure the selected academic level belongs
        # to the selected education system.
        if (
            self.academic_level
            and self.academic_level.education_system
            != self.education_system
        ):
            raise ValidationError({
                "academic_level": (
                    "This academic level does not belong "
                    "to the selected education system."
                )
            })
    
        # If this academic level belongs to a phase,
        # check whether that phase is configured for
        # the selected school type.
        #
        # This allows ARWA to use the phase configuration
        # as an additional source of truth.
        if (
            self.academic_level
            and self.academic_level.phase
            and self.education_system
            and self.school_type
        ):
            valid_phase_mapping = (
                EducationSystemSchoolTypePhase.objects
                .filter(
                    education_system=self.education_system,
                    school_type=self.school_type,
                    phase=self.academic_level.phase,
                )
                .exists()
            )
    
            if not valid_phase_mapping:
                raise ValidationError({
                    "academic_level": (
                        "This academic level is not configured "
                        "for the selected school type."
                    )
                })
        
                

    class Meta:
        # Prevent the same academic level from being
        # assigned to the same school type twice
        # within the same education system.
        unique_together = (
            "education_system",
            "school_type",
            "academic_level",
        )

    def __str__(self):
        # Clearly show the relationship in Django Admin.
        return (
            f"{self.education_system.name} - "
            f"{self.school_type.name} - "
            f"{self.academic_level.name}"
        )





class Subject(models.Model):
    # Store the official name of the subject.
    # Example: Mathematics, English, Natural Sciences.
    name = models.CharField(
        max_length=100
    )

    # Store a short code for the subject.
    # Example: MATH, ENG, NS.
    code = models.CharField(
        max_length=30,
        unique=True
    )

    # Store an optional description of the subject.
    description = models.TextField(
        blank=True,
        null=True
    )

    # Control whether this subject is currently available.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Automatically record when the subject was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever the subject is changed.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        # Show the subject name in Django Admin.
        return self.name


"""
    The purpose of this model is to represent a qualification/study path offered by a College or University.
    Examples:
    Bachelor of Computer Science
    Diploma in Information Technology
    Bachelor of Business Administration
    MBA
    A Programme is not a Course/Module. For example:
    Bachelor of Computer Science → Programme
    Programming 101 → Course/Module
"""
class Programme(models.Model):
    # Store the official name of the qualification or study programme.
    # Example: Bachelor of Computer Science.
    name = models.CharField(
        max_length=200
    )

    # Store a short unique code for the programme.
    # Example: BCS, DIT, MBA.
    code = models.CharField(
        max_length=50,
        unique=True
    )

    # Store an optional description of the programme.
    description = models.TextField(
        blank=True,
        null=True
    )

    # Control whether the programme is currently available.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Automatically record when the programme was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever the programme is changed.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        # Show the programme name in Django Admin.
        return self.name
        
        
        
class Course(models.Model):
    # Store the official name of the course or academic module.
    # Example: Programming 101, Database Systems.
    name = models.CharField(
        max_length=200
    )

    # Store a short unique code for the course.
    # Example: PROG101, DB101, MATH101.
    code = models.CharField(
        max_length=50,
        unique=True
    )

    # Store the number of academic credits assigned to the course.
    # Some courses may not use credits, so this can be empty.
    credits = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True
    )

    # Store an optional description of what the course covers.
    description = models.TextField(
        blank=True,
        null=True
    )

    # Control whether the course is currently available.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Automatically record when the course was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever the course is changed.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        # Show the course name in Django Admin.
        return self.name        


class SchoolType(models.Model):
    # The name of the type of institution.
    name = models.CharField(
        max_length=100,
        unique=True
    )

    def __str__(self):
        # Show the school type name in Django Admin.
        return self.name
        

class AcademicStructureSchoolType(models.Model):
    # Connect this compatibility record to an
    # academic structure.
    academic_structure = models.ForeignKey(
        AcademicStructure,
        on_delete=models.CASCADE,
        related_name="allowed_school_types"
    )

    # Connect this compatibility record to a
    # school type.
    school_type = models.ForeignKey(
        SchoolType,
        on_delete=models.CASCADE,
        related_name="academic_structures"
    )

    class Meta:
        # Prevent the same Academic Structure + School Type
        # combination from being entered more than once.
        unique_together = (
            "academic_structure",
            "school_type",
        )

        # Display records in a predictable order.
        ordering = (
            "academic_structure",
            "school_type",
        )

    def __str__(self):
        # Show the relationship clearly in Django Admin.
        return (
            f"{self.academic_structure.name} - "
            f"{self.school_type.name}"
        )        


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
    
    # Store the school's IANA timezone.
    # Example: Africa/Johannesburg
    # This allows ARWA to display dates and times
    # according to each school's local timezone.
    timezone = models.CharField(
        max_length=100,
        default="UTC"
    )

    # Every school must belong to an official education system.
    education_system = models.ForeignKey(
        EducationSystem,
        on_delete=models.PROTECT
    )
    
    # Connect the school to the academic structure
    # used to divide its academic year.
    #
    # Examples:
    # Term System
    # Semester System
    # Trimester System
    # Quarter System
    # Modular / Block System
    #
    # PROTECT prevents an academic structure from being
    # deleted while a school is still using it.
    academic_structure = models.ForeignKey(
        AcademicStructure,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    
    # Connect the school to one or more types of institution.
    # A school may operate multiple sections, such as
    # Primary School and Secondary School, under one institution.
    school_types = models.ManyToManyField(
        SchoolType,
        related_name="schools",
        blank=True
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
    
    logo = models.ImageField(
        upload_to="schools/logos/",
        blank=True,
        null=True,
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
    
    def change_primary_currency(self, new_currency):
        # Import Django's transaction system.
        #
        # This allows the currency switch to happen
        # as one safe database operation.
        from django.db import transaction

        # Import Django's validation error class.
        from django.core.exceptions import ValidationError

        # Make sure the new currency exists in ARWA's
        # global Currency catalogue.
        #
        # We use the currency object itself here rather
        # than accepting a random currency code.
        if not new_currency:
            raise ValidationError(
                "A primary currency is required."
            )

        with transaction.atomic():

            # Find the school's current primary currency.
            current_primary = (
                SchoolCurrency.objects
                .filter(
                    school=self,
                    role="PRIMARY",
                )
                .select_for_update()
                .first()
            )

            # Every school must have a primary currency.
            if current_primary is None:
                raise ValidationError(
                    "This school does not have a primary currency."
                )

            # If the Director selects the currency that is
            # already primary, there is nothing to change.
            if current_primary.currency_id == new_currency.id:
                return current_primary

            # Find the selected currency if it is already
            # registered for this school.
            selected_currency = (
                SchoolCurrency.objects
                .filter(
                    school=self,
                    currency=new_currency,
                )
                .select_for_update()
                .first()
            )

            # If the selected currency is already registered
            # as a secondary currency, we can promote that
            # existing record to primary.
            if selected_currency:

                # The old primary becomes secondary.
                current_primary.role = "SECONDARY"
                current_primary.save(
                    update_fields=[
                        "role",
                        "updated_at",
                    ]
                )

                # The selected secondary becomes primary.
                selected_currency.role = "PRIMARY"
                selected_currency.save(
                    update_fields=[
                        "role",
                        "updated_at",
                    ]
                )

                return selected_currency

            # If the selected currency has not yet been
            # registered for this school, create it as
            # the new primary currency.
            #
            # We first change the old primary to secondary.
            current_primary.role = "SECONDARY"
            current_primary.save(
                update_fields=[
                    "role",
                    "updated_at",
                ]
            )

            # Register the new primary currency.
            return SchoolCurrency.objects.create(
                school=self,
                currency=new_currency,
                role="PRIMARY",
            )
    
    
    def __str__(self):
        # This controls how a School appears when Django displays it.
        return self.name



class SchoolCurrency(models.Model):
    # The school that has approved this currency.
    #
    # This connects the currency configuration directly
    # to a specific school.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="currencies",
    )

    # The currency from ARWA's global Currency catalogue.
    #
    # Example:
    # ZAR - South African Rand
    # USD - United States Dollar
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name="schools",
    )

    # Defines how the school uses this currency.
    #
    # PRIMARY:
    # The school's official financial currency.
    #
    # SECONDARY:
    # An additional currency used to display
    # automatically calculated equivalents.
    ROLE_CHOICES = [
        ("PRIMARY", "Primary"),
        ("SECONDARY", "Secondary"),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
    )

    # Record when the school added this currency.
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # Record when this currency configuration
    # was last changed.
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    
    def clean(self):
        # Import Django's validation error class.
        from django.core.exceptions import ValidationError

        # Look for another currency configuration for
        # the same school using this same currency.
        #
        # We exclude the current record because Django
        # calls clean() when an existing record is edited.
        existing_currency = (
            SchoolCurrency.objects
            .filter(
                school=self.school,
                currency=self.currency,
            )
            .exclude(pk=self.pk)
            .first()
        )

        # If the same currency already exists for this school,
        # it cannot be registered again with another role.
        #
        # This is especially important when changing:
        #
        # ZAR → PRIMARY
        # USD → SECONDARY
        #
        # to:
        #
        # USD → PRIMARY
        #
        # because USD already exists for the school.
        if existing_currency:
            raise ValidationError(
                {
                    "currency": (
                        "This currency is already registered for "
                        "this school and cannot be assigned another role."
                    )
                }
            )

    class Meta:
        constraints = [
            # A school cannot register the same currency
            # more than once.
            #
            # Example:
            # School 1 + ZAR
            # School 1 + ZAR  ❌
            models.UniqueConstraint(
                fields=[
                    "school",
                    "currency",
                ],
                name="unique_school_currency",
            ),

            # A school can have only ONE primary currency.
            #
            # Example:
            # School 1 + ZAR + PRIMARY  ✅
            # School 1 + USD + PRIMARY  ❌
            models.UniqueConstraint(
                fields=[
                    "school",
                ],
                condition=models.Q(role="PRIMARY"),
                name="unique_primary_currency_per_school",
            ),
        ]

    def __str__(self):
        # Example:
        # ARWA Demonstration School - ZAR - Primary
        return (
            f"{self.school.name} - "
            f"{self.currency.code} - "
            f"{self.get_role_display()}"
        )

        

"""
The purpose of SchoolPhase is to connect a specific school to the phase structure that the school actually uses.
Think of it this way:
Global Phase
Phase answers:
What phases exist in this education system?
For example:
CAPS
 ├── Foundation Phase
 ├── Intermediate Phase
 ├── Senior Phase
 └── FET Phase
Those are global ARWA configuration records.
SchoolPhase
SchoolPhase answers:
Which phase does THIS particular school use?
For example:
ARWA School
    ↓
SchoolPhase
    ↓
Foundation Phase
Another school could have:
Another School
    ↓
SchoolPhase
    ↓
Middle Cycle  ← custom phase created by that school
The second school's Middle Cycle does not become a global ARWA phase.
"""

class SchoolPhase(models.Model):
    # The school that owns this phase configuration.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="school_phases"
    )

    # The type of school that uses this phase.
    #
    # For example:
    # Primary School
    # Secondary School
    school_type = models.ForeignKey(
        SchoolType,
        on_delete=models.PROTECT,
        related_name="school_phases"
    )

    # An existing phase from ARWA's global catalogue.
    #
    # This is optional because the school may create
    # its own custom phase instead.
    phase = models.ForeignKey(
        Phase,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="school_phases"
    )


    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def clean(self):
        from django.core.exceptions import ValidationError
    
        # Make sure the selected school type belongs
        # to the selected school.
        if (
            self.school_id
            and self.school_type_id
            and not self.school.school_types.filter(
                pk=self.school_type_id
            ).exists()
        ):
            raise ValidationError({
                "school_type": (
                    "This school type does not belong "
                    "to the selected school."
                )
            })
    
        # A phase is mandatory.
        #
        # Schools cannot create their own custom phase.
        # They must select a phase from the global catalogue.
        if not self.phase_id:
            raise ValidationError({
                "phase": (
                    "You must select a phase from the "
                    "available phase catalogue."
                )
            })
    
        # The school's education system determines
        # whether the school uses phases.
        if (
            self.school_id
            and self.school.education_system
            and not self.school.education_system.uses_phases
        ):
            raise ValidationError({
                "phase": (
                    "This education system does not "
                    "use phases."
                )
            })
    
        # The selected phase must belong to the same
        # education system as the school.
        if (
            self.phase_id
            and self.school_id
            and self.school.education_system
            and self.phase.education_system
            != self.school.education_system
        ):
            raise ValidationError({
                "phase": (
                    "This phase does not belong to "
                    "the school's education system."
                )
            })
    
        # The selected phase must be configured for
        # the selected school type.
        #
        # ARWA does not hard-code these relationships.
        # The database configuration is the authority.
        if (
            self.school_id
            and self.school_type_id
            and self.phase_id
            and self.school.education_system_id
        ):
            valid_mapping = (
                EducationSystemSchoolTypePhase.objects
                .filter(
                    education_system=self.school.education_system,
                    school_type=self.school_type,
                    phase=self.phase,
                )
                .exists()
            )
    
            if not valid_mapping:
                raise ValidationError({
                    "phase": (
                        "This phase is not configured "
                        "for the selected school type."
                    )
                })

    def __str__(self):
        return (
            f"{self.school.name} - "
            f"{self.school_type.name} - "
            f"{self.phase.name}"
        )



class AcademicYear(models.Model):
    # Connect this academic year to the school that owns it.
    # Each school manages its own academic years.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE
    )

    # Store the academic year.
    # Example: 2026, 2027, 2028.
    year = models.PositiveIntegerField()

    # Control whether this academic year is currently active.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Automatically record when the academic year was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever the academic year changes.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # Prevent the same school from having
        # the same academic year twice.
        unique_together = (
            "school",
            "year",
        )

        # Display the newest academic years first.
        ordering = ["-year"]
        
    def current_term(self):
        # Find the term that is currently running
        # within this academic year.
        for term in self.term_set.all():

            # Use the method we created inside Term
            # to check whether this is the current term.
            if term.is_current():
                return term

        # Return None if no term is currently running.
        return None    
        

    def __str__(self):
        # Display the school and academic year together.
        return f"{self.school.name} - {self.year}"



class Term(models.Model):

    # Connect this academic period to the academic year
    # that owns it.
    #
    # Example:
    # 2027 Academic Year
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
    )

    # Define what type of academic period this is.
    #
    # This allows ARWA to support different types
    # of educational institutions.
    #
    # Examples:
    # Term       -> schools
    # Semester   -> colleges/universities
    # Trimester  -> institutions using three periods
    # Quarter    -> institutions using four periods
    # Year       -> institutions using one annual period
    PERIOD_TYPE_CHOICES = [
        ("TERM", "Term"),
        ("SEMESTER", "Semester"),
        ("TRIMESTER", "Trimester"),
        ("QUARTER", "Quarter"),
        ("YEAR", "Year"),
    ]

    period_type = models.CharField(
        max_length=10,
        choices=PERIOD_TYPE_CHOICES,
    )

    # Store the number of the academic period.
    #
    # Examples:
    # Term 1       -> 1
    # Term 2       -> 2
    # Semester 1   -> 1
    # Semester 2   -> 2
    # Trimester 3  -> 3
    period_number = models.PositiveIntegerField()

    # Store the name displayed to users.
    #
    # ARWA will eventually generate this from
    # the period type and period number.
    #
    # Examples:
    # Term 1
    # Semester 1
    # Trimester 2
    name = models.CharField(
        max_length=50,
    )

    # Store when the academic period starts.
    start_date = models.DateField()

    # Store when the academic period ends.
    end_date = models.DateField()

    # Control whether this academic period is active.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE",
    )

    # Automatically record when the period was created.
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # Automatically update whenever the period changes.
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        # Prevent duplicate academic periods.
        #
        # Example:
        # 2027 + TERM + 1
        #
        # cannot exist twice.
        unique_together = (
            "academic_year",
            "period_type",
            "period_number",
        )

        # Display academic periods in their
        # natural numerical order.
        ordering = [
            "period_type",
            "period_number",
        ]

    def is_current(self):
        # Get today's date.
        today = timezone.localdate()

        # Check whether today falls between
        # the period's start and end dates.
        return (
            self.status == "ACTIVE"
            and self.start_date <= today <= self.end_date
        )

    def __str__(self):

        # Example:
        # 2027 - Term 1
        # 2027 - Semester 1
        return (
            f"{self.academic_year.year} - "
            f"{self.name}"
        )
        


class SchoolSubject(models.Model):
    # Connect this subject offering to the school that offers it.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE
    )

    # Connect this record to the global Subject definition.
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT
    )

    # Control whether the school currently offers this subject.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Automatically record when this subject was added to the school.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever this record changes.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # A school must not add the same subject twice.
        unique_together = ("school", "subject")

    def __str__(self):
        # Show the school and subject together in Django Admin.
        return f"{self.school.name} - {self.subject.name}"
        

class SchoolCourse(models.Model):
    # Identify the school that offers this course.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="school_courses"
    )

    # Identify the master course being offered.
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="school_offerings"
    )

    # Control whether this course is currently offered
    # by this particular school.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Automatically record when the school started
    # offering this course.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever this offering changes.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # A school should not have the exact same course
        # added more than once.
        unique_together = (
            "school",
            "course",
        )

    def __str__(self):
        # Show both the school and course in Django Admin.
        return f"{self.school.name} - {self.course.name}"
                
        

# It will represent a paper or component belonging to a school's subject offering.
# For example:
# School subject
# Mathematics
# Paper 1
# Code: MATH-P1
# Paper 2
# Code: MATH-P2
class SubjectComponent(models.Model):
    # Connect this paper or component to the subject
    # offered by a particular school.
    school_subject = models.ForeignKey(
        SchoolSubject,
        on_delete=models.PROTECT,
        related_name="components"
    )

    # Store the name of the paper or component.
    # Examples: Paper 1, Paper 2, Practical.
    name = models.CharField(
        max_length=100
    )

    # Store a short code identifying the component.
    # Examples: MATH-P1, MATH-P2.
    code = models.CharField(
        max_length=30
    )

    # Control whether this component is available
    # for new assignments.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Automatically record when the component is created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update when the component changes.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # Prevent duplicate component names and codes
        # within the same school's subject offering.
        constraints = [
            models.UniqueConstraint(
                fields=["school_subject", "name"],
                name="unique_subject_component_name"
            ),
            models.UniqueConstraint(
                fields=["school_subject", "code"],
                name="unique_subject_component_code"
            ),
        ]

        ordering = ["school_subject", "name"]

    def __str__(self):
        # Display the subject and its paper together.
        return (
            f"{self.school_subject.subject.name} - "
            f"{self.name}"
        )
        


class Department(models.Model):
    # Store the school this department belongs to.
    #
    # This keeps departments separated between schools.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="departments"
    )

    # Store the department or faculty name.
    #
    # Examples:
    # Finance
    # Mathematics
    # Science
    # Sports
    # Administration
    name = models.CharField(
        max_length=150
    )

    # Allow the school to temporarily disable
    # a department without deleting its historical records.
    status = models.CharField(
        max_length=20,
        choices=(
            ("ACTIVE", "Active"),
            ("INACTIVE", "Inactive"),
        ),
        default="ACTIVE"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        unique_together = ("school", "name")
        ordering = ("name",)

    def __str__(self):
        return f"{self.school.name} - {self.name}"
                
        
        
        
class StaffProfile(models.Model):
    # ============================================================
    # DJANGO ACCOUNT CONNECTION
    # ============================================================

    # Connect this staff member to their Django login account.
    #
    # The User model already stores:
    # - First name
    # - Surname
    # - Email
    # - Username
    # - Password
    # - Account active/inactive status
    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE
    )

    # Connect the staff member to the school where they work.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="staff_profiles"
    )


    # ============================================================
    # PERSONAL INFORMATION
    # ============================================================

    # Store the staff member's identification document number.
    #
    # Examples:
    # - National ID
    # - Passport number
    id_or_passport = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    # Store the staff member's date of birth.
    #
    # This is useful for HR records and age-related
    # employment requirements.
    date_of_birth = models.DateField(
        blank=True,
        null=True
    )

    # Store the staff member's gender.
    #
    # Kept optional because schools and countries may
    # have different HR requirements.
    GENDER_CHOICES = (
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("OTHER", "Other"),
        ("PREFER_NOT_TO_SAY", "Prefer not to say"),
    )

    gender = models.CharField(
        max_length=30,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )

    # Store the staff member's physical/home address.
    #
    # Optional because smaller schools may not require
    # the information during initial registration.
    physical_address = models.TextField(
        blank=True,
        null=True
    )

    # Store the staff member's work/contact phone number.
    phone_number = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    # Store the staff member's profile photograph.
    profile_picture = models.ImageField(
        upload_to="staff/profile_pictures/",
        blank=True,
        null=True,
    )


    # ============================================================
    # CORPORATE & INSTITUTIONAL IDENTITY
    # ============================================================

    # Store the staff member's ARWA staff number.
    #
    # This number is generated automatically by ARWA
    # and cannot be manually changed.
    #
    # Example:
    # SCHOOLCODE-S000001
    # SCHOOLCODE-S000002
    staff_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
    )

    # Store the staff member's professional job title
    # or designation.
    #
    # Examples:
    # Head of Mathematics
    # Grade 10 Coordinator
    # Senior Bursar
    # IT Support Lead
    # Teacher
    job_title = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    # Connect the staff member to their department.
    #
    # Examples:
    # Mathematics
    # Finance
    # Administration
    # Sports
    # Information Technology
    department = models.ForeignKey(
        "Department",
        on_delete=models.PROTECT,
        related_name="staff_members",
        blank=True,
        null=True
    )

    # Store the date the staff member officially
    # joined or was appointed by the school.
    appointment_date = models.DateField(
        blank=True,
        null=True
    )

    # Track the employment arrangement.
    CONTRACT_TYPE_CHOICES = (
        ("FULL_TIME", "Full-Time"),
        ("PART_TIME", "Part-Time"),
        ("CONTRACT", "Contract"),
        ("SUBSTITUTE", "Substitute"),
        ("VOLUNTEER", "Volunteer"),
        ("OTHER", "Other"),
    )

    contract_type = models.CharField(
        max_length=20,
        choices=CONTRACT_TYPE_CHOICES,
        blank=True,
        null=True
    )

    # Track the current employment status.
    #
    # This is different from User.is_active.
    #
    # User.is_active controls whether the person can
    # authenticate into Django.
    #
    # This field records their institutional employment status.
    WORK_STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("ON_LEAVE", "On Leave"),
        ("SUSPENDED", "Suspended"),
        ("TRANSFERRED", "Transferred"),
        ("RESIGNED", "Resigned"),
        ("TERMINATED", "Terminated"),
        ("RETIRED", "Retired"),
    )

    work_status = models.CharField(
        max_length=20,
        choices=WORK_STATUS_CHOICES,
        default="ACTIVE"
    )


    # ============================================================
    # ROLE & AUTHORISATION
    # ============================================================

    # Connect this staff member to their official ARWA role.
    #
    # Examples:
    # Director
    # Principal
    # Deputy Principal
    # Teacher
    # Accountant
    # etc.
    #
    # StaffRole contains the organisational authority.
    role = models.ForeignKey(
        "StaffRole",
        on_delete=models.PROTECT,
        related_name="staff_profiles"
    )


    # ============================================================
    # COMPLIANCE / LEGAL / VERIFICATION
    # ============================================================

    # Store whether a police/criminal-record verification
    # has been completed.
    #
    # Optional because not every school will require
    # the same level of compliance information.
    police_clearance_verified = models.BooleanField(
        default=False
    )

    # Optional document containing police clearance evidence.
    police_clearance_document = models.FileField(
        upload_to="staff/compliance/police_clearance/",
        blank=True,
        null=True
    )

    # Store a professional council registration number.
    #
    # Example:
    # SACE registration number.
    #
    # Optional because different countries and professions
    # use different regulatory bodies.
    professional_registration_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # Store the name of the professional council.
    #
    # Example:
    # South African Council for Educators
    #
    # This makes the field useful internationally rather
    # than hard-coding SACE into ARWA.
    professional_registration_body = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )


    # ============================================================
    # EMERGENCY CONTACT
    # ============================================================

    # Store the staff member's emergency contact name.
    emergency_contact_name = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    # Store the emergency contact's relationship.
    #
    # Examples:
    # Spouse
    # Parent
    # Brother
    # Sister
    # Guardian
    emergency_contact_relationship = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # Store the emergency contact's phone number.
    emergency_contact_phone = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )


    # ============================================================
    # SECURITY
    # ============================================================

    # Record whether the staff member has successfully
    # enrolled in two-factor authentication.
    #
    # This records the state.
    #
    # The actual enforcement of 2FA will be handled by
    # ARWA's authentication/security system later.
    two_factor_enrolled = models.BooleanField(
        default=False
    )


    # ============================================================
    # TIMESTAMPS
    # ============================================================

    # Automatically store when the staff profile was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever the staff profile changes.
    updated_at = models.DateTimeField(
        auto_now=True
    )


    # ============================================================
    # STAFF NUMBER GENERATION
    # ============================================================

    def save(self, *args, **kwargs):
        """
        Automatically generate a unique Staff Number
        when a new staff profile is created.
        """

        # Generate a Staff Number only when creating
        # a brand-new staff profile.
        if not self.pk:

            # Make sure the sequence operation and the
            # staff profile creation happen safely together.
            with transaction.atomic():

                # Get this school's Staff Number sequence.
                #
                # select_for_update() locks the sequence row
                # while we generate the number.
                #
                # This prevents two staff members from receiving
                # the same number at the same time.
                sequence = (
                    StaffNumberSequence.objects
                    .select_for_update()
                    .get(school=self.school)
                )

                # Build the Staff Number.
                #
                # Example:
                # ARWA-S000001
                # ARWA-S000002
                self.staff_number = (
                    f"{self.school.school_code}-S"
                    f"{sequence.next_number:06d}"
                )

                # Increase the sequence so the next staff member
                # receives the next available number.
                sequence.next_number += 1
                sequence.save()

                # Save the staff profile inside the same transaction.
                super().save(*args, **kwargs)

            # The transaction completed successfully.
            return

        # Existing staff profiles are saved normally.
        super().save(*args, **kwargs)


    def __str__(self):
        # Show the staff member's name from the Django User account.
        return f"{self.user.first_name} {self.user.last_name}"

class StaffSchoolTypeResponsibility(models.Model):

    # Staff member
    staff_profile = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name="school_type_responsibilities"
    )

    # School type they are responsible for
    school_type = models.ForeignKey(
        SchoolType,
        on_delete=models.PROTECT,
        related_name="staff_responsibilities"
    )

    # Automatically record when this responsibility
    # was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever this responsibility
    # is changed.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    # Control whether this responsibility is currently
    # active or no longer active.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )
    
    def clean(self):
        """
        Make sure the selected school type actually belongs
        to the staff member's school.
        """
    
        # Check whether the selected school type is one of
        # the school types registered for this staff member's school.
        if not self.staff_profile.school.school_types.filter(
            pk=self.school_type.pk
        ).exists():
    
            # Reject the assignment if the school type does
            # not belong to the staff member's school.
            from django.core.exceptions import ValidationError
    
            raise ValidationError({
                "school_type": (
                    "This school type does not belong to "
                    "the staff member's school."
                )
            })

    class Meta:
        # Prevent the same staff member from being assigned
        # the same school type more than once.
        unique_together = (
            "staff_profile",
            "school_type",
        )

    def __str__(self):
        # Clearly show the staff member and the
        # school type they are responsible for.
        return (
            f"{self.staff_profile} - "
            f"{self.school_type}"
        )
                


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
        

# ---------------------------------------------------------
# GUARDIAN NUMBER SEQUENCE
# ---------------------------------------------------------
#
# Keeps track of the next guardian number available
# for each school.
#
# Example:
# ARWA-G000001
# ARWA-G000002
# ARWA-G000003
#
class GuardianNumberSequence(models.Model):

    # Each school gets its own guardian number sequence.
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE
    )

    # Store the next guardian number available.
    next_number = models.PositiveIntegerField(
        default=1
    )

    # Record when this sequence was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Record when this sequence was last updated.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.school.name} "
            f"- Next Guardian Number: "
            f"{self.next_number}"
        )


# ---------------------------------------------------------
# STAFF NUMBER SEQUENCE
# ---------------------------------------------------------
#
# Keeps track of the next staff number available
# for each school.
#
# Example:
# ARWA-S000001
# ARWA-S000002
# ARWA-S000003
#
class StaffNumberSequence(models.Model):

    # Each school gets its own staff number sequence.
    school = models.OneToOneField(
        School,
        on_delete=models.CASCADE
    )

    # Store the next staff number available.
    next_number = models.PositiveIntegerField(
        default=1
    )

    # Record when this sequence was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Record when this sequence was last updated.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.school.name} "
            f"- Next Staff Number: "
            f"{self.next_number}"
        )
                
        
class StaffRole(models.Model):
    # Store the name of the staff role.
    #
    # Examples:
    # Director
    # Principal
    # Deputy Principal
    # Teacher
    # Accountant
    # etc.
    name = models.CharField(
        max_length=100,
        unique=True
    )

    # Store a short description explaining
    # what this role is responsible for.
    description = models.TextField(
        blank=True,
        null=True
    )

    # Define the organisational rank of the role.
    #
    # Rank 1 = Executive leadership
    # Rank 2 = Senior management
    # Rank 3 = Administrative / finance
    # Rank 4 = Academic faculty
    # Rank 5 = Support staff
    RANK_CHOICES = (
        (1, "Executive Board / Director"),
        (2, "Senior Management / Principal"),
        (3, "Administrative & Finance Staff"),
        (4, "Academic Faculty / Teacher"),
        (5, "Support & Maintenance Staff"),
    )

    rank_level = models.IntegerField(
        choices=RANK_CHOICES,
        default=4
    )

    # Define which educational tier this role
    # is intended to operate within.
    #
    # K12       = Primary / Secondary education
    # GLOBAL    = All institutional tiers
    TIER_SCOPE_CHOICES = (
        ("K12", "K-12 (Primary & High School)"),
        ("GLOBAL", "All Institutional Tiers"),
    )

    scope_tier = models.CharField(
        max_length=15,
        choices=TIER_SCOPE_CHOICES,
        default="GLOBAL"
    )

    # Indicates that this role requires two-factor
    # authentication before accessing ARWA.
    #
    # This field describes the security requirement.
    # The actual 2FA enforcement will be handled
    # by the authentication system later.
    requires_2fa = models.BooleanField(
        default=False
    )

    # Indicates that this role has financial
    # responsibilities.
    #
    # This is used as part of authorization logic
    # for financial areas of ARWA.
    is_financial_role = models.BooleanField(
        default=False
    )

    # Automatically store when this role was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever this role changes.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    def is_director(self):
        """
        Check whether this is the Director role.
        """

        return self.name.strip().lower() == "director"

    def is_executive_tier(self):
        """
        Check whether this role belongs to the
        executive or senior-management tiers.
        """

        return self.rank_level in [1, 2]

    def can_access_billing(self):
        """
        Determine whether this role can access
        sensitive billing and financial areas.

        Directors have access because they are
        Rank 1 executives.

        Other roles require the financial-role
        flag to be enabled.
        """

        return (
            self.is_financial_role
            or self.rank_level == 1
        )

    def __str__(self):
        # Show the role name in Django Admin
        # and other Django displays.
        return self.name  
        
        

class SchoolAcademicLevel(models.Model):
    # Connect this record to the school offering the academic level.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE
    )
    
    # The type of school that offers this academic level.
    # This is important because one school can contain
    # multiple school types.
    school_type = models.ForeignKey(
        SchoolType,
        on_delete=models.PROTECT
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
        # Prevent the same academic level from being added
        # twice for the same school type within a school.
        unique_together = (
            "school",
            "school_type",
            "academic_level",
        )
    
    
    def clean(self):
        from django.core.exceptions import ValidationError
    
        # Make sure the selected school type actually
        # belongs to this school.
        if (
            self.school_id
            and self.school_type_id
            and not self.school.school_types.filter(
                pk=self.school_type_id
            ).exists()
        ):
            raise ValidationError({
                "school_type": (
                    "This school type does not belong "
                    "to the selected school."
                )
            })
    
        # Make sure the academic level belongs to the
        # school's education system.
        if (
            self.academic_level_id
            and self.school_id
            and self.academic_level.education_system_id
            != self.school.education_system_id
        ):
            raise ValidationError({
                "academic_level": (
                    "This academic level does not belong "
                    "to the school's education system."
                )
            })
    
        # Make sure this academic level is configured
        # for the selected education system and school type.
        if (
            self.school_id
            and self.school_type_id
            and self.academic_level_id
        ):
            valid_mapping = (
                EducationSystemSchoolTypeLevel.objects
                .filter(
                    education_system=self.school.education_system,
                    school_type=self.school_type,
                    academic_level=self.academic_level,
                )
                .exists()
            )
    
            if not valid_mapping:
                raise ValidationError({
                    "academic_level": (
                        "This academic level is not configured "
                        "for the selected school type."
                    )
                })     
        
        
        # If this academic level belongs to a phase,
        # make sure that phase is configured for this
        # school and school type.
        if (
            self.school_id
            and self.school_type_id
            and self.academic_level_id
            and self.academic_level.phase_id
        ):
            valid_school_phase = (
                SchoolPhase.objects
                .filter(
                    school=self.school,
                    school_type=self.school_type,
                    phase=self.academic_level.phase,
                    status="ACTIVE",
                )
                .exists()
            )

            if not valid_school_phase:
                raise ValidationError({
                    "academic_level": (
                        "This academic level belongs to a phase "
                        "that is not configured for the selected "
                        "school and school type."
                    )
                })
    
    def __str__(self):
        # Show the school's name and the chosen academic level.
        level_name = self.display_name or self.academic_level.name
        return f"{self.school.name} - {level_name}" 
        
        

# Its purpose is to record which subjects a school makes available 
# at a particular grade. Later, the registration form can use these 
# records to show the correct subject choices.
# allows each school to configure its own subject offerings.
class SchoolAcademicLevelSubject(models.Model):
    # Identify the grade offered by a particular school.
    school_academic_level = models.ForeignKey(
        SchoolAcademicLevel,
        on_delete=models.CASCADE,
        related_name="available_subjects"
    )

    # Identify a subject offered by that school.
    school_subject = models.ForeignKey(
        SchoolSubject,
        on_delete=models.PROTECT,
        related_name="grade_offerings"
    )

    # Allow the school to activate or deactivate this offering.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Record when this grade-subject relationship is created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Record when this relationship is updated.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # Prevent the same subject from being assigned to the
        # same school's academic level more than once.
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "school_academic_level",
                    "school_subject"
                ],
                name="unique_school_grade_subject"
            )
        ]

        # Display offerings in a predictable order.
        ordering = [
            "school_academic_level",
            "school_subject__subject__name"
        ]

    def clean(self):
        # Run Django's standard validation first.
        super().clean()

        from django.core.exceptions import ValidationError

        errors = {}

        # Confirm that the grade and subject belong to the same school.
        if (
            self.school_academic_level_id
            and self.school_subject_id
            and self.school_academic_level.school_id
            != self.school_subject.school_id
        ):
            errors["school_subject"] = (
                "The subject must belong to the same school "
                "as the selected academic level."
            )

        # Prevent new active offerings from using an inactive grade.
        if (
            self.status == "ACTIVE"
            and self.school_academic_level_id
            and self.school_academic_level.status != "ACTIVE"
        ):
            errors["school_academic_level"] = (
                "An inactive academic level cannot have "
                "an active subject offering."
            )

        # Prevent new active offerings from using an inactive subject.
        if (
            self.status == "ACTIVE"
            and self.school_subject_id
            and self.school_subject.status != "ACTIVE"
        ):
            errors["school_subject"] = (
                "An inactive school subject cannot have "
                "an active grade offering."
            )

        # Return all validation errors together.
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        # Display the grade and subject clearly in Django Admin.
        return (
            f"{self.school_academic_level} - "
            f"{self.school_subject.subject.name}"
        )




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
        



# We want ARWA to assign teachers to a specific subject component, 
# classroom and academic year. That lets Teacher A teach Mathematics Paper 1 
# while Teacher B teaches Mathematics Paper 2, without allowing two teachers 
# to be assigned the same paper in the same class and year.
# We'll also preserve assignment history by using PROTECT instead of CASCADE for the teacher relationship.
class TeacherSubjectClass(models.Model):
    # Connect this assignment to the teacher's staff profile.
    # PROTECT helps preserve historical assignment records.
    teacher = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT,
        related_name="teaching_assignments"
    )

    # Connect this assignment to a subject offered by the school.
    school_subject = models.ForeignKey(
        SchoolSubject,
        on_delete=models.PROTECT,
        related_name="teaching_assignments"
    )

    # Optionally identify a paper or component.
    # Example: Mathematics Paper 1 or Mathematics Paper 2.
    # Leave blank when the teacher teaches the whole subject.
    subject_component = models.ForeignKey(
        SubjectComponent,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="teaching_assignments"
    )

    # Connect the assignment to the classroom being taught.
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.PROTECT,
        related_name="teaching_assignments"
    )

    # Record the academic year for this assignment.
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="teaching_assignments"
    )

    # Control whether this assignment is currently active.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Record when the assignment was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Update the timestamp whenever the assignment changes.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # Display assignments in a predictable order.
        ordering = [
            "academic_year__year",
            "classroom__name",
            "school_subject__subject__name",
        ]

        # Prevent duplicate assignments for a particular paper
        # in the same classroom and academic year.
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "classroom",
                    "academic_year",
                    "subject_component",
                ],
                condition=models.Q(
                    subject_component__isnull=False
                ),
                name="unique_component_class_year",
            ),

            # When no component is specified, only one whole-subject
            # assignment is allowed for that subject, classroom and year.
            models.UniqueConstraint(
                fields=[
                    "school_subject",
                    "classroom",
                    "academic_year",
                ],
                condition=models.Q(
                    subject_component__isnull=True
                ),
                name="unique_whole_subject_class_year",
            ),
        ]

    def clean(self):
        # Import Django's validation error class.
        from django.core.exceptions import ValidationError

        # Run Django's standard validation first.
        super().clean()

        errors = {}

        # Make sure the teacher and all school-owned records
        # belong to the same school.
        if self.teacher_id and self.school_subject_id:
            if self.teacher.school_id != self.school_subject.school_id:
                errors["school_subject"] = (
                    "The subject must belong to the teacher's school."
                )

        if self.teacher_id and self.classroom_id:
            if self.teacher.school_id != self.classroom.school_id:
                errors["classroom"] = (
                    "The classroom must belong to the teacher's school."
                )

        if self.teacher_id and self.academic_year_id:
            if self.teacher.school_id != self.academic_year.school_id:
                errors["academic_year"] = (
                    "The academic year must belong to the teacher's school."
                )

        if self.school_subject_id and self.classroom_id:
            if (
                self.school_subject.school_id
                != self.classroom.school_id
            ):
                errors["classroom"] = (
                    "The classroom and subject must belong to the same school."
                )

        if self.classroom_id and self.academic_year_id:
            if self.classroom.school_id != self.academic_year.school_id:
                errors["academic_year"] = (
                    "The academic year must belong to the classroom's school."
                )

        # Make sure the school's subject component belongs
        # to the selected school subject.
        if self.subject_component_id and self.school_subject_id:
            if (
                self.subject_component.school_subject_id
                != self.school_subject_id
            ):
                errors["subject_component"] = (
                    "This component must belong to the selected school subject."
                )

        # Make sure the classroom's academic level belongs
        # to the same school as the classroom.
        if self.classroom_id:
            if (
                self.classroom.academic_level.school_id
                != self.classroom.school_id
            ):
                errors["classroom"] = (
                    "The classroom's academic level must belong "
                    "to the same school."
                )

        # New assignments should use active records.
        if self.status == "ACTIVE":
            if self.teacher_id and self.teacher.status != "ACTIVE":
                errors["teacher"] = "The teacher must be active."

            if (
                self.school_subject_id
                and self.school_subject.status != "ACTIVE"
            ):
                errors["school_subject"] = (
                    "The school's subject offering must be active."
                )

            if (
                self.subject_component_id
                and self.subject_component.status != "ACTIVE"
            ):
                errors["subject_component"] = (
                    "The subject component must be active."
                )

            if self.classroom_id and self.classroom.status != "ACTIVE":
                errors["classroom"] = "The classroom must be active."

            if (
                self.classroom_id
                and self.classroom.academic_level.status != "ACTIVE"
            ):
                errors["classroom"] = (
                    "The classroom's academic level must be active."
                )

        # Return all validation problems together.
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        # Display the teacher, subject, classroom and year.
        component_name = (
            self.subject_component.name
            if self.subject_component_id
            else "Whole Subject"
        )

        return (
            f"{self.teacher} - "
            f"{self.school_subject.subject.name} - "
            f"{component_name} - "
            f"{self.classroom.name} - "
            f"{self.academic_year.year}"
        )
        



class Assessment(models.Model):

    # The school that owns this assessment.
    # This keeps assessments separated between schools.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE
    )

    # The academic year in which the assessment takes place.
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT
    )

    # The term in which the assessment takes place.
    term = models.ForeignKey(
        Term,
        on_delete=models.PROTECT
    )

    # The teacher who created the assessment.
    teacher = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT
    )

    # The subject offered by this particular school.
    school_subject = models.ForeignKey(
        SchoolSubject,
        on_delete=models.PROTECT
    )

    # The classroom receiving the assessment.
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.PROTECT
    )

    # The title of the assessment.
    # Example: History Test 1.
    title = models.CharField(
        max_length=200
    )

    # The type of assessment.
    # Teachers will select this from a dropdown.
    ASSESSMENT_TYPE_CHOICES = [
        ("TEST", "Test"),
        ("ASSIGNMENT", "Assignment"),
        ("PROJECT", "Project"),
        ("EXAMINATION", "Examination"),
        ("PRACTICAL", "Practical"),
        ("ORAL", "Oral"),
        ("QUIZ", "Quiz"),
        ("OTHER", "Other"),
    ]

    assessment_type = models.CharField(
        max_length=20,
        choices=ASSESSMENT_TYPE_CHOICES
    )

    # The date on which the assessment takes place.
    assessment_date = models.DateField()

    # The maximum number of marks available.
    # Example: 100 marks.
    total_possible = models.PositiveIntegerField()

    # Controls whether the assessment is active.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Automatically record when the assessment was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update when the assessment changes.
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    def clean(self):

        # Import ValidationError so Django can
        # show a clear validation message.
        from django.core.exceptions import ValidationError

        # Run Django's normal model validation first.
        super().clean()

        # Make sure the academic year belongs
        # to the same school as the assessment.
        if self.academic_year:
            if self.academic_year.school_id != self.school_id:
                raise ValidationError({
                    "academic_year": (
                        "The academic year must belong "
                        "to the same school."
                    )
                })

        # Make sure the term belongs to the
        # selected academic year.
        if self.term and self.academic_year:
            if self.term.academic_year_id != self.academic_year_id:
                raise ValidationError({
                    "term": (
                        "The term must belong to "
                        "the selected academic year."
                    )
                })
                
                # Make sure the term's academic year
        # belongs to the same school as the assessment.
        if self.term:
            if self.term.academic_year.school_id != self.school_id:
                raise ValidationError({
                    "term": (
                        "The term must belong "
                        "to the same school."
                    )
                })        

        # Make sure the teacher belongs
        # to the same school.
        if self.teacher:
            if self.teacher.school_id != self.school_id:
                raise ValidationError({
                    "teacher": (
                        "The teacher must belong "
                        "to the same school."
                    )
                })

        # Make sure the subject belongs
        # to the same school.
        if self.school_subject:
            if self.school_subject.school_id != self.school_id:
                raise ValidationError({
                    "school_subject": (
                        "The subject must belong "
                        "to the same school."
                    )
                })

        # Make sure the classroom belongs
        # to the same school.
        if self.classroom:
            if self.classroom.school_id != self.school_id:
                raise ValidationError({
                    "classroom": (
                        "The classroom must belong "
                        "to the same school."
                    )
                })
                
                # Make sure the teacher is actually assigned
        # to this subject and classroom.
        if (
            self.teacher
            and self.school_subject
            and self.classroom
        ):

            assigned = TeacherSubjectClass.objects.filter(
                teacher=self.teacher,
                school_subject=self.school_subject,
                classroom=self.classroom,
                status="ACTIVE",
            ).exists()

            # Reject the assessment if the teacher
            # does not have an active teaching assignment
            # for this subject and classroom.
            if not assigned:
                raise ValidationError({
                    "teacher": (
                        "The teacher is not assigned "
                        "to this subject and classroom."
                    )
                })              

    def __str__(self):
        return (
            f"{self.title} - "
            f"{self.classroom.name} - "
            f"{self.school_subject.subject.name}"
        )


class StudentAssessmentResult(models.Model):

    # The assessment for which this result belongs.
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE
    )

    # The student who received this mark.
    student = models.ForeignKey(
    
    #This relationship points to the model named Student. Resolve it when Django loads all the models.
    # so that we don't get an error for NameError: name 'Student' is not defined since we puted this model 
    # b4 student model 
        "Student",
        on_delete=models.PROTECT
    )
    
    # The staff member who entered this student's mark.
    # This gives ARWA an audit trail showing who
    # entered the result.
    entered_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT
    )

    # The mark achieved by the student.
    # Example: 42 out of 50.
    mark = models.PositiveIntegerField()

    # Automatically record when the result was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update when the result changes.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        # A student can only have one result
        # for a particular assessment.
        unique_together = (
            "assessment",
            "student",
        )

    def clean(self):

        # Import ValidationError so Django can
        # display a clear validation message.
        from django.core.exceptions import ValidationError

        # Run Django's normal validation first.
        super().clean()

        # Make sure the student belongs
        # to the same school as the assessment.
        if self.assessment and self.student:

            if self.assessment.school_id != self.student.school_id:
                raise ValidationError({
                    "student": (
                        "The student must belong "
                        "to the same school as "
                        "the assessment."
                    )
                })

        # Make sure the student belongs
        # to the classroom receiving the assessment.
        if self.assessment and self.student:

            if self.assessment.classroom_id != self.student.classroom_id:
                raise ValidationError({
                    "student": (
                        "The student must belong "
                        "to the assessment's classroom."
                    )
                })

        # Make sure the mark does not exceed
        # the maximum marks for the assessment.
        if self.assessment and self.mark is not None:

            if self.mark > self.assessment.total_possible:
                raise ValidationError({
                    "mark": (
                        "The mark cannot be greater "
                        "than the assessment's "
                        "total possible marks."
                    )
                })

    def __str__(self):

        return (
            f"{self.student} - "
            f"{self.assessment.title} - "
            f"{self.mark}/"
            f"{self.assessment.total_possible}"
        )
        

class ExaminationResult(models.Model):

    # The examination assessment this result belongs to.
    # This connects the result to the subject, class,
    # teacher, academic year and term.
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.PROTECT
    )

    # The student who received this examination mark.
    student = models.ForeignKey(
        "Student",
        on_delete=models.PROTECT
    )

    # The mark entered by the HOD.
    mark = models.PositiveIntegerField()
    
    # Store the original examination mark before
    # any correction is made.
    original_mark = models.PositiveIntegerField()
        
    # The HOD who entered this examination mark.
    # This creates an audit trail showing who
    # was responsible for entering the mark.
    entered_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT
    )
    
    # The teacher who verified the examination mark.
    # This is filled only after the teacher confirms
    # that the mark is correct.
    verified_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="verified_examination_results"
    )
    
    # The exact date and time when the teacher
    # verified the examination mark.
    # This remains empty until verification happens.
    verified_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # The staff member who reported a problem
    # with this examination mark.
    # This can be the teacher or the HOD.
    reported_problem_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reported_examination_problems"
    )
    
    # Explain what is wrong with the examination mark.
    # This gives the teacher or HOD a clear audit trail
    # of why the result was sent back for correction.
    problem_reason = models.TextField(
        null=True,
        blank=True
    )
    
    # The staff member who corrected the examination mark
    # after a problem was reported.
    # This can be used to track who made the correction.
    corrected_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="corrected_examination_results"
    )
    
    # The exact date and time when the examination mark
    # was corrected.
    # This remains empty when no correction has happened.
    corrected_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # The HOD who finalized the examination mark.
    # Once finalized, the examination result becomes
    # the official result for the student.
    finalized_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="finalized_examination_results"
    )
    
    # The exact date and time when the HOD
    # finalized the examination result.
    # This remains empty until finalization happens.
    finalized_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # The current stage of the examination result.
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("AWAITING_VERIFICATION", "Awaiting Teacher Verification"),
        ("CORRECTION_REQUESTED", "Correction Requested"),
        ("VERIFIED", "Verified by Teacher"),
        ("FINALIZED", "Finalized"),
    ]

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="DRAFT"
    )

    # Automatically record when the examination result
    # is first created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever the result changes.
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:

        # Prevent the same student from receiving
        # more than one result for the same examination.
        unique_together = ("assessment", "student")
        
    def save(self, *args, **kwargs):
        # If this is a new examination result,
        # store the first mark as the original mark.
        if self.pk is None:
            self.original_mark = self.mark
    
        # Save the examination result normally.
        super().save(*args, **kwargs)  
        
          
    def correct_mark(self, new_mark, corrected_by):
        """
        Correct an examination mark through the official
        ARWA correction process.
        """
    
        from django.core.exceptions import ValidationError
        from django.utils import timezone
    
        # A correction is only allowed when a teacher
        # has reported a problem with the examination result.
        if self.status != "CORRECTION_REQUESTED":
            raise ValidationError(
                "This examination result is not awaiting correction."
            )
    
        # Only a Head of Department can correct
        # an examination mark.
        if corrected_by.role.name != "Head of Department":
            raise ValidationError(
                "Only a Head of Department can correct examination marks."
            )
    
        # The correcting HOD must belong to the
        # same school as the examination result.
        if corrected_by.school_id != self.assessment.school_id:
            raise ValidationError(
                "The correcting HOD must belong to the same school "
                "as the examination."
            )
    
        # The new mark cannot be greater than the
        # examination's total possible marks.
        if new_mark > self.assessment.total_possible:
            raise ValidationError(
                "The corrected mark cannot be greater than "
                "the examination's total possible marks."
            )
    
        # Never change original_mark.
        # It represents the first mark entered.
        self.mark = new_mark
    
        # Record who made the correction.
        self.corrected_by = corrected_by
    
        # Record exactly when the correction was made.
        self.corrected_at = timezone.now()
    
        # The corrected result must go back to the teacher
        # for verification.
        self.status = "AWAITING_VERIFICATION"
    
        # Save the corrected examination result.
        self.save()
        
    def verify_marks(self, verified_by):
        """
        Verify an examination result through the
        official ARWA teacher verification process.
        """
    
        from django.core.exceptions import ValidationError
        from django.utils import timezone
    
        # The teacher can only verify a result that
        # is waiting for teacher verification.
        if self.status != "AWAITING_VERIFICATION":
            raise ValidationError(
                "This examination result is not awaiting verification."
            )
    
        # Only a Teacher can verify examination marks.
        if verified_by.role.name != "Teacher":
            raise ValidationError(
                "Only a Teacher can verify examination marks."
            )
    
        # The verifying teacher must belong to the
        # same school as the examination.
        if verified_by.school_id != self.assessment.school_id:
            raise ValidationError(
                "The verifying teacher must belong to the same school "
                "as the examination."
            )
    
        # Record which teacher verified the marks.
        self.verified_by = verified_by
    
        # Record exactly when the teacher verified them.
        self.verified_at = timezone.now()
    
        # The examination result is now verified.
        self.status = "VERIFIED"
    
        # Save the verified result.
        self.save()    
    
    
    def finalize_result(self, finalized_by):
        """
        Finalize an examination result through the
        official ARWA finalization process.
        """
    
        from django.core.exceptions import ValidationError
        from django.utils import timezone
    
        # Only a verified examination result can be finalized.
        if self.status != "VERIFIED":
            raise ValidationError(
                "Only a verified examination result can be finalized."
            )
    
        # A teacher must have verified the marks first.
        if not self.verified_by:
            raise ValidationError(
                "The examination result cannot be finalized "
                "until a teacher has verified the marks."
            )
    
        # Only a Head of Department can finalize
        # examination marks.
        if finalized_by.role.name != "Head of Department":
            raise ValidationError(
                "Only a Head of Department can finalize examination marks."
            )
    
        # The HOD finalizing the result must belong to
        # the same school as the examination.
        if finalized_by.school_id != self.assessment.school_id:
            raise ValidationError(
                "The finalizing HOD must belong to the same school "
                "as the examination."
            )
    
        # Record who finalized the examination result.
        self.finalized_by = finalized_by
    
        # Record exactly when it was finalized.
        self.finalized_at = timezone.now()
    
        # The examination result is now official.
        self.status = "FINALIZED"
    
        # Save the finalized examination result.
        self.save()
    
    def clean(self):

        # Import Django's validation error.
        from django.core.exceptions import ValidationError

        # Run Django's normal validation first.
        super().clean()

        # Make sure the selected assessment is actually
        # an examination.
        if self.assessment:
            if self.assessment.assessment_type != "EXAMINATION":
                raise ValidationError({
                    "assessment": (
                        "This result must belong "
                        "to an examination assessment."
                    )
                })

        # Make sure the student belongs to the
        # same school as the examination assessment.
        if self.assessment and self.student:
            if self.assessment.school_id != self.student.school_id:
                raise ValidationError({
                    "student": (
                        "The student must belong "
                        "to the same school as "
                        "the examination."
                    )
                })

        # Make sure the student belongs to the
        # classroom receiving this examination.
        if self.assessment and self.student:
            if self.assessment.classroom_id != self.student.classroom_id:
                raise ValidationError({
                    "student": (
                        "The student must belong "
                        "to the examination's classroom."
                    )
                })

        # Make sure the mark cannot be greater than
        # the examination's total possible marks.
        if self.assessment and self.mark is not None:
            if self.mark > self.assessment.total_possible:
                raise ValidationError({
                    "mark": (
                        "The mark cannot be greater "
                        "than the examination's "
                        "total possible marks."
                    )
                })

        # Make sure the staff member who entered the mark
        # belongs to the same school as the assessment.
        if self.assessment and self.entered_by:
            if self.assessment.school_id != self.entered_by.school_id:
                raise ValidationError({
                    "entered_by": (
                        "The staff member who entered "
                        "the mark must belong to the "
                        "same school as the examination."
                    )
                })
        
        # Make sure the staff member who entered
        # the examination mark is an HOD.
        if self.entered_by:
            if self.entered_by.role.name != "Head of Department":
                raise ValidationError({
                    "entered_by": (
                        "Only an HOD can enter "
                        "examination marks."
                    )
                }) 
        
        
        
        # If a teacher verified the result, make sure
        # that teacher belongs to the same school.
        if self.assessment and self.verified_by:
            if self.assessment.school_id != self.verified_by.school_id:
                raise ValidationError({
                    "verified_by": (
                        "The verifying staff member "
                        "must belong to the same school "
                        "as the examination."
                    )
                })
        
        # Make sure the staff member who verified
        # the examination result is a Teacher.
        if self.verified_by:
            if self.verified_by.role.name != "Teacher":
                raise ValidationError({
                    "verified_by": (
                        "Only a Teacher can verify "
                        "examination marks."
                    )
                })
        
        
        # If someone reported a problem, make sure
        # they belong to the same school.
        if self.assessment and self.reported_problem_by:
            if self.assessment.school_id != self.reported_problem_by.school_id:
                raise ValidationError({
                    "reported_problem_by": (
                        "The staff member reporting "
                        "the problem must belong to the "
                        "same school as the examination."
                    )
                })
                
        # Make sure the staff member who reported
        # the problem is a Teacher.
        if self.reported_problem_by:
            if self.reported_problem_by.role.name != "Teacher":
                raise ValidationError({
                    "reported_problem_by": (
                        "Only a Teacher can report "
                        "a problem with examination marks."
                    )
                })               

        # If someone corrected the result, make sure
        # they belong to the same school.
        if self.assessment and self.corrected_by:
            if self.assessment.school_id != self.corrected_by.school_id:
                raise ValidationError({
                    "corrected_by": (
                        "The staff member correcting "
                        "the result must belong to the "
                        "same school as the examination."
                    )
                })
                
        # Make sure the staff member who corrected
        # the examination result is an HOD.
        if self.corrected_by:
            if self.corrected_by.role.name != "Head of Department":
                raise ValidationError({
                    "corrected_by": (
                        "Only an HOD can correct "
                        "examination marks."
                    )
                })        

        # If someone finalized the result, make sure
        # they belong to the same school.
        if self.assessment and self.finalized_by:
            if self.assessment.school_id != self.finalized_by.school_id:
                raise ValidationError({
                    "finalized_by": (
                        "The staff member finalizing "
                        "the result must belong to the "
                        "same school as the examination."
                    )
                })
                
        # Make sure the staff member who finalized
        # the examination result is an HOD.
        if self.finalized_by:
            if self.finalized_by.role.name != "Head of Department":
                raise ValidationError({
                    "finalized_by": (
                        "Only an HOD can finalize "
                        "examination marks."
                    )
                }) 
                
        # Make sure an examination result cannot be
        # finalized before the teacher verifies it.
        if self.status == "FINALIZED":
        
            # A teacher must have verified the result
            # before the HOD can finalize it.
            if not self.verified_by:
                raise ValidationError({
                    "status": (
                        "The examination result cannot be "
                        "finalized until the teacher has "
                        "verified the marks."
                    )
                })  
        
        
        # Make sure a result cannot be marked as
        # verified without a teacher being recorded
        # as the person who verified the marks.
        if self.status == "VERIFIED":
        
            if not self.verified_by:
                raise ValidationError({
                    "status": (
                        "The examination result cannot be "
                        "marked as verified until a teacher "
                        "has been recorded as the verifier."
                    )
                })                      
        
        # Make sure a result cannot be marked as
        # verified without recording the verification time.
        if self.status == "VERIFIED":
        
            if not self.verified_at:
                raise ValidationError({
                    "status": (
                        "The examination result cannot be "
                        "marked as verified without a "
                        "verification date and time."
                    )
                })
        
        # Make sure a correction request always
        # records the staff member who reported
        # the examination problem.
        if self.status == "CORRECTION_REQUESTED":
        
            if not self.reported_problem_by:
                raise ValidationError({
                    "status": (
                        "A correction request must "
                        "record the teacher who reported "
                        "the problem."
                    )
                })
                
        # Make sure a correction request always
        # includes a reason explaining the problem.
        if self.status == "CORRECTION_REQUESTED":
        
            if not self.problem_reason:
                raise ValidationError({
                    "problem_reason": (
                        "A correction request must "
                        "include a reason explaining "
                        "the problem."
                    )
                })
        
        # Make sure a correction always records
        # when the correction was made.
        if self.corrected_by:
        
            if not self.corrected_at:
                raise ValidationError({
                    "corrected_at": (
                        "A corrected examination result "
                        "must include the date and time "
                        "when the correction was made."
                    )
                })
                
        # Make sure the staff member who corrected
        # the examination result is a Head of Department.
        if self.corrected_by:
            if self.corrected_by.role.name != "Head of Department":
                raise ValidationError({
                    "corrected_by": (
                        "Only a Head of Department can "
                        "correct examination marks."
                    )
                })        
        
        # Make sure a finalized examination result
        # always records the date and time when
        # it was finalized.
        if self.status == "FINALIZED":
        
            if not self.finalized_at:
                raise ValidationError({
                    "finalized_at": (
                        "A finalized examination result "
                        "must include the date and time "
                        "when it was finalized."
                    )
                })
        
        # Make sure a finalized examination result
        # always records the HOD who finalized it.
        if self.status == "FINALIZED":
        
            if not self.finalized_by:
                raise ValidationError({
                    "status": (
                        "The examination result cannot be "
                        "finalized without recording the "
                        "HOD who finalized the marks."
                    )
                })
                
        # Make sure a reported examination problem
        # puts the result into the correction workflow.
        if self.reported_problem_by or self.problem_reason:
        
            if self.status != "CORRECTION_REQUESTED":
                raise ValidationError({
                    "status": (
                        "An examination result with a "
                        "reported problem must have the "
                        "status CORRECTION_REQUESTED."
                    )
                })            
        
    def __str__(self):

        # Display the student, examination and mark
        # clearly in Django Admin.
        return (
            f"{self.student} - "
            f"{self.assessment.title} - "
            f"{self.mark}/"
            f"{self.assessment.total_possible}"
        )
        
        
class Guardian(models.Model):
    """
    Stores the official parent/guardian information
    for a student in ARWA.
    """
    
    # Connect this guardian to Django's secure login system.
    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="guardian_profile",
    )

    # The guardian belongs to a specific school.
    # This keeps different schools' guardian records separated.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE
    )
    
    # Unique login number generated automatically by ARWA.
    # Guardians will use this number as their login identifier.
    guardian_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False
    )
    
    
    # Guardian's first name.
    first_name = models.CharField(
        max_length=100
    )

    # Guardian's surname.
    last_name = models.CharField(
        max_length=100
    )

    # South African ID number or foreign passport number.
    id_or_passport = models.CharField(
        max_length=50
    )
    
    # The guardian's nationality.
    # This uses ARWA's shared Nationality table
    # so nationality information stays consistent.
    nationality = models.ForeignKey(
        Country,
        on_delete=models.PROTECT
    )

    # Guardian's main contact number.
    phone_number = models.CharField(
        max_length=30
    )

    # Email is optional because not every guardian
    # may have an email address.
    email = models.EmailField(
        blank=True
    )
    
    # Stores the Guardian's current profile picture.
    #
    # Django stores the file path in the database
    # while the actual image is stored in media storage.
    #
    # If the Guardian has no profile picture yet,
    # this field can remain empty.
    profile_picture = models.ImageField(
        upload_to="guardians/profile_pictures/",
        blank=True,
        null=True,
    )

    # Guardian's physical/residential address.
    address = models.TextField()
    
    def save(self, *args, **kwargs):
        """
        Automatically generate a unique Guardian Number
        when a new guardian is created.
        """
    
        # Generate a Guardian Number only when
        # creating a new Guardian.
        if not self.pk and not self.guardian_number:
    
            # Make sure the sequence operation is treated
            # as one safe database transaction.
            with transaction.atomic():
    
                # Get this school's Guardian Number sequence.
                #
                # select_for_update() locks the sequence row
                # while we are generating the number.
                #
                # This prevents two guardians from receiving
                # the same number at the same time.
                sequence = (
                    GuardianNumberSequence.objects
                    .select_for_update()
                    .get(school=self.school)
                )
    
                # Build the Guardian Number using:
                #
                # ARWA-G + six-digit sequence number
                #
                # Example:
                # ARWA-G000001
                self.guardian_number = (
                    f"{self.school.school_code}-G"
                    f"{sequence.next_number:06d}"
                )
    
                # Increase the sequence so the next Guardian
                # receives the next available number.
                sequence.next_number += 1
                sequence.save()
    
                # Save the Guardian inside the same transaction.
                super().save(*args, **kwargs)
    
            # The transaction has completed successfully.
            return
    
        # Existing Guardian records are saved normally.
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class StudentGuardian(models.Model):
    """
    Connects students with their parents or guardians.
    """

    # The student connected to the guardian.
    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE
    )

    # The parent/guardian connected to the student.
    guardian = models.ForeignKey(
        Guardian,
        on_delete=models.CASCADE
    )

    # Describes the relationship.
    # Examples: Mother, Father, Guardian, Grandparent.
    relationship = models.CharField(
        max_length=50
    )

    # Identifies the main guardian for school communication.
    is_primary = models.BooleanField(
        default=False
    )

    # Records when this relationship was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        # A guardian can only be linked to the same
        # student once.
        unique_together = (
            "student",
            "guardian",
        )

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.guardian} "
            f"({self.relationship})"
        )


        

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
    
    profile_picture = models.ImageField(
        upload_to="students/profile_pictures/",
        blank=True,
        null=True,
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
                   
    def __str__(self):

        # Display the student's name and student number
        # instead of Django's default "Student object (1)".
        return (
           f"{self.first_name} "
           f"{self.last_name} "
           f"({self.student_number})"
        )  
         


# =========================================================
# This model will record a student's academic placement for one school year. 
# For example, the same student can have a Grade 10 enrolment in 2026 
# and a Grade 11 enrolment in 2027, while retaining the same permanent 
# student number and identity.
# =========================================================  

# StudentEnrollment records the student's participation in a particular 
# academic year, including their grade and classroom for that year.       
        
class StudentEnrollment(models.Model):
    # Link this enrolment to the student's permanent identity.
    student = models.ForeignKey(
        "Student",
        on_delete=models.PROTECT,
        related_name="enrollments"
    )

    # Record which school owns this enrolment.
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name="student_enrollments"
    )

    # Record the academic year for this enrolment.
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="student_enrollments"
    )

    # Record the academic level for this particular year.
    academic_level = models.ForeignKey(
        SchoolAcademicLevel,
        on_delete=models.PROTECT,
        related_name="student_enrollments"
    )

    # Record the classroom assigned for this academic year.
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.PROTECT,
        related_name="student_enrollments"
    )

    # Track the status of this year's enrolment.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
        ("SUSPENDED", "Suspended"),
        ("TRANSFERRED", "Transferred"),
        ("WITHDRAWN", "Withdrawn"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Record when this enrolment was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Record when this enrolment was last updated.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # A student can have only one enrolment per academic year.
        constraints = [
            models.UniqueConstraint(
                fields=["student", "academic_year"],
                name="unique_student_enrollment_per_year"
            )
        ]

        # Display the newest academic years first.
        ordering = ["-academic_year__year", "student"]
    
    
    def clean(self):
        # Run Django's standard model validation first.
        super().clean()

        from django.core.exceptions import ValidationError

        errors = {}

        # Ensure the student belongs to this school.
        if (
            self.student_id
            and self.school_id
            and self.student.school_id != self.school_id
        ):
            errors["student"] = (
                "The student must belong to this school."
            )

        # Ensure the academic year belongs to this school.
        if (
            self.academic_year_id
            and self.school_id
            and self.academic_year.school_id != self.school_id
        ):
            errors["academic_year"] = (
                "The academic year must belong to this school."
            )

        # Ensure the academic level belongs to this school.
        if (
            self.academic_level_id
            and self.school_id
            and self.academic_level.school_id != self.school_id
        ):
            errors["academic_level"] = (
                "The academic level must belong to this school."
            )

        # Ensure the classroom belongs to this school.
        if (
            self.classroom_id
            and self.school_id
            and self.classroom.school_id != self.school_id
        ):
            errors["classroom"] = (
                "The classroom must belong to this school."
            )

        # Ensure the classroom uses the selected academic level.
        if (
            self.classroom_id
            and self.academic_level_id
            and self.classroom.academic_level_id != self.academic_level_id
        ):
            errors["classroom"] = (
                "The classroom must use the selected academic level."
            )

        # Return all detected relationship errors together.
        if errors:
            raise ValidationError(errors)
                

    def __str__(self):
        # Display the student, year and academic level.
        return (
            f"{self.student} - "
            f"{self.academic_year.year} - "
            f"{self.academic_level}"
        )
        


# =========================================================
# this model stores the subjects selected for each annual enrolment.
# For example, a student might have Mathematics and English in the 2026 enrolment. 
# If the administrator changes the student's subjects for 2027, the 2026 selection remains unchanged.
# =========================================================  

class StudentEnrollmentSubject(models.Model):
    # Connect this subject selection to one academic-year enrolment.
    enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.PROTECT,
        related_name="enrollment_subjects"
    )

    # Select a subject that this school offers.
    school_subject = models.ForeignKey(
        SchoolSubject,
        on_delete=models.PROTECT,
        related_name="student_enrollment_subjects"
    )

    # Record when this subject was added to the enrolment.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        # Prevent the same subject from being added twice
        # to the same student's annual enrolment.
        constraints = [
            models.UniqueConstraint(
                fields=["enrollment", "school_subject"],
                name="unique_subject_per_student_enrollment"
            )
        ]

        # Display subject selections in a consistent order.
        ordering = ["school_subject__subject__name"]

    def clean(self):
        # Import Django's validation error class.
        from django.core.exceptions import ValidationError

        # Run Django's standard validation first.
        super().clean()

        # Ensure the subject belongs to the enrolment's school.
        if self.enrollment_id and self.school_subject_id:
            if (
                self.enrollment.school_id
                != self.school_subject.school_id
            ):
                raise ValidationError({
                    "school_subject": (
                        "This subject belongs to a different school."
                    )
                })

    def __str__(self):
        # Display the student and selected subject.
        return (
            f"{self.enrollment.student} - "
            f"{self.school_subject.subject.name} - "
            f"{self.enrollment.academic_year.year}"
        )




class Timetable(models.Model):
    # Connect this timetable entry to the school.
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name="timetable_entries"
    )

    # Record the academic year for this timetable entry.
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="timetable_entries"
    )

    # Identify the classroom receiving the lesson.
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.PROTECT,
        related_name="timetable_entries"
    )

    # Identify the subject offered by the school.
    school_subject = models.ForeignKey(
        SchoolSubject,
        on_delete=models.PROTECT,
        related_name="timetable_entries"
    )
    
    
    # Identify the specific paper or component, if applicable.
    # For example, Mathematics Paper 1 or Mathematics Paper 2.
    # Leave this empty for subjects without separate components.
    subject_component = models.ForeignKey(
        SubjectComponent,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="timetable_entries"
    )
    

    # Identify the staff member teaching the lesson.
    teacher = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT,
        related_name="timetable_entries"
    )

    # Store the weekday on which the lesson takes place.
    DAY_CHOICES = [
        ("MONDAY", "Monday"),
        ("TUESDAY", "Tuesday"),
        ("WEDNESDAY", "Wednesday"),
        ("THURSDAY", "Thursday"),
        ("FRIDAY", "Friday"),
    ]

    day_of_week = models.CharField(
        max_length=10,
        choices=DAY_CHOICES
    )

    # Record when the lesson starts.
    start_time = models.TimeField()

    # Record when the lesson ends.
    end_time = models.TimeField()

    # Record when this timetable entry was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Record when this timetable entry was last updated.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # Display lessons in weekday and start-time order.
        ordering = ["day_of_week", "start_time", "classroom"]

        # Help the database find timetable entries efficiently.
        indexes = [
            models.Index(
                fields=[
                    "school",
                    "academic_year",
                    "day_of_week",
                    "start_time",
                ],
                name="timetable_schedule_idx"
            ),
            models.Index(
                fields=[
                    "teacher",
                    "academic_year",
                    "day_of_week",
                ],
                name="timetable_teacher_idx"
            ),
            models.Index(
                fields=[
                    "classroom",
                    "academic_year",
                    "day_of_week",
                ],
                name="timetable_class_idx"
            ),
        ]

    def clean(self):

        # Run Django's standard validation first.
        super().clean()

        errors = {}

        # Make sure the lesson has a valid time range.
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time <= self.start_time
        ):
            errors["end_time"] = (
                "The lesson end time must be later "
                "than its start time."
            )
            
        # This validation checks that relationship before the timetable entry is accepted.
        # For example:
        # Mathematics + Mathematics Paper 1: allowed.
        # Mathematics + Mathematics Paper 2: allowed.
        # Mathematics + English Paper 1: rejected.
        # Ensure the selected component belongs to this subject.
        if self.subject_component_id and self.school_subject_id:
            if (
                self.subject_component.school_subject_id
                != self.school_subject_id
            ):
                errors["subject_component"] = (
                    "The selected component must belong "
                    "to the selected school subject."
                )
                    

        # Check that the related records belong to the same school.
        if self.school_id:
            if (
                self.academic_year_id
                and self.academic_year.school_id != self.school_id
            ):
                errors["academic_year"] = (
                    "The academic year must belong to this school."
                )

            
            if self.classroom_id:
                # Ensure the classroom belongs to this school.
                if self.classroom.school_id != self.school_id:
                    errors["classroom"] = (
                        "The classroom must belong to this school."
                    )

                # Ensure the classroom's academic level is registered
                # under the same school as the classroom.
                elif (
                    self.classroom.academic_level.school_id
                    != self.classroom.school_id
                ):
                    errors["classroom"] = (
                        "The classroom's academic level "
                        "must belong to the same school."
                    )
                    

            if (
                self.school_subject_id
                and self.school_subject.school_id != self.school_id
            ):
                errors["school_subject"] = (
                    "The subject must belong to this school."
                )

            if (
                self.teacher_id
                and self.teacher.school_id != self.school_id
            ):
                errors["teacher"] = (
                    "The teacher must belong to this school."
                )

        
        # Check that the teacher has the correct active assignment.
        if (
            self.teacher_id
            and self.school_id
            and self.academic_year_id
            and self.school_subject_id
            and self.classroom_id
        ):
            # Import the model that stores teacher assignments.
            from .models import TeacherSubjectClass

            # Start with the exact teacher, subject, classroom and year.
            assignment_filter = {
                "teacher_id": self.teacher_id,
                "school_subject_id": self.school_subject_id,
                "classroom_id": self.classroom_id,
                "academic_year_id": self.academic_year_id,
                "status": "ACTIVE",
            }

            # Require the assignment's component to match the timetable.
            # None means a whole-subject assignment.
            if self.subject_component_id:
                assignment_filter["subject_component_id"] = (
                    self.subject_component_id
                )
            else:
                assignment_filter["subject_component__isnull"] = True

            # Confirm that a matching assignment exists.
            assigned = TeacherSubjectClass.objects.filter(
                **assignment_filter
            ).exists()

            # Reject lessons without a matching assignment.
            if not assigned:
                errors["teacher"] = (
                    "This teacher does not have an active assignment "
                    "for this subject, classroom, academic year "
                    "and subject component."
                )
                

        # Check for conflicts only when enough information exists.
        if (
            self.school_id
            and self.academic_year_id
            and self.day_of_week
            and self.start_time is not None
            and self.end_time is not None
            and self.end_time > self.start_time
        ):
            # Find lessons whose time ranges overlap.
            overlapping_lessons = Timetable.objects.filter(
                school_id=self.school_id,
                academic_year_id=self.academic_year_id,
                day_of_week=self.day_of_week,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            )

            # Exclude this entry when editing an existing lesson.
            if self.pk:
                overlapping_lessons = overlapping_lessons.exclude(
                    pk=self.pk
                )

            # Reject assigning the same teacher to overlapping lessons.
            if (
                self.teacher_id
                and overlapping_lessons.filter(
                    teacher_id=self.teacher_id
                ).exists()
            ):
                errors["teacher"] = (
                    "This teacher already has a lesson "
                    "scheduled during this time."
                )

            # Reject assigning the same classroom to overlapping lessons.
            if (
                self.classroom_id
                and overlapping_lessons.filter(
                    classroom_id=self.classroom_id
                ).exists()
            ):
                errors["classroom"] = (
                    "This classroom already has a lesson "
                    "scheduled during this time."
                )

        # Return all detected validation errors together.
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        # Display the day, time, classroom and subject.
        return (
            f"{self.get_day_of_week_display()} - "
            f"{self.start_time} - "
            f"{self.classroom.name} - "
            f"{self.school_subject.subject.name}"
        )



# LessonSession represents one scheduled lesson on a particular date.
# For example, a timetable entry might schedule Mathematics 
# from 08:00 to 09:00 every Monday. On 12 October 2026, 
# ARWA can create a specific Mathematics lesson session. 
# Attendance for that lesson will be recorded separately from other lessons on the same day.
class LessonSession(models.Model):
    """
    Represent one scheduled lesson on a specific date.
    Attendance will be recorded against this lesson.
    """

    # Identify the school that owns this lesson.
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name="lesson_sessions"
    )

    # Identify the timetable entry for this lesson.
    timetable = models.ForeignKey(
        Timetable,
        on_delete=models.PROTECT,
        related_name="lesson_sessions"
    )

    # Record the date on which the lesson takes place.
    date = models.DateField()

    # Record when this lesson session was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Record when this lesson session was last updated.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # Display the most recent lessons first.
        ordering = ["-date", "timetable__start_time"]

        # Prevent creating the same scheduled lesson twice
        # for the same date.
        constraints = [
            models.UniqueConstraint(
                fields=["timetable", "date"],
                name="unique_timetable_lesson_per_day"
            )
        ]

    def clean(self):
        # Run Django's standard validation first.
        super().clean()

        # Ensure the lesson belongs to the same school
        # as the timetable entry.
        if (
            self.school_id
            and self.timetable_id
            and self.timetable.school_id != self.school_id
        ):
            from django.core.exceptions import ValidationError

            raise ValidationError({
                "timetable": (
                    "The timetable entry must belong "
                    "to the selected school."
                )
            })

    def __str__(self):
        # Display the lesson date, subject and classroom.
        return (
            f"{self.date} - "
            f"{self.timetable.school_subject.subject.name} - "
            f"{self.timetable.classroom.name}"
        )


class Homework(models.Model):
    # Identify the school that owns this homework assignment.
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name="homework_assignments"
    )

    # Record the academic year for this assignment.
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="homework_assignments"
    )

    # Record the term in which the homework is assigned.
    term = models.ForeignKey(
        Term,
        on_delete=models.PROTECT,
        related_name="homework_assignments"
    )

    # Identify the classroom receiving the homework.
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.PROTECT,
        related_name="homework_assignments"
    )

    # Identify the subject for this assignment.
    school_subject = models.ForeignKey(
        SchoolSubject,
        on_delete=models.PROTECT,
        related_name="homework_assignments"
    )

    # Identify the teacher responsible for the homework.
    teacher = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT,
        related_name="created_homework"
    )

    # Give the homework assignment a clear title.
    title = models.CharField(max_length=200)

    # Store written instructions and textbook page references.
    # Example: Complete the exercises on pages 20–25.
    description = models.TextField(
        blank=True,
        help_text=(
            "Write instructions, textbook page numbers, "
            "or additional information for students."
        )
    )

    # Allow the teacher to upload a PDF or other permitted document.
    # The permitted file types and upload security will be configured later.
    attachment = models.FileField(
        upload_to="homework/attachments/",
        blank=True,
        null=True,
        help_text="Optional homework document uploaded by the teacher."
    )

    
    # Store the current submission deadline.
    due_date = models.DateField()

    # Preserve the deadline that students were originally given.
    # This field should be set when homework is first published.
    original_due_date = models.DateField(
        blank=True,
        null=True,
        editable=False
    )
    

    # Store the maximum mark available for this assignment.
    total_possible = models.PositiveIntegerField(default=100)

    # Control whether the assignment is a draft, published or closed.
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("PUBLISHED", "Published"),
        ("CLOSED", "Closed"),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="DRAFT"
    )

    # Record when the homework assignment was created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Update this timestamp whenever the assignment is changed.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Arrange homework by deadline, then by title.
        ordering = ["due_date", "title"]

        # Improve filtering by school, academic year and classroom.
        indexes = [
            models.Index(
                fields=[
                    "school",
                    "academic_year",
                    "classroom"
                ],
                name="homework_school_year_class_idx"
            ),
        ]

    def clean(self):
        # Validate that the homework belongs to consistent school records.
        from django.core.exceptions import ValidationError

        super().clean()
        errors = {}

        if self.school_id and self.academic_year_id:
            if self.academic_year.school_id != self.school_id:
                errors["academic_year"] = (
                    "The academic year must belong to this school."
                )

        if self.school_id and self.term_id:
            if self.term.academic_year.school_id != self.school_id:
                errors["term"] = (
                    "The term must belong to this school."
                )

            if (
                self.academic_year_id
                and self.term.academic_year_id != self.academic_year_id
            ):
                errors["term"] = (
                    "The term must belong to the selected academic year."
                )

        if self.school_id and self.classroom_id:
            if self.classroom.school_id != self.school_id:
                errors["classroom"] = (
                    "The classroom must belong to this school."
                )

        if self.school_id and self.school_subject_id:
            if self.school_subject.school_id != self.school_id:
                errors["school_subject"] = (
                    "The subject must belong to this school."
                )

        if self.school_id and self.teacher_id:
            if self.teacher.school_id != self.school_id:
                errors["teacher"] = (
                    "The teacher must belong to this school."
                )

        # A homework assignment must have a positive maximum mark.
        if self.total_possible is not None and self.total_possible <= 0:
            errors["total_possible"] = (
                "The maximum mark must be greater than zero."
            )

        # Require written instructions or an uploaded attachment.
        if not self.description.strip() and not self.attachment:
            errors["description"] = (
                "Provide written instructions, upload a file, or do both."
            )

        if errors:
            raise ValidationError(errors)

    # method that records the original deadline the first time 
    # a homework assignment is published. Later deadline changes 
    # must go through a controlled workflow that records who made the change and why.
    def publish(self):
        # Import the validation error class used by Django.
        from django.core.exceptions import ValidationError

        # Only draft homework can be published for the first time.
        if self.status != "DRAFT":
            raise ValidationError(
                "Only draft homework can be published."
            )

        # Check the assignment's required fields and school relationships.
        self.full_clean()

        # Preserve the first published deadline.
        if self.original_due_date is None:
            self.original_due_date = self.due_date

        # Change the assignment status to published.
        self.status = "PUBLISHED"

        # Save the publication details.
        self.save()

    def __str__(self):
        # Display a readable homework title in Django Admin.
        return f"{self.title} - {self.classroom.name}"
        



class HomeworkSubmission(models.Model):
    # Identify the homework assignment being submitted.
    homework = models.ForeignKey(
        Homework,
        on_delete=models.PROTECT,
        related_name="submissions"
    )

    # Link the submission to the student's enrolment for that academic year.
    # This preserves the correct classroom and year after promotion.
    enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.PROTECT,
        related_name="homework_submissions"
    )

    # Record how the student submitted the homework.
    SUBMISSION_METHOD_CHOICES = [
        ("ONLINE", "Online"),
        ("PHYSICAL", "Physical"),
    ]

    submission_method = models.CharField(
        max_length=10,
        choices=SUBMISSION_METHOD_CHOICES,
        blank=True
    )

    # Allow students to type their answers online.
    typed_answer = models.TextField(blank=True)

    # Allow students to upload their completed work.
    # File upload security and permitted file types will be configured later.
    attachment = models.FileField(
        upload_to="homework/submissions/",
        blank=True,
        null=True
    )


    # Keep track of whether the student has submitted the work.
    SUBMISSION_STATUS_CHOICES = [
        ("NOT_SUBMITTED", "Not Submitted"),
        ("SUBMITTED", "Submitted"),
        ("LATE", "Late"),
    ]

    submission_status = models.CharField(
        max_length=15,
        choices=SUBMISSION_STATUS_CHOICES,
        default="NOT_SUBMITTED"
    )

    # Track marking independently of the submission status.
    MARKING_STATUS_CHOICES = [
        ("NOT_MARKED", "Not Marked"),
        ("AWAITING_MARK", "Awaiting Mark"),
        ("MARKED", "Marked"),
    ]

    marking_status = models.CharField(
        max_length=15,
        choices=MARKING_STATUS_CHOICES,
        default="NOT_MARKED"
    )

    # Store the student's mark once the teacher has marked the work.
    mark = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    # Record the teacher's feedback on the submitted work.
    teacher_feedback = models.TextField(blank=True)

    # Identify the teacher who marked the submission.
    marked_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT,
        related_name="marked_homework_submissions",
        blank=True,
        null=True
    )
    
    # Record the date and time when the teacher marks the submission.
    marked_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    
    # Record the actual calendar date the work was handed in.
    # This is especially useful for physical homework.
    submission_date = models.DateField(
        blank=True,
        null=True,
        help_text="The actual date the student handed in the homework."
    )

    # Record the actual submission date and time when known.
    # For physical submissions, the exact time may not be known.
    submitted_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="The actual submission timestamp, when known."
    )
    
    
    # Preserve the deadline that applied when the work was submitted.
    # This helps ARWA calculate lateness correctly if the deadline changes.
    due_date_at_submission = models.DateField(
        blank=True,
        null=True,
        editable=False,
        help_text=(
            "The homework deadline in effect when the work was submitted."
        )
    )
    

    # Record when the submission was entered into ARWA.
    # This is separate from the actual hand-in date.
    recorded_at = models.DateTimeField(
        auto_now_add=True
    )

    # Record which staff member entered the submission details.
    recorded_by = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT,
        related_name="recorded_homework_submissions",
        blank=True,
        null=True
    )

    # Track when this submission record was created and updated.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Keep submissions grouped by homework and student.
        ordering = ["homework", "enrollment"]

        # A student can have only one submission record per assignment.
        constraints = [
            models.UniqueConstraint(
                fields=["homework", "enrollment"],
                name="unique_homework_submission_per_enrollment"
            ),
        ]

        # Help ARWA find submissions for a particular homework and status.
        indexes = [
            models.Index(
                fields=["homework", "submission_status"],
                name="hw_submission_status_idx"
            ),
            models.Index(
                fields=["enrollment", "marking_status"],
                name="hw_enrollment_mark_idx"
            ),
        ]
        
    
    def calculate_submission_status(self):
        # Import today's date from Python's date utilities.
        from datetime import date

        # Leave the status unchanged if the student has not submitted.
        if not self.submission_date:
            return "NOT_SUBMITTED"

        # Use the saved deadline when available.
        # Otherwise, use the homework's current deadline.
        deadline = (
            self.due_date_at_submission
            or self.homework.due_date
        )

        # A submission after the deadline is late.
        if self.submission_date > deadline:
            return "LATE"

        # A submission on or before the deadline is on time.
        return "SUBMITTED"
        
                 
    # We should not change submission_status to LATE just because 
    # the deadline has passed. The student hasn't submitted anything yet. 
    # Instead, ARWA will calculate a display status when the dashboard or 
    # homework list is opened.
    # For example, if homework was due yesterday and the student hasn't 
    # submitted it, ARWA should show Overdue — Not Submitted.
    @property
    def display_submission_status(self):
        # Import Django's timezone utilities.
        from django.utils import timezone

        # Keep the actual submission status unchanged if work was handed in.
        if self.submission_status == "LATE":
            return "Late — Submitted"

        if self.submission_status == "SUBMITTED":
            return "Submitted"

        # Use today's date according to Django's configured timezone.
        today = timezone.localdate()

        # Show overdue only when the deadline has passed and work is missing.
        if (
            self.homework.status == "PUBLISHED"
            and self.homework.due_date < today
            and self.submission_status == "NOT_SUBMITTED"
        ):
            return "Overdue — Not Submitted"

        # Otherwise, the student has not submitted yet.
        return "Not Submitted"
        
    
    # teacher needs to know two things separately:
    # Has the student submitted the homework?
    # Has the teacher marked it?
    # For example, homework can be late but 
    # still awaiting a mark. We should combine 
    # these statuses for display without changing 
    # the saved database values.    
    @property
    def display_homework_status(self):
        # Get the current submission display status.
        submission_status = self.display_submission_status

        # Show when submitted work is waiting for the teacher.
        if self.marking_status == "AWAITING_MARK":
            if submission_status == "Late — Submitted":
                return "Late — Submitted, Awaiting Mark"

            if submission_status == "Submitted":
                return "Submitted — Awaiting Mark"

        # Show when the teacher has finished marking.
        if self.marking_status == "MARKED":
            if submission_status == "Late — Submitted":
                return "Late — Marked"

            if submission_status == "Submitted":
                return "Submitted — Marked"

        # Preserve overdue and not-submitted displays.
        return submission_status
        
    
    def record_submission(self, actual_date, method, recorded_by=None):
        # Import Django's validation error class.
        from django.core.exceptions import ValidationError

        # Only published homework can receive submissions.
        if self.homework.status != "PUBLISHED":
            raise ValidationError(
                "Only published homework can be submitted."
            )

        # Prevent accidental overwriting of an existing submission.
        if self.submission_status in ("SUBMITTED", "LATE"):
            raise ValidationError(
                "This homework has already been submitted. "
                "Use the approved resubmission process if changes are needed."
            )

        # Require the actual date the work was handed in.
        if not actual_date:
            raise ValidationError(
                "The actual submission date is required."
            )
            
        
        # Import Django's timezone utilities.
        from django.utils import timezone

        # Reject a submission date that is in the future.
        if actual_date > timezone.localdate():
            raise ValidationError(
                "The submission date cannot be in the future."
            )
                 

        # Check that the submission method is supported.
        valid_methods = dict(self.SUBMISSION_METHOD_CHOICES)

        if method not in valid_methods:
            raise ValidationError(
                "Choose Online or Physical submission."
            )
            
            
            
        # If a student chooses online submission, ARWA should require 
        # either a typed answer or an uploaded file. Otherwise, a student 
        # could accidentally submit an empty assignment.
        # Online submissions must contain an answer or an attachment.
        if method == "ONLINE":
            if not self.typed_answer.strip() and not self.attachment:
                raise ValidationError(
                    "For online submission, type an answer "
                    "or attach the completed homework."
                )
                    

        # Record the actual hand-in date and method.
        self.submission_date = actual_date
        self.submission_method = method

        # Capture the deadline that applies to this submission.
        self.due_date_at_submission = self.homework.due_date

        # Record who entered the submission, when applicable.
        if recorded_by is not None:
            self.recorded_by = recorded_by

        # Calculate and store the submission status.
        self.submission_status = self.calculate_submission_status()

        # Make the work available for teacher marking.
        self.marking_status = "AWAITING_MARK"

        # Validate the record before saving it.
        self.full_clean()

        # Save the validated submission.
        self.save()
        

    def clean(self):
        # Validate that the submission belongs to the correct school,
        # academic year, classroom and student enrolment.
        from django.core.exceptions import ValidationError

        super().clean()
        errors = {}

        if self.homework_id and self.enrollment_id:
            homework = self.homework
            enrollment = self.enrollment

            # Prevent a student from submitting work to another school's assignment.
            if homework.school_id != enrollment.school_id:
                errors["enrollment"] = (
                    "The student enrolment and homework must belong "
                    "to the same school."
                )

            # The assignment must belong to the student's enrolment year.
            if homework.academic_year_id != enrollment.academic_year_id:
                errors["enrollment"] = (
                    "The student's enrolment must match the homework's "
                    "academic year."
                )

            # The assignment must be for the student's enrolled classroom.
            if homework.classroom_id != enrollment.classroom_id:
                errors["enrollment"] = (
                    "The homework must belong to the student's enrolled "
                    "classroom."
                )

        # A recorded mark must not exceed the maximum possible mark.
        if self.mark is not None and self.homework_id:
            if self.mark > self.homework.total_possible:
                errors["mark"] = (
                    "The mark cannot exceed the homework's maximum mark."
                )
        
        # Check that a submitted status agrees with the actual dates.
        if (
            self.submission_status in ("SUBMITTED", "LATE")
            and self.submission_date
            and self.homework_id
        ):
            # Use the saved deadline for this submission.
            deadline = (
                self.due_date_at_submission
                or self.homework.due_date
            )

            # Reject a status that conflicts with the submission date.
            expected_status = (
                "LATE"
                if self.submission_date > deadline
                else "SUBMITTED"
            )

            if self.submission_status != expected_status:
                errors["submission_status"] = (
                    "The submission status does not match "
                    "the actual submission date and deadline."
                )
        
        
        # A submission must have an actual submission date and method.
        if self.submission_status in ("SUBMITTED", "LATE"):
            if not self.submission_date:
                errors["submission_date"] = (
                    "Record the actual date the work was submitted."
                )

            if not self.submission_method:
                errors["submission_method"] = (
                    "Select whether the work was submitted online or physically."
                )
        
        
        # ARWA should record who marked the homework and when. It should also 
        # ensure that the staff member belongs to the same school as the assignment.
        # Ensure the staff member marking the work belongs to the same school.
        if self.marked_by_id and self.homework_id:
            if self.marked_by.school_id != self.homework.school_id:
                errors["marked_by"] = (
                    "The staff member marking this homework "
                    "must belong to the same school."
                )

        # Ensure the staff member recording the submission belongs to the same school.
        if self.recorded_by_id and self.homework_id:
            if self.recorded_by.school_id != self.homework.school_id:
                errors["recorded_by"] = (
                    "The staff member recording this submission "
                    "must belong to the same school."
                )
                
        
        # A mark cannot exist while the submission is marked as not marked.
        if (
            self.mark is not None
            and self.marking_status == "NOT_MARKED"
        ):
            errors["marking_status"] = (
                "A submission with a mark cannot have "
                "the marking status Not Marked."
            )
                    
        
        # A marked submission must have a mark and marking details.
        if self.marking_status == "MARKED":
            if self.mark is None:
                errors["mark"] = "Enter a mark for marked homework."

            if not self.marked_by_id:
                errors["marked_by"] = (
                    "Record the teacher who marked the homework."
                )

            if not self.marked_at:
                errors["marked_at"] = (
                    "Record when the homework was marked."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        # Display the assignment and student in Django Admin.
        return (
            f"{self.homework.title} - "
            f"{self.enrollment.student}"
        )
        

# =========================================================
# SCHOOL CALENDAR EVENTS
# =========================================================

class SchoolEvent(models.Model):
    # Available categories for school calendar events.
    EVENT_TYPE_CHOICES = [
        ("HOLIDAY", "School Holiday"),
        ("MEETING", "Parent Meeting"),
        ("FUNCTION", "School Function"),
        ("CLOSURE", "School Closure"),
        ("OTHER", "Other Event"),
    ]

    # Connect each event to the school that created it.
    # This supports ARWA's multi-school architecture.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="calendar_events",
    )

    # Store the event's title.
    title = models.CharField(max_length=200)

    # Store optional information about the event.
    description = models.TextField(blank=True)

    # Classify the event.
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        default="OTHER",
    )

    # Store the first day of the event.
    start_date = models.DateField()

    # Store the final day of the event.
    # For a one-day event, use the same date as start_date.
    end_date = models.DateField()

    # Allow an event to be hidden without deleting its record.
    is_active = models.BooleanField(default=True)

    # Record when the event was created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Record when the event was last updated.
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Import Django's validation error class.
        from django.core.exceptions import ValidationError

        # Run Django's standard model validation.
        super().clean()

        # An event must not end before it starts.
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError({
                    "end_date": (
                        "The end date cannot be before "
                        "the start date."
                    )
                })

    def __str__(self):
        # Display the school and event title in Django Admin.
        return f"{self.school.name} - {self.title}"


class Attendance(models.Model):
    """
    Store student attendance for ARWA.

    Each attendance record belongs to a school,
    identifies a student and classroom, and records
    which staff member took the attendance.
    """

    # The school that owns this attendance record.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )

    # The student whose attendance is being recorded.
    student = models.ForeignKey(
        "Student",
        on_delete=models.PROTECT,
        related_name="attendance_records"
    )
    
    # Attendance should use the annual enrolment so that historical 
    # records remain accurate when a student moves to another grade or classroom.
    
    # Identify the student's enrolment for this academic year.
    enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )
    
    # This is what will allow ARWA to record attendance separately for each lesson.
    
    # Identify the specific lesson for which attendance is recorded.
    lesson_session = models.ForeignKey(
        LessonSession,
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )
    
    

    # The classroom associated with this attendance record.
    classroom = models.ForeignKey(
        "Classroom",
        on_delete=models.PROTECT,
        related_name="attendance_records"
    )

    # The staff member who recorded the attendance.
    # This references the existing StaffProfile model.
    recorded_by = models.ForeignKey(
        "StaffProfile",
        on_delete=models.PROTECT,
        related_name="recorded_attendance"
    )

    # Store the date of attendance.
    # If no date is supplied, use today's local date.
    date = models.DateField(
        default=timezone.localdate
    )

    # Define the attendance statuses users can select.
    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("LATE", "Late"),
        ("EXCUSED", "Excused"),
    ]

    # Store the student's attendance status.
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )

    # Allow staff to provide an optional explanation.
    remarks = models.TextField(
        blank=True
    )

    # Automatically store when the record is created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update the timestamp when edited.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        
        # Prevent duplicate attendance for the same student
        # in the same lesson session.
        constraints = [
            models.UniqueConstraint(
                fields=["enrollment", "lesson_session"],
                name="unique_enrollment_lesson_attendance",
            ),
        ]
        

        # Display the newest attendance dates first.
        ordering = ["-date", "student"]

    def clean(self):
        """
        Check that the school, student, classroom and
        recording staff member belong together.
        """
        super().clean()

        # Do not validate relationships until the required
        # objects have been selected.
        if not all([
            self.school_id,
            self.student_id,
            self.classroom_id,
            self.recorded_by_id,
        ]):
            return

        # The student must belong to this school.
        if self.student.school_id != self.school_id:
            raise ValidationError(
                "The student does not belong to this school."
            )
            
        
        # Ensure the annual enrolment belongs to this student
        # and the school recording the attendance.
        if self.enrollment_id:
            if self.enrollment.student_id != self.student_id:
                raise ValidationError({
                    "enrollment": (
                        "The selected enrolment must belong "
                        "to the selected student."
                    )
                })

            if self.enrollment.school_id != self.school_id:
                raise ValidationError({
                    "enrollment": (
                        "The enrolment must belong to this school."
                    )
                })
        
        
        
        # Ensure the lesson session belongs to this school
        # and matches the selected classroom.
        if self.lesson_session_id:
            lesson_timetable = self.lesson_session.timetable

            if self.lesson_session.school_id != self.school_id:
                raise ValidationError({
                    "lesson_session": (
                        "The lesson session must belong "
                        "to this school."
                    )
                })
                
                
            # Ensure the student's enrolment belongs to
            # the same academic year as the lesson.
            if self.enrollment_id:
                if (
                    self.enrollment.academic_year_id
                    != lesson_timetable.academic_year_id
                ):
                    raise ValidationError({
                        "enrollment": (
                            "The student's enrolment and "
                            "lesson must belong to the same "
                            "academic year."
                        )
                    })
                    

            if lesson_timetable.classroom_id != self.classroom_id:
                raise ValidationError({
                    "lesson_session": (
                        "The lesson session must match "
                        "the selected classroom."
                    )
                })
        
                    
        # The classroom must belong to this school.
        if self.classroom.school_id != self.school_id:
            raise ValidationError(
                "The classroom does not belong to this school."
            )

        
        # When an annual enrolment is available, use its
        # classroom as the source of truth for this year.
        if self.enrollment_id:
            if self.enrollment.classroom_id != self.classroom_id:
                raise ValidationError({
                    "classroom": (
                        "The classroom must match the "
                        "student's annual enrolment."
                    )
                })

        # Otherwise, retain the original classroom check
        # for transitional records without an enrolment.
        elif self.student.classroom_id != self.classroom_id:
            raise ValidationError({
                "classroom": (
                    "The classroom does not match "
                    "the student's classroom."
                )
            })
            

        # The staff member recording attendance must work
        # at the school that owns this attendance record.
        if self.recorded_by.school_id != self.school_id:
            raise ValidationError(
                "The staff member does not belong to this school."
            )

    def __str__(self):
        # Provide a readable description in Django Admin.
        return (
            f"{self.student} - "
            f"{self.date} - "
            f"{self.get_status_display()}"
        )
                        


class FeeItem(models.Model):
    # If school is NULL, this is a global ARWA fee item.
    # If school has a value, this item belongs only to that school.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="fee_items",
        blank=True,
        null=True,
    )

    # Name of the fee item.
    name = models.CharField(
        max_length=200
    )

    # Optional explanation of what the fee is for.
    description = models.TextField(
        blank=True,
        null=True
    )

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    # Controls whether the item can currently be used.
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            # A global fee item name must be unique globally.
            models.UniqueConstraint(
                fields=["name"],
                condition=models.Q(school__isnull=True),
                name="unique_global_fee_item_name",
            ),

            # A school cannot create two custom fee items
            # with exactly the same name.
            models.UniqueConstraint(
                fields=["school", "name"],
                condition=models.Q(school__isnull=False),
                name="unique_school_fee_item_name",
            ),
        ]

    def __str__(self):
        return self.name    
        
        
"""
    What FeeStructure represents
    A FeeStructure is the configuration for one academic level in one school for one academic year.
    For example:
    ARWA Demonstration School
    Academic Year: 2027
    Academic Level: Foundation Phase
    That is one Fee Structure.
    Another one would be:
    ARWA Demonstration School
    Academic Year: 2027
    Academic Level: Intermediate Phase
"""

class FeeStructure(models.Model):
    # Identify the school this fee structure belongs to.
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="fee_structures"
    )

    # Identify the academic year for which these fees apply.
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="fee_structures"
    )

    # Identify the academic level or phase to which
    # these fees apply.
    academic_level = models.ForeignKey(
        AcademicLevel,
        on_delete=models.PROTECT,
        related_name="fee_structures"
    )

    # Control whether this fee structure is currently
    # available for use.
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    # Automatically record when the fee structure was created.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever the fee structure changes.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # A school can have only one fee structure
        # for the same academic year and academic level.
        unique_together = (
            "school",
            "academic_year",
            "academic_level",
        )

    def __str__(self):
        # Clearly identify the fee structure in Admin.
        return (
            f"{self.school.name} - "
            f"{self.academic_year} - "
            f"{self.academic_level}"
        )   
        
        
"""
    This is the model that answers:
    “Which fee items are included in this particular fee structure, 
    and how much does the school charge for each one?”
    so it joins the fee items on a fee structure 
"""
        
class FeeStructureItem(models.Model):
    # Identify the fee structure this item belongs to.
    # Example: 2026 Foundation Phase fee structure.
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.CASCADE,
        related_name="items"
    )

    # Identify the official fee item selected by the school.
    # Example: School Fees, Transport, Sports & Clubs.
    fee_item = models.ForeignKey(
        FeeItem,
        on_delete=models.PROTECT,
        related_name="fee_structure_items"
    )

    # Store the amount the school charges for this
    # particular fee item.
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    # Automatically record when this fee item was added
    # to the fee structure.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # Automatically update whenever the fee item amount
    # or another field is changed.
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        # Prevent the same fee item from being added
        # twice to the same fee structure.
        unique_together = (
            "fee_structure",
            "fee_item",
        )

    def __str__(self):
        # Clearly identify the fee item and amount in Admin.
        return (
            f"{self.fee_structure} - "
            f"{self.fee_item.name} - "
            f"{self.amount}"
        )                            