"""
Reusable file-management helpers for ARWA.

This module contains utilities for safely removing
uploaded files from Django storage.
"""

from django.core.files.storage import default_storage


def delete_stored_file(file_field):
    """
    Delete a file from Django's configured storage.

    The function can receive either a Django FileField/ImageField
    value or a stored file name.
    """

    # If there is no file value, there is nothing to delete.
    if not file_field:
        return

    # If a Django FileField/ImageField was supplied,
    # get its stored file name.
    #
    # If a plain file name was supplied, use it directly.
    file_name = getattr(
        file_field,
        "name",
        file_field,
    )

    # Make sure we have a valid file name and that
    # the file actually exists in the configured storage.
    if (
        file_name
        and default_storage.exists(file_name)
    ):

        # Delete the actual file from Django's
        # configured storage backend.
        default_storage.delete(file_name)