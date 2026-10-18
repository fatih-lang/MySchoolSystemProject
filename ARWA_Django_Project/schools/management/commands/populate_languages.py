import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from schools.models import Language


class Command(BaseCommand):
    """
    Import the official ISO 639-3 language catalogue
    into the ARWA Language table.
    """

    help = "Populate the Language table from ISO 639-3 data."

    def handle(self, *args, **options):

        # Find the root directory of the Django project.
        base_dir = Path(__file__).resolve().parents[3]

        # Build the path to the ISO 639-3 data file.
        language_file = (
            base_dir
            / "schools"
            / "data"
            / "iso-639-3.tab"
        )

        # Make sure the language file exists.
        if not language_file.exists():
            self.stdout.write(
                self.style.ERROR(
                    f"Language file not found: {language_file}"
                )
            )
            return

        # Read the ISO 639-3 file.
        languages = []

        with language_file.open(
            "r",
            encoding="utf-8",
            newline=""
        ) as file:

            reader = csv.DictReader(
                file,
                delimiter="\t"
            )

            for row in reader:

                # ISO 639-3 three-letter code.
                code = row["Id"].strip()

                # Official language name.
                name = row["Ref_Name"].strip()

                # Ignore incomplete records.
                if not code or not name:
                    continue

                languages.append(
                    Language(
                        code=code,
                        name=name,
                        is_active=True,
                    )
                )

        self.stdout.write(
            f"ISO 639-3 records found: {len(languages)}"
        )

        # Get all language codes already stored in ARWA.
        existing_codes = set(
            Language.objects.values_list(
                "code",
                flat=True
            )
        )

        # Only prepare languages that do not already exist.
        new_languages = [
            language
            for language in languages
            if language.code not in existing_codes
        ]

        self.stdout.write(
            f"New languages to import: {len(new_languages)}"
        )

        # Insert new languages in batches.
        if new_languages:

            Language.objects.bulk_create(
                new_languages,
                batch_size=500,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Language catalogue imported successfully."
            )
        )

        self.stdout.write(
            f"Languages created: {len(new_languages)}"
        )