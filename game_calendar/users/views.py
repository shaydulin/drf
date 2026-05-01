from django.contrib.auth import get_user_model
from djoser.views import UserViewSet


User = get_user_model()

class GameCalendarUserViewSet(UserViewSet):
    # check if username != "me"
    pass
    # def get_permissions(self):
    #     return [permissions.AllowAny()]

    # def get_queryset(self):
    #     return User.objects.all()
