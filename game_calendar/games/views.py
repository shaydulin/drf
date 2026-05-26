import json
from datetime import datetime
from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.auth import get_user_model
from django.db.models import OuterRef, Subquery
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework import status

from .models import Game, GamePlatformRelease, UserGame, WebhookEvent
from .serializers import GameDetailSerializer, CalendarEntrySerializer, GameListSerializer, UserGameSerializer
from .pagination import StandardResultsSetPagination
from .filters import GameFilterBackend, UserGameFilterBackend


User = get_user_model()

class GameViewset(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    lookup_field = "slug"
    pagination_class = StandardResultsSetPagination
    filter_backends = [GameFilterBackend]

    def get_queryset(self):
        queryset = Game.objects.all().with_user_status(self.request.user)

        if self.action == "retrieve":
            queryset = queryset.prefetch_related("releases__platform")

        return queryset

    def filter_queryset(self, queryset):
        if self.action != "list":
            return queryset

        return super().filter_queryset(queryset)

    def get_serializer_class(self):
        if self.action == "list":
            return GameListSerializer
        elif self.action == "retrieve":
            return GameDetailSerializer

    @action(detail=True,
            methods=["post"],
            url_path="toggle-my-game",
            permission_classes=[IsAuthenticated])
    def toggle_my_game(self, request: Request, slug=None):
        user = request.user
        new_status = request.data.get("status", UserGame.Status.WISHLIST)
        old_status = None
        game = self.get_object()
        if UserGame.objects.filter(user=user, game=game).exists():
            user_game = UserGame.objects.get(user=user, game=game)
            old_status = user_game.status
            user_game.delete()
        if new_status == old_status:
            return Response({"detail": f"Removed from your {old_status} games"})
        else:
            UserGame.objects.get_or_create(user=user,
                                           game=game,
                                           status=new_status)
            return Response({"detail": f"Added to your {new_status} games"})


class CalendarViewset(viewsets.GenericViewSet):
    @action(methods=["get"], detail=False, url_path="releasing-this-month")
    def releasing_this_month(self, request: Request, *args, **kwargs):
        month = request.query_params.get("month", datetime.now().month)
        year = request.query_params.get("year", datetime.now().year)

        all_releases = GamePlatformRelease.objects.filter(
            date__year=year,
            date__month=month,
            date_format__title__in=["YYYYMMDD", "YYYYMM"]
        ).values("game_id", "date", "date_format__title").annotate(
            platforms=ArrayAgg("platform__title")
        ).order_by("date")

        game_ids = [r["game_id"] for r in all_releases]
        games = {game.id: game for game in Game.objects.filter(pk__in=game_ids)}

        releases = {
            "exact_date": [],
            "this_month": []
        }

        for release in all_releases:
            key = "exact_date" if release["date_format__title"] == "YYYYMMDD" else "this_month"
            releases[key].append({
                "game": games[release["game_id"]],
                "platforms": release["platforms"],
                "date": release["date"],
                "date_format": release["date_format__title"],
            })
        
        releases["exact_date"] = CalendarEntrySerializer(releases["exact_date"], many=True).data
        releases["this_month"] = CalendarEntrySerializer(releases["this_month"], many=True).data

        return Response(releases)

    @action(methods=["get"], detail=False, url_path="releasing-this-year")
    def releasing_this_year(self, request):
        year = datetime.now().year

        releases = GamePlatformRelease.objects.exclude(
            date_format__title__in=["YYYYMMDD", "YYYYMM"]
        ).filter(
            date__year=year,
        ).values(
            "game_id",
            "date",
            "date_format__title",
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
                "date_format": release["date_format__title"],
            }
            for release in releases),
            many=True,
        ).data)


class UserGameViewset(mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    serializer_class = UserGameSerializer
    filter_backends = [UserGameFilterBackend]

    def get_queryset(self):
        queryset = UserGame.objects.select_related("game")

        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                requesting_user_status=Subquery(
                    UserGame.objects.filter(
                        user=self.request.user,
                        game=OuterRef("game")
                    ).values("status")[:1]
                )
            )

        return queryset


@api_view(["POST"])
@csrf_exempt
def igdb_webhook(request):
    if request.headers.get("X-Secret") != settings.IGDB_WEBHOOK_SECRET:
        return Response(status=status.HTTP_403_FORBIDDEN)

    WebhookEvent.objects.create(
        headers={k: v for k, v in request.headers.items()},
        payload=json.loads(request.body) if request.body else None
    )
    return Response(status=status.HTTP_200_OK)
