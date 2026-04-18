from rest_framework import serializers
from .models import Game, GamePlatformRelease


class GameSerializer(serializers.HyperlinkedModelSerializer):
    cover_small = serializers.SerializerMethodField()
    cover_big = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ("title", "url", "cover_small", "cover_big")
        read_only_fields = "slug",
        extra_kwargs = {
            "igdb_id": {"write_only": True},
            "url": {"view_name": "games:game-detail", "lookup_field": "slug"},
        }

    def get_cover_small(self, obj):
        return obj.get_cover_url("cover_small")

    def get_cover_big(self, obj):
        return obj.get_cover_url("cover_big")


    # queryset = GamePlatformRelease.objects.values(
    #     "game_id",
    #     "date",
    #     "date_format",
    # ).annotate(
    #     platforms=ArrayAgg("platform__title"),
    # ).order_by("date")
class ReleaseCalendarSerializer(serializers.Serializer):
    game_id = serializers.IntegerField()
    date = serializers.DateField()
    date_format = serializers.CharField()
    platforms = serializers.ListField(child=serializers.CharField())
    # class Meta:
    #     model = GamePlatformRelease
    #     fields = "__all__"
