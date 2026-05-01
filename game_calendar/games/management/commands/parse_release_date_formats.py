from django.core.management.base import BaseCommand, CommandError

from games.models import Platform, ReleaseDateFormat
from games.igdb.queries import fetch_release_date_formats


class Command(BaseCommand):
    help = "Parse release date formats from IGDB and save them to the database."

    def handle(self, *args, **options):
        date_formats = fetch_release_date_formats()
        for format in date_formats:
            ReleaseDateFormat.objects.get_or_create(
                igdb_id=format["id"],
                defaults={"title": format["format"]}
            )
        self.stdout.write(self.style.SUCCESS("Successfully parsed release date formats."))
