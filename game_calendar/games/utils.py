from .models import Platform, ReleaseDateFormat, Game, GamePlatformRelease
from collections import defaultdict
from datetime import datetime, timezone


def retrieve_platform_mapping():
    platform_mapping = dict(
        Platform.objects.values_list("igdb_id", "id")
    )

    return platform_mapping


def retrieve_date_format_mapping():
    date_format_mapping = dict(
        ReleaseDateFormat.objects.values_list("igdb_id", "id")
    )

    return date_format_mapping


def save_game_and_releases(game_data, platform_mapping, date_format_mapping):
    releases_by_platform = defaultdict(dict)
    # Needed fields:
    # - release_dates.platform (platform ID)
    # - release_dates.date
    # - release_dates.date_format (date format ID)
    # Release regions by priority: Worldwide (8) > Europe (1) > Rest of the World
    # Needed release date statuses: Full Release (6) or no info about release status (null)
    for release in game_data.get("release_dates", []):
        if release["platform"]["id"] not in platform_mapping:
            continue

        if "status" in release and release["status"]["id"] != 6:
            continue

        date = release.get("date")
        date_format_igdb_id = release.get("date_format", {}).get("id")
        date_format_title = release.get("date_format", {}).get("format")
        if date is None and date_format_igdb_id is None:
            continue
        elif date_format_igdb_id is not None:
            date_format_id = date_format_mapping.get(date_format_igdb_id)

        region = release.get("release_region", {}).get("id")
        if region is not None and region not in (8, 1):
            continue

        releases_by_platform[release["platform"]["id"]][region] = [date, date_format_id, date_format_title, release["id"]]

    if not releases_by_platform:
        return None

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
    for platform, (date, date_format_id, date_format_title, igdb_id) in releases_by_platform.items():
        date_obj = datetime.fromtimestamp(date, timezone.utc).date() if date is not None else None
        year = date_obj.year if date_obj and "YYYY" in date_format_title else None
        month = date_obj.month if date_obj and "MM" in date_format_title else None
        day = date_obj.day if date_obj and "DD" in date_format_title else None
        game_platform_releases.append(GamePlatformRelease(
            igdb_id=igdb_id,
            game=game,
            platform_id=platform_mapping[platform],
            date=date_obj,
            year=year,
            month=month,
            day=day,
            date_format_id=date_format_id,
        ))
    GamePlatformRelease.objects.bulk_create(game_platform_releases)
    return game
