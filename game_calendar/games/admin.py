from django.contrib import admin

from .models import Game, GamePlatformRelease, Platform

# Register your models here.
admin.site.site_header = "Game Calendar Admin"
admin.site.site_title = "Game Calendar Admin Portal"
admin.site.index_title = "Welcome to Game Calendar Admin Portal"


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)
    # list_filter = ("platforms", "release_date")


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)


@admin.register(GamePlatformRelease)
class GamePlatformReleaseAdmin(admin.ModelAdmin):
    list_display = ("game", "platform", "date", "date_format")
    search_fields = ("game__title", "platform__title")
