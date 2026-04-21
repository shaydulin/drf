from django.shortcuts import render
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import viewsets, permissions


User = get_user_model()

class GameCalendarUserViewSet(UserViewSet):
    pass
    # def get_permissions(self):
    #     return [permissions.AllowAny()]

    # def get_queryset(self):
    #     return User.objects.all()
