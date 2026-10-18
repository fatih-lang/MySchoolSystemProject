from django.core.management.base import BaseCommand

from schools.models import Currency, Country

import pycountry

from babel.numbers import (
    get_currency_precision,
    get_currency_symbol,
    get_territory_currencies,
)


class Command(BaseCommand):
    help = "Load standardized international currencies into ARWA."

    def handle(self, *args, **options):

        # Keep track of how many currency records
        # were created and updated.
        created_count = 0
        updated_count = 0

        # Keep track of the currency codes that are
        # currently used as legal tender somewhere.
        active_currency_codes = set()

        # ---------------------------------------------------------
        # STEP 1:
        # Load the ISO currency records.
        # ---------------------------------------------------------

        for currency_data in pycountry.currencies:

            # Get the internationally recognised
            # three-letter ISO 4217 currency code.
            #
            # Examples:
            # ZAR = South African Rand
            # USD = United States Dollar
            # GBP = Pound Sterling
            code = currency_data.alpha_3

            # Get the official currency name.
            name = currency_data.name

            # -----------------------------------------------------
            # Get currency information from Babel/CLDR.
            # -----------------------------------------------------

            try:
                # Get the currency symbol.
                #
                # Example:
                # ZAR -> R
                # USD -> $
                # GBP -> £
                symbol = get_currency_symbol(
                    code,
                    locale="en",
                )

            except Exception:
                # Some ISO currency codes may not have
                # symbol information in CLDR.
                #
                # In that situation we use the ISO code
                # temporarily as the display symbol.
                symbol = code

            try:
                # Get the number of decimal places normally
                # used by this currency.
                #
                # Examples:
                # ZAR -> 2
                # USD -> 2
                # JPY -> 0
                # KWD -> 3
                decimal_places = get_currency_precision(code)

            except Exception:
                # Most currencies use two decimal places.
                # This is our safe fallback when CLDR
                # does not provide precision information.
                decimal_places = 2

            # -----------------------------------------------------
            # Create or update the currency.
            # -----------------------------------------------------

            currency, created = Currency.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "symbol": symbol,
                    "decimal_places": decimal_places,
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        # ---------------------------------------------------------
        # STEP 2:
        # Find currencies that are currently legal tender.
        # ---------------------------------------------------------

        # Go through every country stored in ARWA.
        for country in Country.objects.all():

            try:
                # Babel/CLDR knows which currencies are currently
                # used as tender in each territory.
                #
                # Example:
                # ZA -> ZAR
                # US -> USD
                # GB -> GBP
                territory_currencies = get_territory_currencies(
                    country.code,
                    tender=True,
                    non_tender=False,
                )

            except Exception:
                # If CLDR does not have information for a country,
                # simply continue to the next country.
                territory_currencies = []

            # Store each current currency code in our set.
            for currency_code in territory_currencies:

                active_currency_codes.add(currency_code)

                try:
                    currency = Currency.objects.get(
                        code=currency_code
                    )

                    # Connect the currency to this country.
                    country.currencies.add(currency)

                except Currency.DoesNotExist:
                    # If Babel knows about a currency that is not
                    # present in pycountry, skip it safely.
                    continue

        # ---------------------------------------------------------
        # STEP 3:
        # Mark currencies as active or inactive.
        # ---------------------------------------------------------

        # A currency is active only if CLDR identifies it as
        # current legal tender in at least one territory.
        Currency.objects.exclude(
            code__in=active_currency_codes
        ).update(
            is_active=False
        )

        Currency.objects.filter(
            code__in=active_currency_codes
        ).update(
            is_active=True
        )

        # ---------------------------------------------------------
        # STEP 4:
        # Display the result.
        # ---------------------------------------------------------

        self.stdout.write(
            self.style.SUCCESS(
                f"Currency loading completed. "
                f"Created: {created_count}, "
                f"Updated: {updated_count}, "
                f"Active currencies: {len(active_currency_codes)}."
            )
        )