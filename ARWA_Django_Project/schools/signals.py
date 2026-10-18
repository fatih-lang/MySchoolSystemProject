"""
Reusable Django signals for ARWA profile-picture
and school-logo management.

These signals safely remove old uploaded images when:

1. A profile picture is replaced.
2. A school logo is replaced.
3. A record containing an uploaded image is deleted.

The old file is deleted only after the database
transaction successfully commits.
"""

from django.db import transaction
from django.db.models.signals import (
    pre_save,
    post_save,
    post_delete,
)
from django.dispatch import receiver

from .models import (
    Guardian,
    Student,
    StaffProfile,
    School,
)

from .file_utils import delete_stored_file


# ---------------------------------------------------------
# MODELS USING "profile_picture"
# ---------------------------------------------------------
#
# These models all store a person's profile picture
# using the same field name.
#
PROFILE_PICTURE_MODELS = (
    Guardian,
    Student,
    StaffProfile,
)


# ---------------------------------------------------------
# REMEMBER OLD PROFILE PICTURE
# ---------------------------------------------------------

def remember_old_profile_picture(
    sender,
    instance,
    **kwargs
):
    """
    Remember the existing profile picture before
    the record is updated.
    """

    # A new record has no previous database record.
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(
            pk=instance.pk
        )
    except sender.DoesNotExist:
        return

    # Get the old profile picture.
    old_picture = getattr(
        old_instance,
        "profile_picture",
        None,
    )

    # If there was no old picture, there is
    # nothing to remember.
    if not old_picture:
        return

    # Get the new picture.
    new_picture = getattr(
        instance,
        "profile_picture",
        None,
    )

    old_name = old_picture.name

    new_name = (
        new_picture.name
        if new_picture
        else None
    )

    # If the picture has not changed,
    # do not delete anything.
    if old_name == new_name:
        return

    # Temporarily remember the old filename.
    instance._old_profile_picture = old_name


# ---------------------------------------------------------
# DELETE OLD PROFILE PICTURE AFTER SAVE
# ---------------------------------------------------------

def delete_replaced_profile_picture(
    sender,
    instance,
    **kwargs
):
    """
    Delete the old profile picture only after
    the database transaction successfully commits.
    """

    old_picture = getattr(
        instance,
        "_old_profile_picture",
        None,
    )

    # Nothing changed.
    if not old_picture:
        return

    # Wait until the transaction successfully commits.
    transaction.on_commit(
        lambda name=old_picture:
            delete_stored_file(name)
    )

    # Remove the temporary value from memory.
    if hasattr(
        instance,
        "_old_profile_picture"
    ):
        del instance._old_profile_picture


# ---------------------------------------------------------
# DELETE PROFILE PICTURE WHEN RECORD IS DELETED
# ---------------------------------------------------------

def delete_profile_picture_on_delete(
    sender,
    instance,
    **kwargs
):
    """
    Delete the profile picture when the
    database record itself is deleted.
    """

    profile_picture = getattr(
        instance,
        "profile_picture",
        None,
    )

    if not profile_picture:
        return

    picture_name = profile_picture.name

    # Delete the physical file only after
    # the database transaction commits.
    transaction.on_commit(
        lambda name=picture_name:
            delete_stored_file(name)
    )


# ---------------------------------------------------------
# SCHOOL LOGO
# ---------------------------------------------------------

def remember_old_school_logo(
    sender,
    instance,
    **kwargs
):
    """
    Remember the old school logo before
    the School record is updated.
    """

    if not instance.pk:
        return

    try:
        old_school = School.objects.get(
            pk=instance.pk
        )
    except School.DoesNotExist:
        return

    old_logo = old_school.logo

    if not old_logo:
        return

    new_logo = instance.logo

    old_name = old_logo.name

    new_name = (
        new_logo.name
        if new_logo
        else None
    )

    # The logo has not changed.
    if old_name == new_name:
        return

    instance._old_school_logo = old_name


def delete_replaced_school_logo(
    sender,
    instance,
    **kwargs
):
    """
    Delete the previous school logo after
    the new logo has been successfully saved.
    """

    old_logo = getattr(
        instance,
        "_old_school_logo",
        None,
    )

    if not old_logo:
        return

    transaction.on_commit(
        lambda name=old_logo:
            delete_stored_file(name)
    )

    if hasattr(
        instance,
        "_old_school_logo"
    ):
        del instance._old_school_logo


def delete_school_logo_on_delete(
    sender,
    instance,
    **kwargs
):
    """
    Delete the school's logo when the
    School record is deleted.
    """

    logo = getattr(
        instance,
        "logo",
        None,
    )

    if not logo:
        return

    logo_name = logo.name

    transaction.on_commit(
        lambda name=logo_name:
            delete_stored_file(name)
    )


# ---------------------------------------------------------
# CONNECT PROFILE-PICTURE SIGNALS
# ---------------------------------------------------------

for model in PROFILE_PICTURE_MODELS:

    pre_save.connect(
        remember_old_profile_picture,
        sender=model,
        dispatch_uid=(
            f"remember_old_profile_picture_{model.__name__}"
        ),
    )

    post_save.connect(
        delete_replaced_profile_picture,
        sender=model,
        dispatch_uid=(
            f"delete_replaced_profile_picture_{model.__name__}"
        ),
    )

    post_delete.connect(
        delete_profile_picture_on_delete,
        sender=model,
        dispatch_uid=(
            f"delete_profile_picture_on_delete_{model.__name__}"
        ),
    )


# ---------------------------------------------------------
# CONNECT SCHOOL LOGO SIGNALS
# ---------------------------------------------------------

pre_save.connect(
    remember_old_school_logo,
    sender=School,
    dispatch_uid="remember_old_school_logo",
)

post_save.connect(
    delete_replaced_school_logo,
    sender=School,
    dispatch_uid="delete_replaced_school_logo",
)

post_delete.connect(
    delete_school_logo_on_delete,
    sender=School,
    dispatch_uid="delete_school_logo_on_delete",
)