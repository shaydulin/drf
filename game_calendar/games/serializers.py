from rest_framework import serializers
from .models import Game, GamePlatformRelease, UserGame


class ReleaseListingField(serializers.RelatedField):
    def to_representation(self, value: GamePlatformRelease):
        return {
            "platform": value.platform.title,
            "date": value.get_formatted_release_date(),
        }


class GameDetailSerializer(serializers.ModelSerializer):
    cover_big = serializers.SerializerMethodField()
    releases = ReleaseListingField(many=True, read_only=True)

    class Meta:
        model = Game
        fields = ("title", "summary", "cover_big", "releases")

    def get_cover_big(self, obj: Game):
        return obj.get_cover_url("cover_big")


class GameListSerializer(serializers.ModelSerializer):
    cover_small = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True, default=None)

    class Meta:
        model = Game
        fields = ("title", "url", "cover_small", "status")

    def get_cover_small(self, obj):
        return obj.get_cover_url("cover_small")

    def get_url(self, obj):
        return obj.get_absolute_url()


class CalendarEntrySerializer(serializers.Serializer):
    game = GameListSerializer()
    date = serializers.SerializerMethodField()
    platforms = serializers.ListField(child=serializers.CharField())

    def get_date(self, obj):
        return GamePlatformRelease.get_formatted_date(obj["date_format"], obj["date"])


class UserGameSerializer(serializers.ModelSerializer):
    game = GameListSerializer()
    requested_user_game_status = serializers.CharField(source="status", read_only=True)

    class Meta:
        model = UserGame
        fields = ("game", "requested_user_game_status")

    def to_representation(self, instance):
        instance.game.status = getattr(instance, "requesting_user_status", None)
        return super().to_representation(instance)
