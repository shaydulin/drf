import json
import requests
from igdb.wrapper import IGDBWrapper
from django.core.cache import cache
from django.conf import settings


URL = "https://id.twitch.tv/oauth2/token"


def get_token():
    access_token = cache.get("access_token")
    # TODO: fix this, token can be cached but
    # expired if it was re-requested in other place
    if access_token is not None:
        return access_token

    response: requests.Response = requests.post(
        URL,
        data={
            "client_id": settings.IGDB_CLIENT_ID, 
            "client_secret": settings.IGDB_CLIENT_SECRET,
            "grant_type": "client_credentials",
        }
    )
    token_data = response.json()
    access_token = token_data["access_token"]
    expires_in = token_data["expires_in"]

    cache.set("access_token", access_token, expires_in - 3600)

    return access_token


def fetch(endpoint, query):
    auth_token = get_token()
    wrapper = IGDBWrapper(settings.IGDB_CLIENT_ID, auth_token)

    byte_array = wrapper.api_request(
        endpoint,
        query,
    )
    return json.loads(byte_array.decode("utf-8"))
