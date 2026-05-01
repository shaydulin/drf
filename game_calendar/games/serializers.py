from rest_framework import serializers
from .models import Game, GamePlatformRelease, UserGame


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
    date = serializers.DateField() # fix this to be a string with formatted date
    platforms = serializers.ListField(child=serializers.CharField())


class UserGameSerializer(serializers.ModelSerializer):
    game = GameListSerializer(read_only=True)
    game_slug = serializers.CharField(write_only=True)

    class Meta:
        model = UserGame
        fields = ['game', 'game_slug', 'status', 'added_at']
        read_only_fields = ['added_at']

    def create(self, validated_data):
        game_slug = validated_data.pop('game_slug')
        game = Game.objects.get(slug=game_slug)
        validated_data['game'] = game
        return super().create(validated_data)
