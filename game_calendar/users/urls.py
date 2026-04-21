from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views


app_name = "users"

router = routers.SimpleRouter()
router.register("", views.GameCalendarUserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    # path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
