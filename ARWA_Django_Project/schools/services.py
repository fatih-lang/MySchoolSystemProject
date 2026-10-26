# This file will eventually contain the business logic for operations such as:
# Register student
     # ↓
# Generate student number
     # ↓
# Create Django login
     # ↓
# Connect login to Student
     # ↓
# Complete registration




# Import Django's transaction tool.
# This will allow the complete registration process
# to succeed or fail as one database operation.
from django.db import transaction

# Import Django's built-in User model.
# This will be used to create the student's login account.
from django.contrib.auth.models import User

# Import the Student model.
# This will allow the registration service
# to create and connect the student's record.
# Import the models needed for student registration.
from .models import (
    Student,
    StudentNumberSequence,
    StudentEnrollment,
    AcademicYear,
    SchoolAcademicLevel,
    AssessmentConfiguration,
    StudentAssessmentResult,
    HomeworkSubmission,
    ExaminationResult,
)

@transaction.atomic
def register_student(
    school,
    first_name,
    last_name,
    id_or_passport,
    nationality,
    gender,
    date_of_birth,
    academic_level,
    classroom,
    password,
):

    # Make sure the selected academic level belongs
    # to the school registering this student.
    if academic_level.school_id != school.id:
        raise ValueError(
            "The selected academic level does not belong "
            "to this school."
        )
        
    # Make sure the selected classroom belongs
    # to the school registering this student.
    if classroom.school_id != school.id:
        raise ValueError(
            "The selected classroom does not belong "
            "to this school."
        )

    # Make sure the classroom belongs to the
    # academic level selected for this student.
    if classroom.academic_level_id != academic_level.id:
        raise ValueError(
            "The selected classroom does not belong "
            "to the selected academic level."
        )
        
    # Find the active academic years for this school.
    active_academic_years = AcademicYear.objects.filter(
        school=school,
        status="ACTIVE",
    )

    # A student must be registered into exactly one
    # active academic year.
    if active_academic_years.count() != 1:
        raise ValueError(
            "This school must have exactly one active "
            "academic year before students can be registered."
        )

    # Get the school's active academic year.
    academic_year = active_academic_years.first()    
        
    
    # Make sure the student has been given a password.
    if not password:
        raise ValueError(
            "A student password is required."
        )     
        
    # Make sure this school has a student-number sequence.
    # If one already exists, keep using the existing sequence.
    # Otherwise, create one starting at the default number.
    StudentNumberSequence.objects.get_or_create(
        school=school
    )
    
    # Create the Student record first.
    # Student.save() will automatically generate
    # the student's unique student number.
    student = Student(
        school=school,
        first_name=first_name,
        last_name=last_name,
        id_or_passport=id_or_passport,
        nationality=nationality,
        gender=gender,
        date_of_birth=date_of_birth,
        academic_level=academic_level,
        classroom=classroom,
    )

    # Save the student so ARWA generates the student number.
    student.save()
    
    # Create the student's Django login account.
    # The generated student number becomes the username.
    user = User.objects.create_user(
        username=student.student_number,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    
    # Connect the Django login account to the Student record.
    # This allows ARWA to know which login account belongs
    # to this particular student.
    student.user = user

    # Save the connection between the Student and User.
    student.save(update_fields=["user"])
    
    # Create the student's annual enrolment record.
    # This preserves the student's academic placement
    # for the selected academic year.
    enrollment = StudentEnrollment(
        student=student,
        school=school,
        academic_year=academic_year,
        academic_level=academic_level,
        classroom=classroom,
    )

    # Validate the enrolment before saving it.
    # This checks that the school, year, level and
    # classroom belong together.
    enrollment.full_clean()

    # Save the validated annual enrolment.
    enrollment.save()

    # Return both objects created during registration.
    return student, user
    
    

def calculate_academic_performance(student):
    """
    Calculate a student's overall academic performance
    using the assessment configuration assigned to the
    student's academic level.

    The calculation logic will be added step by step.
    """
    # Find the school's current active academic year.
    #
    # ARWA requires exactly one active academic year
    # for a school when student academic calculations
    # are being performed.
    active_academic_years = AcademicYear.objects.filter(
        school=student.school,
        status="ACTIVE",
    )

    # There must be exactly one active academic year.
    if active_academic_years.count() != 1:
        raise ValueError(
            "This school must have exactly one active "
            "academic year before academic performance "
            "can be calculated."
        )

    # Store the school's current academic year.
    academic_year = active_academic_years.first()  
    
    
    # Find the student's enrollment for the current academic year.
    #
    # This gives us the student's academic level and classroom
    # for the year whose academic performance we are calculating.
    enrollment = StudentEnrollment.objects.filter(
        student=student,
        school=student.school,
        academic_year=academic_year,
        status="ACTIVE",
    ).first()

    # A student must have an active enrollment before
    # academic performance can be calculated.
    if enrollment is None:
        raise ValueError(
            "This student does not have an active enrollment "
            "for the current academic year."
        )
        
    # The student's enrollment already stores the
    # school-specific academic level.
    #
    # StudentEnrollment.academic_level is a ForeignKey
    # to SchoolAcademicLevel, so there is no need to
    # query SchoolAcademicLevel again.
    school_academic_level = enrollment.academic_level
    
    # The student's academic level must be configured
    # for this school before academic performance can
    # be calculated.
    if school_academic_level is None:
        raise ValueError(
            "This student's academic level is not configured "
            "for the school."
        ) 
        
    # Find assessment configurations assigned to this
    # student's school academic level.
    #
    # The configuration must belong to the same school
    # and must currently be active.
    active_configurations = (
        AssessmentConfiguration.objects
        .filter(
            school=student.school,
            is_active=True,
            academic_levels__school_academic_level=school_academic_level,
        )
        .distinct()
    ) 
    
    # There must be exactly one active assessment
    # configuration for the student's academic level.
    #
    # ARWA must never guess which configuration to use
    # when multiple active configurations exist.
    if active_configurations.count() != 1:
        raise ValueError(
            "This student's academic level must have exactly "
            "one active assessment configuration."
        )

    # Store the assessment configuration that will
    # control this student's academic performance calculation.
    assessment_configuration = active_configurations.first() 
    
    # Get all assessment components belonging to the
    # selected assessment configuration.
    #
    # These components determine which types of academic
    # work contribute to the student's overall performance
    # and how much each type contributes.
    components = assessment_configuration.components.all() 
    
    # Make sure the assessment configuration is complete
    # before using it to calculate academic performance.
    #
    # The component weights must add up to exactly 100%.
    assessment_configuration.validate_weights()  
    
    # Store the calculated result for each assessment
    # component separately.
    #
    # This allows the Director dashboard to show
    # how the overall academic performance was calculated.
    component_results = []   
    
    # Keep track of assessment components for which
    # the student does not yet have usable results.
    #
    # Missing data must never be treated as 0%.
    # ARWA will use this information later to determine
    # whether the overall academic performance is complete.
    missing_components = []
    
    # Process each assessment component configured
    # for this student's academic level.
    #
    # Each component may obtain its marks from a
    # different source, such as StudentAssessmentResult,
    # HomeworkSubmission, or ExaminationResult.
    for component in components:
        # The specific calculation for each component
        # will be added step by step.
        
        # Read the configured component type.
        #
        # Examples:
        # "TEST"
        # "HOMEWORK"
        # "PROJECT"
        # "EXAMINATION"
        component_type = component.component_type 
        
        # These component types obtain their marks from
        # StudentAssessmentResult.
        assessment_component_types = {
            "ASSIGNMENT",
            "PROJECT",
            "TEST",
            "PRACTICAL",
            "ORAL",
            "QUIZ",
            "OTHER",
        }

        # Check whether the current component is an
        # assessment-based component.
        if component_type in assessment_component_types:
            
            # Find this student's results for assessments
            # belonging to the current academic year.
            #
            # The assessment type must match the component
            # currently being calculated.
            assessment_results = (
                StudentAssessmentResult.objects
                .filter(
                    student=student,
                    assessment__school=student.school,
                    assessment__academic_year=academic_year,
                    assessment__assessment_type=component_type,
                    assessment__classroom=enrollment.classroom,
                    assessment__status="ACTIVE",
                )
            )
            
            # Check whether the student has any results
            # for this assessment component.
            #
            # We do not treat missing results as 0%.
            # Missing work and a genuine mark of 0% are
            # two different things.
            if not assessment_results.exists():
                # Record the component as incomplete instead
                # of treating the missing result as 0%.
                missing_components.append({
                    "component_type": component_type,
                    "name": component.name,
                    "weight": float(component.weight),
                })

                # Move to the next configured component.
                continue
                
            # Calculate the total marks earned across
            # all assessments in this component.
            total_marks = sum(
                result.mark
                for result in assessment_results
            )  
            
            # Calculate the total marks possible across
            # all assessments in this component.
            total_possible = sum(
                result.assessment.total_possible
                for result in assessment_results
            )
            
            # Convert the student's total marks into
            # a percentage for this assessment component.
            component_percentage = (
                total_marks / total_possible
            ) * 100  
            
            # Apply the school's configured weight to
            # this component's percentage.
            component_contribution = (
                component_percentage * float(component.weight)
            ) / 100   
            
            
            # Store this component's calculation so ARWA
            # can use it later when producing the overall
            # academic performance result.
            component_results.append({
                "component_type": component_type,
                "name": component.name,
                "percentage": component_percentage,
                "weight": float(component.weight),
                "contribution": component_contribution,
            })
            
        # Homework marks are stored through
        # HomeworkSubmission rather than
        # StudentAssessmentResult.
        if component_type == "HOMEWORK":
                
                # Find this student's homework submissions
                # for the current academic year and classroom.
                #
                # Only homework belonging to this school and
                # current academic year should contribute to
                # academic performance.
                homework_submissions = (
                    HomeworkSubmission.objects
                    .filter(
                        student_enrollment=enrollment,
                        homework__school=student.school,
                        homework__academic_year=academic_year,
                        homework__classroom=enrollment.classroom,
                    )
                )
                
                # Only marked homework can contribute to
                # academic performance.
                #
                # Submitted homework without a mark is not
                # treated as zero.
                homework_submissions = homework_submissions.filter(
                    marking_status="MARKED",
                )
                
                # If none of the student's homework has been
                # marked yet, there is no homework percentage
                # to calculate.
                #
                # We do not interpret unmarked homework as 0%.
                if not homework_submissions.exists():
                    # Record the homework component as incomplete
                    # instead of treating missing homework marks
                    # as 0%.
                    missing_components.append({
                        "component_type": component_type,
                        "name": component.name,
                        "weight": float(component.weight),
                    })
    
                    # Move to the next configured component.
                    continue
                        
                # Calculate the total marks earned from
                # all marked homework submissions.
                total_marks = sum(
                    submission.mark
                    for submission in homework_submissions
                ) 
                
                
                # Calculate the total marks possible across
                # all marked homework submissions.
                total_possible = sum(
                    submission.homework.total_possible
                    for submission in homework_submissions
                )
                
                # Convert the student's total homework marks
                # into a percentage.
                homework_percentage = (
                    total_marks / total_possible
                ) * 100
                
                # Apply the school's configured weight to
                # the student's homework percentage.
                homework_contribution = (
                    homework_percentage * float(component.weight)
                ) / 100   
                
                # Store the homework calculation so ARWA
                # can include it in the overall academic
                # performance breakdown.
                component_results.append({
                    "component_type": component_type,
                    "name": component.name,
                    "percentage": homework_percentage,
                    "weight": float(component.weight),
                    "contribution": homework_contribution,
                }) 
                
        # Examination results are stored separately from
        # normal assessments.
        #
        # Only FINALIZED examination results are allowed
        # to contribute to official academic performance.
        if component_type == "EXAMINATION":
                
                    # Find this student's examination results
                    # for the current academic year and classroom.
                    #
                    # ExaminationResult stores its academic year,
                    # classroom and total possible marks through
                    # its related Assessment.
                    #
                    # Only FINALIZED examination results are included
                    # because only finalized results are official in ARWA.
                    examination_results = (
                        ExaminationResult.objects
                        .filter(
                            student=student,
                            assessment__school=student.school,
                            assessment__academic_year=academic_year,
                            assessment__classroom=enrollment.classroom,
                            assessment__assessment_type="EXAMINATION",
                            status="FINALIZED",
                        )
                    )
                
                    # Check whether the student has any finalized
                    # examination results for this component.
                    #
                    # Missing examination results are not treated
                    # as a mark of 0%.
                    if not examination_results.exists():
                
                        # Record the examination component as incomplete.
                        missing_components.append({
                            "component_type": component_type,
                            "name": component.name,
                            "weight": float(component.weight),
                        })
                
                        # Move to the next configured component.
                        continue
                
                    # Calculate the total examination marks
                    # earned by the student.
                    total_marks = sum(
                        result.mark
                        for result in examination_results
                    )
                
                    # Calculate the total marks possible across
                    # all finalized examinations.
                    total_possible = sum(
                        result.assessment.total_possible
                        for result in examination_results
                    )
                
                    # Convert the student's finalized examination
                    # marks into a percentage.
                    examination_percentage = (
                        total_marks / total_possible
                    ) * 100
                
                    # Apply the school's configured weight.
                    examination_contribution = (
                        examination_percentage * float(component.weight)
                    ) / 100
                
                    # Store the examination calculation so ARWA
                    # can show exactly how this component
                    # contributed to the student's performance.
                    component_results.append({
                        "component_type": component_type,
                        "name": component.name,
                        "percentage": examination_percentage,
                        "weight": float(component.weight),
                        "contribution": examination_contribution,
                    })
                    
    # Add the weighted contributions from all
    # components for which usable results exist.
    overall_contribution = sum(
        result["contribution"]
        for result in component_results
    ) 
    
    # Determine whether all configured assessment
    # components have usable results.
    #
    # A student with missing component results must
    # not receive a misleading "complete" performance
    # percentage.
    is_complete = len(missing_components) == 0   
    
    # Only a complete set of configured assessment
    # components can produce an official overall
    # academic performance percentage.
    if is_complete:
        overall_percentage = overall_contribution
    else:
        overall_percentage = None    
        
        
    # Return the academic performance information
    # in a structured format so the Director dashboard
    # and other ARWA services can use it.
    return {
        "student": student,
        "academic_year": academic_year,
        "academic_level": school_academic_level,
        "assessment_configuration": assessment_configuration,
        "is_complete": is_complete,
        "overall_percentage": overall_percentage,
        "component_results": component_results,
        "missing_components": missing_components,
    }                   