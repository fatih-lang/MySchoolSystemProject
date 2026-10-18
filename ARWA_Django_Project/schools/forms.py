from django import forms

import json

from .models import (
    Term,
    School,
    SchoolType,
    AcademicStructureSchoolType,
    Language,
    UserLanguagePreference,
)


class TermForm(forms.ModelForm):

    # These are the names that will appear
    # in the Period Name dropdown.
    PERIOD_NAME_CHOICES = {
        "TERM": [
            ("1", "Term 1"),
            ("2", "Term 2"),
            ("3", "Term 3"),
            ("4", "Term 4"),
        ],
        "SEMESTER": [
            ("1", "Semester 1"),
            ("2", "Semester 2"),
        ],
        "TRIMESTER": [
            ("1", "Trimester 1"),
            ("2", "Trimester 2"),
            ("3", "Trimester 3"),
        ],
        "QUARTER": [
            ("1", "Quarter 1"),
            ("2", "Quarter 2"),
            ("3", "Quarter 3"),
            ("4", "Quarter 4"),
        ],
        "YEAR": [
            ("1", "Year"),
        ],
    }

    # Create the Period Name dropdown.
    #
    # The choices will be populated based on
    # the selected Period Type.
    name = forms.ChoiceField(
        choices=[],
        label="Period Name",
    )
    
    def __init__(self, *args, **kwargs):
        # Initialize the normal ModelForm first.
        super().__init__(*args, **kwargs)
    
        # Get the selected Period Type.
        #
        # When editing an existing period, this comes
        # from the existing database record.
        period_type = self.initial.get("period_type")
    
        # When submitting the form, use the submitted
        # Period Type instead.
        if self.data.get("period_type"):
            period_type = self.data.get("period_type")
    
        # Populate the Period Name dropdown with the
        # choices belonging to the selected Period Type.
        if period_type:
            self.fields["name"].choices = (
                self.PERIOD_NAME_CHOICES.get(
                    period_type,
                    []
                )
            )
    
        # Display the Start Date using DD/MM/YYYY.
        self.fields["start_date"].input_formats = [
            "%d/%m/%Y"
        ]
    
        # Display the End Date using DD/MM/YYYY.
        self.fields["end_date"].input_formats = [
            "%d/%m/%Y"
        ]
    
        # Use a text input so ARWA can consistently
        # display and accept DD/MM/YYYY.
        self.fields["start_date"].widget = forms.DateInput(
            format="%d/%m/%Y",
            attrs={
                "placeholder": "DD/MM/YYYY"
            }
        )
    
        self.fields["end_date"].widget = forms.DateInput(
            format="%d/%m/%Y",
            attrs={
                "placeholder": "DD/MM/YYYY"
            }
        )
        
    
    class Meta:
        model = Term

        # Only these fields should appear
        # in the Add/Edit Academic Period form.
        #
        # period_number is intentionally excluded
        # because ARWA calculates it automatically
        # from the selected Period Name.
        fields = [
            "academic_year",
            "period_type",
            "name",
            "start_date",
            "end_date",
            "status",
        ]
             
        
    def clean(self):
        # Get all submitted form data.
        cleaned_data = super().clean()
    
        # Get the selected period type.
        period_type = cleaned_data.get("period_type")
    
        # Get the selected period name.
        name = cleaned_data.get("name")
    
        # Get the selected start date.
        start_date = cleaned_data.get("start_date")
    
        # Get the selected end date.
        end_date = cleaned_data.get("end_date")
    
        # Make sure both period values were provided.
        if period_type and name:
    
            # Get the valid choices for this period type.
            valid_choices = dict(
                self.PERIOD_NAME_CHOICES.get(
                    period_type,
                    []
                )
            )
    
            # Check whether the selected name
            # belongs to the selected period type.
            if name not in valid_choices:
                self.add_error(
                    "name",
                    "The selected Period Name does not match "
                    "the selected Period Type."
                )
    
        # Make sure the End Date is not before
        # the Start Date.
        if start_date and end_date:
            if end_date < start_date:
                self.add_error(
                    "end_date",
                    "The End Date cannot be before the Start Date."
                )
    
        return cleaned_data
        
    def save(self, commit=True):
        # Get the Term object without saving it yet.
        instance = super().save(commit=False)

        # Get the selected Period Type.
        period_type = self.cleaned_data.get("period_type")

        # Get the selected Period Name number.
        #
        # Example:
        # "2" from "Semester 2"
        period_number = self.cleaned_data.get("name")

        # Get the correct choices for the selected
        # Period Type.
        choices = dict(
            self.PERIOD_NAME_CHOICES.get(
                period_type,
                []
            )
        )

        # Get the human-readable Period Name.
        #
        # Example:
        # "Semester 2"
        period_name = choices.get(
            period_number
        )

        # Store the period number in the database.
        if period_number:
            instance.period_number = int(
                period_number
            )

        # Store the full display name in the database.
        if period_name:
            instance.name = period_name

        # Save the object if commit=True.
        if commit:
            instance.save()

            # Save any many-to-many form data.
            self.save_m2m()

        return instance  
        


