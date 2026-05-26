from itertools import count

from django.core.management.base import BaseCommand, CommandError

from games.utils import (
    retrieve_platform_mapping,
    retrieve_date_format_mapping,
    save_game_and_releases
)
from games.models import Game
from games.igdb.queries import fetch_games


class Command(BaseCommand):
    help = "Parse games from IGDB and save them to the database."

    def handle(self, *args, **options):
        platform_mapping = retrieve_platform_mapping()
        date_format_mapping = retrieve_date_format_mapping()

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
                        f"Game with IGDB ID {game_data['id']} already exists. "
                        f"Total games written so far: {games_written}. "
                        "Stopping parsing to avoid duplicates."
                    ))
                    interrupt = True
                    break

                game = save_game_and_releases(game_data, platform_mapping, date_format_mapping)
                if not game:
                    skipped_games.append([game_data["id"], game_data["name"]])
                    games_skipped += 1
                    continue

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
