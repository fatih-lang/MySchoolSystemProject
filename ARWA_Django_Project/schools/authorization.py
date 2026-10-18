from functools import wraps

from django.core.exceptions import PermissionDenied




"""
ARWA Staff Authorization

This module contains reusable backend authorization helpers.

The purpose is to make authorization decisions using the
ARWA staff architecture instead of checking role names
directly inside individual views.

Authorization considers:

    StaffProfile
        ↓
    StaffRole
        ↓
    StaffSchoolTypeResponsibility
        ↓
    School / School Type
"""


def get_staff_profile(user):
    """
    Return the StaffProfile belonging to a Django User.

    If the user does not have a StaffProfile, return None.

    This gives the rest of the authorization system one
    consistent way to obtain the staff member.
    """

    if not user or not user.is_authenticated:
        return None

    return getattr(user, "staffprofile", None)


def is_staff_member(user):
    """
    Check whether the authenticated user has a StaffProfile.

    Returns:
        True  -> User is an ARWA staff member.
        False -> User is not an ARWA staff member.
    """

    return get_staff_profile(user) is not None


def has_role(user, role_name):
    """
    Check whether the staff member has a specific StaffRole.

    Example:

        has_role(request.user, "Director")

    """

    staff_profile = get_staff_profile(user)

    if not staff_profile:
        return False

    return staff_profile.role.name.strip().lower() == role_name.strip().lower()


def has_rank_level(user, maximum_rank):
    """
    Check whether the staff member belongs to a sufficiently
    senior organisational rank.

    Lower rank numbers represent greater authority.

    Example:

        Rank 1 = Director
        Rank 2 = Principal
        Rank 3 = Administration
        Rank 4 = Teacher
        Rank 5 = Support

    Therefore:

        has_rank_level(user, 2)

    allows Rank 1 and Rank 2 staff.

    This does NOT mean that every Rank 1 or Rank 2 person
    automatically receives every permission.

    Additional scope and operation checks are still required.
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile:
        return False

    return staff_profile.role.rank_level <= maximum_rank


def is_financial_role(user):
    """
    Check whether the staff member's role has financial
    responsibility.
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile:
        return False

    return staff_profile.role.can_access_billing()


def requires_2fa(user):
    """
    Check whether the staff member's role requires 2FA.
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile:
        return False

    return staff_profile.role.requires_2fa


def has_completed_2fa_enrollment(user):
    """
    Check whether the staff member has enrolled in 2FA.

    The actual authentication enforcement will be handled
    by the security system later.
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile:
        return False

    return staff_profile.two_factor_enrolled


def can_access_financial_area(user):
    """
    Determine whether the staff member can access a
    financial area of ARWA.

    This uses the StaffRole financial capability rather
    than checking role names such as 'Director' or 'Accountant'.
    """

    return is_financial_role(user)


def can_manage_senior_staff(user):
    """
    Determine whether the staff member is senior enough
    to enter the senior-staff management area.

    For now, this means Rank 1.

    More detailed permission checks will be added later
    for specific operations.
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile:
        return False

    return staff_profile.role.rank_level == 1
    
    

def has_school_type_responsibility(user, school_type):
    """
    Check whether the staff member has an active responsibility
    for the supplied school type.

    This is the scope check.

    A role tells us WHAT authority a person has.

    StaffSchoolTypeResponsibility tells us WHERE
    that authority applies.
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile or not school_type:
        return False

    return staff_profile.school_type_responsibilities.filter(
        school_type=school_type,
        status="ACTIVE",
    ).exists()


def has_school_type_responsibility_id(user, school_type_id):
    """
    Same responsibility check, but accepts a SchoolType ID.

    This is useful when the school type comes from
    a URL parameter, form submission, or database lookup.
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile or not school_type_id:
        return False

    return staff_profile.school_type_responsibilities.filter(
        school_type_id=school_type_id,
        status="ACTIVE",
    ).exists()


def get_responsible_school_types(user):
    """
    Return all active school types for which this staff member
    currently has responsibility.

    This will later power the Director school-type switcher.

    Example:

        Director
        ├── Primary School
        └── Secondary School
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile:
        return []

    return staff_profile.school_type_responsibilities.filter(
        status="ACTIVE"
    ).select_related("school_type")


def can_operate_in_school_type(user, school_type):
    """
    Determine whether the staff member can operate within
    the supplied school-type context.

    The staff member must:

        1. Be an authenticated ARWA staff member.
        2. Have an active responsibility for that school type.

    Role authority and specific operation permissions will
    be checked separately.
    """

    return has_school_type_responsibility(
        user,
        school_type
    )
    
    

def can_manage_senior_staff_in_school_type(user, school_type):
    """
    Determine whether the staff member can manage senior staff
    within the supplied school-type context.

    This combines two separate authorization questions:

        1. Does the staff member have sufficient authority
           to manage senior staff?

        2. Does the staff member have active responsibility
           for this school type?

    Both conditions must be true.

    This is important for ARWA because a Director may be
    responsible for more than one school type, while the
    actual management action must still be limited to the
    selected school-type context.
    """

    if not can_manage_senior_staff(user):
        return False

    if not can_operate_in_school_type(user, school_type):
        return False

    return True
    
    
