from django.utils import translation



# The purpose of:
# class UserLanguageMiddleware:
# is to act as the bridge between the language preference we saved in the database and the language Django uses to display ARWA.
# Right now we have two separate things:
# UserLanguagePreference
        #↓
# Teacher → Arabic
# and:
# Django
        #↓
# Currently displaying English
# The middleware's job is to connect them:
# Teacher logs in
      #↓
# UserLanguagePreference
      #↓
# Arabic
      #↓
# UserLanguageMiddleware
      #↓
# Django activates Arabic
      #↓
# ARWA displays Arabic
# Why middleware?
# Middleware runs during the processing of a web request.
# So when a teacher opens:
# Teacher Dashboard
# the middleware gets a chance to say:
# "Who is this user?"
# Then:
# "Does this user have a language preference?"
# Then:
# "What language did they choose?"
# Then it tells Django:
# "Use that language for this request."

class UserLanguageMiddleware:
    """
    Activate the interface language selected by the logged-in user.

    The selected language is stored in UserLanguagePreference.
    The Language model then provides the Django locale code.
    """

    def __init__(self, get_response):
        # Store the next middleware/view Django should call.
        self.get_response = get_response

    def __call__(self, request):
        # Default ARWA interface language.
        language = "en"

        # Only logged-in users can have a personal
        # language preference.
        if request.user.is_authenticated:

            # Get the user's language preference.
            preference = getattr(
                request.user,
                "language_preference",
                None,
            )

            # Make sure the preference exists and has
            # a Django locale code.
            if preference and preference.language.django_code:
                language = preference.language.django_code

        # Activate the selected language for this request.
        translation.activate(language)

        # Continue processing the request.
        response = self.get_response(request)

        # Return the response to the user.
        return response