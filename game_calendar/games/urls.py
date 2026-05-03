from django.urls import path, include
from rest_framework import routers

from . import views


app_name = "games"

router = routers.SimpleRouter()
router.register("games", views.GameViewset, basename="game")
router.register("games-calendar", views.CalendarViewset, basename="calendar")
router.register("user-games", views.UserGameViewset, basename="user-games")

urlpatterns = [
    path("", include(router.urls)),
    # path("calendar/", views.CalendarView.as_view(), name="calendar"),

    path("webhooks/igdb/", views.igdb_webhook, name="igdb_webhook"),
]