def can_control_staff_accounts(user):
    """
    Determine whether the staff member can perform
    administrative account-control actions.

    Account-control actions include operations such as:

        - Blocking a staff account
        - Unblocking a staff account
        - Restricting access during an emergency

    This is a highly sensitive operation, so access is
    currently limited to the highest organisational rank.

    The actual account-control view will perform additional
    checks before changing an account.
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile:
        return False

    return staff_profile.role.rank_level == 1
    

def can_manage_currency(user):
    """
    Determine whether the staff member can manage
    school currency configuration.

    Currency management includes operations such as:

        - Changing the school's primary currency
        - Adding a secondary currency
        - Removing a secondary currency

    Currency configuration is a high-level institutional
    responsibility in ARWA.

    The actual currency operation will later perform
    additional school and transaction checks.
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile:
        return False

    return staff_profile.role.rank_level == 1


def can_manage_currency_in_school_type(user, school_type):
    """
    Check whether a staff member is authorized to manage
    currency within a specific school-type context.

    Authorization requires:

        1. A valid ARWA staff profile.
        2. Executive authority (rank level 1).
        3. The school type belongs to the staff member's school.
        4. Active responsibility for that school type.

    This prevents a staff member from using a valid
    responsibility in one school to access another school's
    context.
    """

    staff_profile = get_staff_profile(user)

    # The user must have an ARWA staff profile.
    if not staff_profile:
        return False

    # Currency management is restricted to executive authority.
    if staff_profile.role.rank_level != 1:
        return False

    # A school type must be supplied.
    if not school_type:
        return False

    # The requested school type must belong to the
    # staff member's school.
    if not staff_profile.school.school_types.filter(
        pk=school_type.pk
    ).exists():
        return False

    # Finally, the executive must have an ACTIVE
    # responsibility for that school type.
    return has_school_type_responsibility(
        user,
        school_type,
    )
        
    

def can_view_financial_audit(user):
    """
    Determine whether the staff member can view
    financial audit information.

    Financial audit information may include:

        - Who modified an invoice
        - Who changed a fee structure
        - Who recorded or changed a payment
        - When a financial record was changed
        - What financial action was performed

    This permission controls access to the audit information.
    It does not itself allow the staff member to modify
    financial records.
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile:
        return False

    return staff_profile.role.rank_level == 1
    
    
def can_view_academic_audit(user):
    """
    Determine whether the staff member can view
    academic audit information.

    Academic audit information may include:

        - Who modified a grading matrix
        - Who entered or corrected examination results
        - Who verified results
        - Who finalized results
        - When an academic record was changed
        - What academic action was performed

    This permission controls access to the academic
    audit information.

    It does not give the staff member permission to
    modify academic records.
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile:
        return False

    return staff_profile.role.rank_level == 1    
    

def can_manage_communications(user):
    """
    Determine whether the staff member can manage
    high-level institutional communications.

    Communication management may include:

        - Reviewing official notices
        - Publishing institutional announcements
        - Publishing board declarations
        - Managing strategic school communications

    This permission controls access to the communication
    management area.

    The actual communication view will perform additional
    checks before publishing or modifying a communication.
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile:
        return False

    return staff_profile.role.rank_level == 1    
    

def can_view_staff_oversight(user):
    """
    Determine whether the staff member can access
    the executive staff oversight area.

    Staff oversight allows an authorised executive to
    review staff information such as:

        - Staff members
        - Staff roles
        - Departments
        - Work status
        - School-type responsibilities
        - Staff account status

    This permission is for oversight and visibility.

    It does not automatically grant permission to edit
    staff records or change staff roles.
    """

    staff_profile = get_staff_profile(user)

    if not staff_profile:
        return False

    return staff_profile.role.rank_level == 1    
    

def require_authorization(permission_function):
    """
    Protect a Django view with an ARWA authorization function.

    The supplied permission function must accept the
    authenticated user as its first argument.

    Example:

        @require_authorization(can_manage_currency)
        def currency_management(request):
            ...

    If the authorization function returns True,
    the view is allowed to continue.

    If it returns False, Django raises PermissionDenied
    and the protected view is not executed.
    """

    def decorator(view_function):
        @wraps(view_function)
        def wrapped_view(request, *args, **kwargs):

            # Ask the supplied authorization function
            # whether this user is allowed to access
            # the protected view.
            if not permission_function(request.user):

                # Stop the request immediately.
                #
                # Django will treat this as a permission
                # failure rather than allowing the view
                # to continue.
                raise PermissionDenied

            # Authorization succeeded.
            #
            # Continue to the original Django view.
            return view_function(
                request,
                *args,
                **kwargs
            )

        return wrapped_view

    return decorator    
    
    
    
def require_school_type_authorization(
    permission_function,
    school_type_getter,
):
    """
    Protect a Django view using a school-type-aware
    authorization function.

    The permission function must accept:

        user
        school_type

    The school_type_getter is responsible for obtaining
    the school type from the current request.

    This keeps the authorization system reusable because
    different views can obtain their school-type context
    in different ways.
    """
    
    def decorator(view_function):

        @wraps(view_function)
        def wrapped_view(request, *args, **kwargs):

            # Determine which school type the current request
            # is operating in.
            school_type = school_type_getter(
                request,
                *args,
                **kwargs,
            )

            # Deny access if no valid school-type context
            # was supplied or if authorization fails.
            if not permission_function(
                request.user,
                school_type,
            ):
                raise PermissionDenied

            return view_function(
                request,
                *args,
                **kwargs,
            )

        return wrapped_view

    return decorator    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    