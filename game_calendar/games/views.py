import json
import logging
from pprint import pprint
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms import model_to_dict
from django.db.models import Prefetch
from django.db.models.functions import TruncWeek
from django.contrib.postgres.aggregates import ArrayAgg
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, ListCreateAPIView, DestroyAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.decorators import action

from .utils import retrieve_platform_mapping
from .models import Game, GamePlatformRelease, WebhookEvent
from .serializers import GameSerializer, ReleaseCalendarSerializer
from .pagination import StandardResultsSetPagination


class GameViewset(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    serializer_class = GameSerializer
    queryset = Game.objects.annotate(week=TruncWeek("releases__date"))
    lookup_field = "slug"
    pagination_class = StandardResultsSetPagination
    
    @action(detail=True, methods=["post"], url_path="add-to-my-list")
    def add_to_my_list(self, request, slug=None):
        # TODO: Implement user authentication and associate games with users
        return Response({"detail": "Success"})


class GamePlatformReleaseViewset(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = ReleaseCalendarSerializer
    queryset = GamePlatformRelease.objects.filter(year=2026).values(
        "game_id",
        "date",
        "date_format",
    ).annotate(
        platforms=ArrayAgg("platform__title"),
    ).order_by("date")
    pagination_class = StandardResultsSetPagination


@csrf_exempt
def igdb_webhook(request):
    WebhookEvent.objects.create(payload=json.loads(request.body))
    return HttpResponse(status=200)
