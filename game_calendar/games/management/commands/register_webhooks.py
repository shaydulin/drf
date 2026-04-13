from django.core.management.base import BaseCommand, CommandError
import requests
from django.conf import settings

from games.igdb.base import get_token


class Command(BaseCommand):
    help = "Register webhooks for IGDB updates."

    def handle(self, *args, **options):
        endpoints = ["platforms", "games", "release_dates"]
        methods = ["create", "update", "delete"]

        headers = {
            "Client-ID": settings.IGDB_CLIENT_ID,
            "Authorization": f"Bearer {get_token()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        webhook_url = f"{settings.SITE_URL}/webhooks/igdb/"

        for endpoint in endpoints:
            url = f"https://api.igdb.com/v4/{endpoint}/webhooks/"
            for method in methods:
                data = f"url={webhook_url}&secret={settings.IGDB_WEBHOOK_SECRET}&method={method}"

                response = requests.post(url, headers=headers, data=data)
                if response.status_code != 200:
                    raise CommandError(f"Failed to register webhook for {endpoint} {method}: {response.text}")
                self.stdout.write(self.style.SUCCESS(f"Successfully registered webhook for {endpoint} {method}"))
