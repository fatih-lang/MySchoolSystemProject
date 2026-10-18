from django.core.management.base import BaseCommand
from schools.models import Country
import pycountry


class Command(BaseCommand):
    help = "Load standardized ISO countries into the ARWA database."

    def handle(self, *args, **options):

        # Keep track of how many countries were created
        # and how many already existed.
        created_count = 0
        updated_count = 0

        # pycountry provides standardized ISO country data.
        for country_data in pycountry.countries:

            # Get the official country name.
            country_name = country_data.name

            # Get the ISO 3166-1 alpha-2 country code.
            #
            # Examples:
            # ZA = South Africa
            # US = United States
            # GB = United Kingdom
            country_code = country_data.alpha_2

            # Create the country if it does not exist.
            #
            # If the country already exists, update its name.
            country, created = Country.objects.update_or_create(
                code=country_code,
                defaults={
                    "name": country_name,
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        # Display the result in the terminal.
        self.stdout.write(
            self.style.SUCCESS(
                f"Country loading completed. "
                f"Created: {created_count}, "
                f"Updated: {updated_count}."
            )
        )
