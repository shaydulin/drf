from django.core.management.base import BaseCommand, CommandError

from games.models import Platform
from games.igdb.queries import fetch_platforms


class Command(BaseCommand):
    help = "Parse platforms from IGDB and save them to the database."

    def handle(self, *args, **options):
        # These platform IDs correspond to the platforms we are interested in:
        # 6 - PC (Microsoft Windows)
        # 48 - PlayStation 4
        # 49 - Xbox One
        # 130 - Nintendo Switch
        # 167 - PlayStation 5
        # 169 - Xbox Series X|S
        # 508 - Nintendo Switch 2
        platform_ids = [6, 48, 49, 130, 167, 169, 508]

        platforms = fetch_platforms(platform_ids)
        for platform in platforms:
            Platform.objects.get_or_create(
                igdb_id=platform["id"],
                defaults={"title": platform["name"]}
            )
        self.stdout.write(self.style.SUCCESS("Successfully parsed platforms."))
