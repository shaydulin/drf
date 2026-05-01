from datetime import datetime
import json
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms import model_to_dict
from django.db.models import Prefetch
from django.db.models.functions import TruncWeek
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.auth import get_user_model
from rest_framework import filters
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, ListCreateAPIView, DestroyAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.filters import OrderingFilter
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from .utils import retrieve_platform_mapping
from .models import Game, GamePlatformRelease, UserGame, WebhookEvent
from .serializers import GameDetailSerializer, CalendarEntrySerializer, GameListSerializer, UserGameSerializer
from .pagination import StandardResultsSetPagination
from .filters import GameFilterBackend


User = get_user_model()

class GameViewset(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = Game.objects.all()
    lookup_field = "slug"
    pagination_class = StandardResultsSetPagination
    filter_backends = [GameFilterBackend]

    # TODO: annotate games with user-specific data (e.g. is_in_wishlist) if user is authenticated

    def filter_queryset(self, queryset):
        if self.action != "list":
            return queryset

        return super().filter_queryset(queryset)

    def get_serializer_class(self):
        if self.action == "list":
            return GameListSerializer
        return GameDetailSerializer

    @action(detail=True,
            methods=["post"],
            url_path="toggle-my-game",
            permission_classes=[IsAuthenticated])
    def toggle_my_game(self, request, slug=None):
        user = request.user
        new_status = request.data.get("status", UserGame.Status.WISHLIST)
        old_status = None
        game = self.get_object()
        if UserGame.objects.filter(user=user, game=game).exists():
            user_game = UserGame.objects.get(user=user, game=game)
            old_status = user_game.status
            user_game.delete()
        if new_status == old_status:
            return Response({"detail": "Removed from your games"})
        else:
            UserGame.objects.get_or_create(user=user,
                                           game=game,
                                           status=new_status)
            return Response({"detail": "Added to your games"})

    # @action(detail=False,
    #         methods=["get"],
    #         url_path=r"user/(?P<username>[\w.@+-]+)")
    # def get_user_games(self, request, username):
    #     user = get_object_or_404(User, username=username)
    #     user_games = user.games.all()
    #     return Response(GameListSerializer(user_games, many=True).data)


class CalendarViewset(viewsets.GenericViewSet):
    @action(methods=["get"], detail=False, url_path="releasing-this-month")
    def releasing_this_month(self, request: Request, *args, **kwargs):
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


# class UserGameViewset(mixins.ListModelMixin,
#                       mixins.CreateModelMixin,
#                       mixins.DestroyModelMixin,
#                       viewsets.GenericViewSet):
#     serializer_class = UserGameSerializer
#     permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
#     filter_backends = [OrderingFilter, DjangoFilterBackend]
#     filterset_class = UserGameFilterSet
#     ordering_fields = ['added_at', 'game__title']

#     def get_queryset(self):
#         from pprint import pprint
#         pprint(self.__class__.__mro__)
#         return UserGame.objects.select_related('game')

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

#     def get_permissions(self):
#         return super().get_permissions()
    
#     def check_permissions(self, request):
#         return super().check_permissions(request)

#     def get_queryset(self):
#         pass


@csrf_exempt
def igdb_webhook(request):
    WebhookEvent.objects.create(payload=json.loads(request.body))
    return HttpResponse(status=200)
