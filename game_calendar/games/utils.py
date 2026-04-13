from .models import Platform


def retrieve_platform_mapping():
    platform_mapping = dict(
        Platform.objects.values_list("igdb_id", "id")
    )

    return platform_mapping
