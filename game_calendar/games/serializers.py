from rest_framework import serializers
from .models import Game, GamePlatformRelease


class ReleaseListingField(serializers.RelatedField):
    def to_representation(self, value: GamePlatformRelease):
        return {
            "platform": value.platform.title,
            "date": value.get_formatted_date(),
        }


class GameDetailSerializer(serializers.ModelSerializer):
    cover_big = serializers.SerializerMethodField()
    releases = ReleaseListingField(many=True, read_only=True)

    class Meta:
        model = Game
        fields = ("title", "summary", "cover_big", "releases")

    def get_cover_big(self, obj):
        return obj.get_cover_url("cover_big")


class GameListSerializer(serializers.ModelSerializer):
    cover_small = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = ("title", "url", "cover_small")

    def get_cover_small(self, obj):
        return obj.get_cover_url("cover_small")

    def get_url(self, obj):
        return obj.get_absolute_url()


class CalendarEntrySerializer(serializers.Serializer):
    game = GameListSerializer()
    date = serializers.DateField()
    platforms = serializers.ListField(child=serializers.CharField())
