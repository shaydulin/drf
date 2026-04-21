from django.urls import path, include
from rest_framework import routers

from . import views


app_name = "games"

router = routers.SimpleRouter()
router.register("", views.GameViewset, basename="game")
router.register("release-calendar", views.GamePlatformReleaseViewset)

urlpatterns = [
    path("", include(router.urls)),

    path("webhooks/igdb/", views.igdb_webhook, name="igdb_webhook"),
]
