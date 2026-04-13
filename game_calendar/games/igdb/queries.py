from .base import fetch


def fetch_platforms(platform_ids: list):
    endpoint = "platforms/"
    query = f"""
        fields id, name;
        where id = ({",".join(map(str, platform_ids))});
        limit 500;
    """
    result = fetch(endpoint, query)

    return result



def fetch_games(platform_ids: list, offset: int = 0, cnt: bool = False):
    endpoint = "games/"
    if cnt:
        endpoint += "count/"

    # game_type: 0 - Main Game, 8 - Remake, 9 - Remaster
    # release_dates.status: 6 - Full Release, null - no info about release status
    # release_dates.release_region: 8 - Worldwide, 1 - Europe, null - not specified
    # release_dates.date should be specified or at least release_dates.date_format should be specified (TBD)
    query = f"""
        fields
            cover.image_id,
            game_type.type,
            hypes,
            name,
            release_dates.date,
            release_dates.date_format.format,
            release_dates.platform.name,
            release_dates.release_region.region,
            release_dates.status.name,
            slug;
        where
            game_type = (0, 8, 9)
            & hypes > 0
            & (release_dates.release_region = (8, 1) | release_dates.release_region = null)
            & (release_dates.date != null | release_dates.date_format.format != null)
            & (release_dates.status = 6 | release_dates.status = null)
            & release_dates.platform = ({",".join(map(str, platform_ids))});
        offset {offset};
        limit 500;
    """
    result = fetch(endpoint, query)

    return result