class SchoolForm(forms.ModelForm):

    # Use a normal multiple-select field for School Types.
    #
    # This allows ARWA's JavaScript to control the choices
    # in the same way as the TermForm Period Name dropdown.
    school_types = forms.ModelMultipleChoiceField(
        queryset=SchoolType.objects.none()    ,
        required=False,
        widget=forms.SelectMultiple()
    )
    
    # Store the database-generated school type
    # compatibility information for JavaScript.
    school_type_compatibility = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = School

        fields = [
            "name",
            "school_code",
            "registration_number",
            "country",
            "timezone",
            "education_system",
            "academic_structure",
            "school_types",
            "address",
            "city",
            "state_province",
            "postal_code",
            "email",
            "website",
            "hotline",
            "mobile",
            "logo",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        # Initialize the normal ModelForm first.
        super().__init__(*args, **kwargs)
        
        # Get every Academic Structure + School Type
        # compatibility record from the database.
        compatibility_records = (
            AcademicStructureSchoolType.objects
            .select_related(
                "academic_structure",
                "school_type",
            )
            .values(
                "academic_structure_id",
                "school_type_id",
                "school_type__name",
            )
        )
        
        # Build a dictionary that JavaScript can understand.
        #
        # Example:
        #
        # {
        #     "1": [
        #         ["1", "Primary School"],
        #         ["2", "Secondary/High School"]
        #     ],
        #     "2": [
        #         ["3", "College"],
        #         ["4", "University"]
        #     ]
        # }
        compatibility_map = {}
        
        for record in compatibility_records:
        
            academic_structure_id = str(
                record["academic_structure_id"]
            )
        
            school_type_id = str(
                record["school_type_id"]
            )
        
            school_type_name = (
                record["school_type__name"]
            )
        
            compatibility_map.setdefault(
                academic_structure_id,
                []
            ).append(
                [
                    school_type_id,
                    school_type_name,
                ]
            )
            
        # Store the database-generated compatibility map
        # inside the hidden form field.
        #
        # JavaScript will read this hidden value and use it
        # to populate the School Types dropdown.
        self.initial["school_type_compatibility"] = (
            json.dumps(compatibility_map)
        )

        # Check whether an Academic Structure was selected
        # in the submitted form.
        academic_structure_id = self.data.get(
            "academic_structure"
        )

        # When editing an existing school, use its current
        # Academic Structure if the form has not been submitted.
        if (
            not academic_structure_id
            and self.instance
            and self.instance.pk
            and self.instance.academic_structure
        ):
            academic_structure_id = (
                self.instance.academic_structure_id
            )

        # If an Academic Structure has been selected,
        # find the School Types allowed for it.
        if academic_structure_id:

            allowed_school_type_ids = (
                AcademicStructureSchoolType.objects
                .filter(
                    academic_structure_id=academic_structure_id
                )
                .values_list(
                    "school_type_id",
                    flat=True
                )
            )

            # Only show School Types that are compatible
            # with the selected Academic Structure.
            self.fields["school_types"].queryset = (
                SchoolType.objects.filter(
                    id__in=allowed_school_type_ids
                )
            )
            


class UserLanguagePreferenceForm(forms.ModelForm):
    """
    Form used to allow a logged-in ARWA user
    to select their interface language.
    """

    class Meta:
        model = UserLanguagePreference

        # Only the language preference is editable.
        fields = ("language",)

    def __init__(self, *args, **kwargs):
        # Run the normal ModelForm setup first.
        super().__init__(*args, **kwargs)

        # Only show languages that ARWA has translated
        # and officially made available.
        self.fields["language"].queryset = (
            Language.available_languages()
        )            