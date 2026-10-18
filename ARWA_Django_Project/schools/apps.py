# apps.py tells Django things about the schools app and gives us a place to run code when the app is loaded.
# For example:
# class SchoolsConfig(AppConfig):
    # name = 'schools'
# means:
# "This configuration belongs to the schools Django app."
# And when we add:
# def ready(self):
    # from . import signals
# we're telling Django:
# "When the schools app starts, load the signals defined in signals.py."

from django.apps import AppConfig


class SchoolsConfig(AppConfig):
    name = 'schools'

    def ready(self):
        # Load ARWA's model signals when the application starts.
        from . import signals
