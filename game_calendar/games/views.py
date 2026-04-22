from datetime import datetime
import json
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms import model_to_dict
from django.db.models import Prefetch
from django.db.models.functions import TruncWeek
from django.contrib.postgres.aggregates import ArrayAgg
from rest_framework import filters
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, ListCreateAPIView, DestroyAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.decorators import action

from .utils import retrieve_platform_mapping
from .models import Game, GamePlatformRelease, WebhookEvent
from .serializers import GameDetailSerializer, CalendarEntrySerializer
from .pagination import StandardResultsSetPagination
from .filters import GameSearchFilter


class GameViewset(mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    serializer_class = GameDetailSerializer
    queryset = Game.objects.all()
    lookup_field = "slug"
    # pagination_class = StandardResultsSetPagination
    filter_backends = [GameSearchFilter]

    def list(self, request, *args, **kwargs):
        month = request.query_params.get("month", datetime.now().month)
        year = request.query_params.get("year", datetime.now().year)

        all_releases = GamePlatformRelease.objects.filter(
            date__year=year,
            date__month=month,
            date_format__in=[
                GamePlatformRelease.Format.YYYYMMDD,
                GamePlatformRelease.Format.YYYYMM
            ]
        ).values("game_id", "date", "date_format").annotate(
            platforms=ArrayAgg("platform__title")
        ).order_by("date")

        game_ids = [r["game_id"] for r in all_releases]
        games = {game.id: game for game in Game.objects.filter(pk__in=game_ids)}

        releases = {
            "exact_date": [],
            "this_month": []
        }
        
        for release in all_releases:
            key = "exact_date" if release["date_format"] == GamePlatformRelease.Format.YYYYMMDD else "this_month"
            releases[key].append({
                "game": games[release["game_id"]],
                "platforms": release["platforms"],
                "date": release["date"],
                "date_format": release["date_format"],
            })
        
        releases["exact_date"] = CalendarEntrySerializer(releases["exact_date"], many=True).data
        releases["this_month"] = CalendarEntrySerializer(releases["this_month"], many=True).data

        return Response(releases)
    
    @action(methods=["get"], detail=False, url_path="releasing-this-year")
    def releasing_this_year(self, request):
        year = datetime.now().year

        releases = GamePlatformRelease.objects.exclude(
            date_format__in=[
                GamePlatformRelease.Format.YYYYMMDD,
                GamePlatformRelease.Format.YYYYMM,
            ]
        ).filter(
            date__year=year,
        ).values(
            "game_id",
            "date",
            "date_format",
        ).annotate(
            platforms=ArrayAgg("platform__title"),
        ).order_by("date")

        game_ids = [release["game_id"] for release in releases]
        games = {game.id: game for game in Game.objects.filter(pk__in=game_ids)}

        return Response(CalendarEntrySerializer(
            ({
                "game": (games[release["game_id"]]),
                "platforms": release["platforms"],
                "date": release["date"],
                "date_format": release["date_format"],
            }
            for release in releases),
            many=True,
        ).data)

    @action(detail=True, methods=["post"], url_path="add-to-my-games")
    def add_to_my_list(self, request, slug=None):
        # TODO: Implement user authentication and associate games with users
        return Response({"detail": "Success"})


@csrf_exempt
def igdb_webhook(request):
    WebhookEvent.objects.create(payload=json.loads(request.body))
    return HttpResponse(status=200)
