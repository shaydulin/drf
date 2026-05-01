from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views


app_name = "users"

router = routers.SimpleRouter()
router.register("users", views.GameCalendarUserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    # path("", include("djoser.urls")),
    # path("u/auth/", include("djoser.urls.authtoken")),
    path('users/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
