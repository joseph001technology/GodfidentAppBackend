import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.bible.models import (
    BibleBook,
    BibleTranslation,
    BibleVerse,
)


class Command(BaseCommand):
    help = "Import KJV Bible verses from JSON files located in apps/bible/data/Bible-kjv-master/"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting Bible verse import..."))

        # ------------------------------------------------------------------
        # Ensure translation exists
        # ------------------------------------------------------------------
        try:
            translation = BibleTranslation.objects.get(code="KJV")
        except BibleTranslation.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "KJV translation not found.\n"
                    "Run: python manage.py load_bible_books"
                )
            )
            return

        # ------------------------------------------------------------------
        # Locate data folder (Updated to point to your actual repository layout)
        # ------------------------------------------------------------------
        bible_app_dir = Path(__file__).resolve().parent.parent.parent
        data_dir = bible_app_dir / "data" / "Bible-kjv-master"

        if not data_dir.exists():
            self.stdout.write(
                self.style.ERROR(
                    f"Bible data directory not found:\n{data_dir}\n"
                    "Expected location: apps/bible/data/Bible-kjv-master/"
                )
            )
            return

        json_files = sorted(data_dir.glob("*.json"))

        if not json_files:
            self.stdout.write(
                self.style.WARNING(
                    f"No JSON files found in {data_dir}"
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {len(json_files)} Bible book files."
            )
        )

        # ------------------------------------------------------------------
        # Statistics
        # ------------------------------------------------------------------
        total_books = 0
        total_verses = 0
        skipped_books = 0
        skipped_chapters = 0
        skipped_verses = 0

        # ------------------------------------------------------------------
        # Process each file
        # ------------------------------------------------------------------
        for file_path in json_files:

            self.stdout.write(f"\nProcessing {file_path.name}")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

            except json.JSONDecodeError as e:
                skipped_books += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Invalid JSON in {file_path.name}: {e}"
                    )
                )
                continue

            except Exception as e:
                skipped_books += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed reading {file_path.name}: {e}"
                    )
                )
                continue

            # --------------------------------------------------------------
            # Support multiple JSON structures
            # --------------------------------------------------------------
            if isinstance(data, dict):
                book_name = data.get("book", file_path.stem)
                chapters = data.get("chapters", [])

            elif isinstance(data, list):
                book_name = file_path.stem
                chapters = data

            else:
                skipped_books += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Unknown JSON structure in {file_path.name}"
                    )
                )
                continue

            cleaned_name = book_name.replace("_", " ").strip()

            # --------------------------------------------------------------
            # Match book in database
            # --------------------------------------------------------------
            book = (
                BibleBook.objects
                .filter(name__iexact=cleaned_name)
                .first()
            )

            if not book:
                book = (
                    BibleBook.objects
                    .filter(abbreviation__iexact=file_path.stem)
                    .first()
                )

            if not book:
                skipped_books += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"No matching BibleBook found for "
                        f"'{cleaned_name}'"
                    )
                )
                continue

            verse_objects = []

            # --------------------------------------------------------------
            # Parse chapters
            # --------------------------------------------------------------
            for chapter_entry in chapters:

                try:
                    chapter_num = int(
                        chapter_entry.get("chapter")
                    )

                except (
                    ValueError,
                    TypeError,
                    AttributeError,
                ) as e:

                    skipped_chapters += 1

                    self.stdout.write(
                        self.style.WARNING(
                            f"[{book.name}] "
                            f"Skipped invalid chapter: {e}"
                        )
                    )

                    continue

                verses = chapter_entry.get("verses", [])

                # ----------------------------------------------------------
                # Parse verses
                # ----------------------------------------------------------
                for verse_entry in verses:

                    try:
                        verse_num = int(
                            verse_entry.get("verse")
                        )

                    except (
                        ValueError,
                        TypeError,
                        AttributeError,
                    ) as e:

                        skipped_verses += 1

                        self.stdout.write(
                            self.style.WARNING(
                                f"[{book.name} {chapter_num}] "
                                f"Skipped invalid verse: {e}"
                            )
                        )

                        continue

                    verse_text = (
                        verse_entry.get("text", "")
                        .strip()
                    )

                    if not verse_text:
                        skipped_verses += 1

                        self.stdout.write(
                            self.style.WARNING(
                                f"[{book.name} "
                                f"{chapter_num}:{verse_num}] "
                                f"Empty verse text skipped."
                            )
                        )

                        continue

                    verse_objects.append(
                        BibleVerse(
                            translation=translation,
                            book=book,
                            chapter=chapter_num,
                            verse=verse_num,
                            text=verse_text,
                        )
                    )

            if not verse_objects:
                self.stdout.write(
                    self.style.WARNING(
                        f"No verses found in {file_path.name}"
                    )
                )
                continue

            # --------------------------------------------------------------
            # Replace existing verses
            # --------------------------------------------------------------
            existing_count = (
                BibleVerse.objects.filter(
                    translation=translation,
                    book=book,
                ).count()
            )

            self.stdout.write(
                f"Replacing {existing_count:,} existing verses "
                f"for {book.name}"
            )

            with transaction.atomic():

                BibleVerse.objects.filter(
                    translation=translation,
                    book=book,
                ).delete()

                BibleVerse.objects.bulk_create(
                    verse_objects,
                    batch_size=1000,
                )

            imported_count = len(verse_objects)

            total_books += 1
            total_verses += imported_count

            self.stdout.write(
                self.style.SUCCESS(
                    f"Imported {imported_count:,} verses "
                    f"for {book.name}"
                )
            )

        # ------------------------------------------------------------------
        # Final Summary
        # ------------------------------------------------------------------
        self.stdout.write("")
        self.stdout.write("=" * 60)

        self.stdout.write(
            self.style.SUCCESS(
                "\nIMPORT COMPLETE\n"
                f"Books Imported   : {total_books}\n"
                f"Verses Imported  : {total_verses:,}\n"
                f"Skipped Books    : {skipped_books}\n"
                f"Skipped Chapters : {skipped_chapters}\n"
                f"Skipped Verses   : {skipped_verses}\n"
            )
        )

        self.stdout.write("=" * 60)