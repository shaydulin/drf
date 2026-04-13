import json
import logging
from pprint import pprint
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms import model_to_dict
from django.db.models import Prefetch
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, ListCreateAPIView, DestroyAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.decorators import action

from .utils import retrieve_platform_mapping
from .models import Game, Platform, WebhookEvent
from .serializers import GameSerializer
from .pagination import StandardResultsSetPagination


class GameViewset(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    serializer_class = GameSerializer
    queryset = Game.objects.all()
    lookup_field = "slug"
    pagination_class = StandardResultsSetPagination
    
    @action(detail=True, methods=["post"], url_path="add-to-my-list")
    def add_to_my_list(self, request, slug=None):
        # TODO: Implement user authentication and associate games with users
        return Response({"detail": "Success"})


@csrf_exempt
def igdb_webhook(request):
    WebhookEvent.objects.create(payload=json.loads(request.body))
    return HttpResponse(status=200)
