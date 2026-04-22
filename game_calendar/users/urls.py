from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views


app_name = "users"

router = routers.SimpleRouter()
router.register("u", views.GameCalendarUserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    # path("", include("djoser.urls")),
    # path("u/auth/", include("djoser.urls.authtoken")),
    path('u/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('u/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
