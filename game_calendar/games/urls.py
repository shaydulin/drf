from django.urls import path, include
from rest_framework import routers

from . import views


app_name = "games"

router = routers.DefaultRouter()
router.register("games", views.GameViewset)
router.register("release-calendar", views.GamePlatformReleaseViewset)

urlpatterns = [
    path("api/v1/", include(router.urls)),

    path("webhooks/igdb/", views.igdb_webhook, name="igdb_webhook"),
]
