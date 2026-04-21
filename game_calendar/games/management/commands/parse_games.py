from collections import defaultdict
from datetime import datetime, timezone
from itertools import count
from math import inf

from django.core.management.base import BaseCommand, CommandError

from games.utils import retrieve_platform_mapping
from games.models import Game, GamePlatformRelease
from games.igdb.queries import fetch_games


class Command(BaseCommand):
    help = "Parse games from IGDB and save them to the database."

    def handle(self, *args, **options):
        platform_mapping = retrieve_platform_mapping()

        total_games = fetch_games(list(platform_mapping), cnt=True).get("count", 0)
        self.stdout.write(self.style.NOTICE(f"Total games to parse: {total_games}"))

        games_parsed = 0
        games_skipped = 0
        games_written = 0
        interrupt = False
        for offset in count(0, 500):
            data = fetch_games(list(platform_mapping), offset)
            if not data:
                break
            games_parsed += len(data)

            skipped_games = []
            for game_data in data:
                if Game.objects.filter(igdb_id=game_data["id"]).exists():
                    self.stdout.write(self.style.WARNING(
                        f"Game with IGDB ID {game_data['id']} already exists."
                        f"Total games written so far: {games_written}."
                        "Stopping parsing to avoid duplicates."
                    ))
                    interrupt = True
                    break

                releases_by_platform = defaultdict(dict)
                # Needed fields:
                # - release_dates.platform (platform ID)
                # - release_dates.date
                # - release_dates.date_format.format
                # Release regions by priority: Worldwide (8) > Europe (1) > Rest of the World
                # Needed release date statuses: Full Release (6) or no info about release status (null)
                for release in game_data.get("release_dates", []):
                    if release["platform"]["id"] not in platform_mapping:
                        continue

                    if "status" in release and release["status"]["id"] != 6:
                        continue

                    date = release.get("date")
                    date_format = release.get("date_format", {}).get("format")
                    if date is None and date_format is None:
                        continue

                    region = release.get("release_region", {}).get("id")
                    if region is not None and region not in (8, 1):
                        continue

                    releases_by_platform[release["platform"]["id"]][region] = [date, date_format, release["id"]]

                if not releases_by_platform:
                    skipped_games.append([game_data["id"], game_data["name"]])
                    games_skipped += 1
                    continue
                for platform in releases_by_platform:
                    if 8 in releases_by_platform[platform]:
                        releases_by_platform[platform] = releases_by_platform[platform].pop(8)
                    elif 1 in releases_by_platform[platform]:
                        releases_by_platform[platform] = releases_by_platform[platform].pop(1)
                    else:
                        releases_by_platform[platform] = releases_by_platform[platform].pop(next(iter(releases_by_platform[platform])))

                game = Game.objects.create(
                    igdb_id=game_data["id"],
                    title=game_data["name"],
                    slug=game_data["slug"],
                    summary=game_data.get("summary"),
                    hypes=game_data.get("hypes"),
                    cover_image_id=game_data["cover"]["image_id"] if "cover" in game_data else None,
                )

                game_platform_releases = []
                for platform, (date, date_format, igdb_id) in releases_by_platform.items():
                    date_obj = datetime.fromtimestamp(date, timezone.utc).date() if date is not None else None
                    year = date_obj.year if date_obj and "YYYY" in date_format else None
                    month = date_obj.month if date_obj and "MM" in date_format else None
                    day = date_obj.day if date_obj and "DD" in date_format else None
                    game_platform_releases.append(GamePlatformRelease(
                        igdb_id=igdb_id,
                        game=game,
                        platform_id=platform_mapping[platform],
                        date=date_obj,
                        year=year,
                        month=month,
                        day=day,
                        date_format=date_format,
                    ))
                GamePlatformRelease.objects.bulk_create(game_platform_releases)
                games_written += 1

            if interrupt:
                break

            self.stdout.write(self.style.NOTICE(f"Written {games_written} games of {games_parsed} parsed so far. Skipped {games_skipped} games."))
            if skipped_games:
                print("Skipped games:")
                for igdb_id, name in skipped_games:
                    print(igdb_id, name)

        if not interrupt:
            self.stdout.write(self.style.SUCCESS(
                f"Finished parsing. Total games parsed: {games_parsed}, "
                f"skipped: {games_skipped}, written: {games_written}."
            ))
            if games_written + games_skipped < total_games:
                self.stdout.write(self.style.WARNING(
                    f"Processed {games_written + games_skipped} games, but expected {total_games}. "
                    "There might be some missing data or an error in the parsing process."
                ))
            elif games_written + games_skipped > total_games:
                self.stdout.write(self.style.WARNING(
                    f"Processed {games_written + games_skipped} games, but expected {total_games}. "
                    "There might be some duplicates or an error in the parsing process."
                ))
            else:
                self.stdout.write(self.style.SUCCESS("Successfully parsed and processed all games."))
