from django.db import models
from django.urls import reverse
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.auth import get_user_model


User = get_user_model()

class IGDBIdMixin(models.Model):
    igdb_id = models.IntegerField(unique=True)

    class Meta:
        abstract = True


class GameQuerySet(models.QuerySet):
    def with_user_status(self, user):
        if not user.is_authenticated:
            return self
        user_games = user.game_links.filter(game=models.OuterRef("pk"))
        self = self.annotate(status=models.Subquery(user_games.values("status")[:1]))
        return self


class Game(IGDBIdMixin):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)
    summary = models.TextField(null=True, blank=True)
    hypes = models.IntegerField(default=0)
    cover_image_id = models.CharField(max_length=250, null=True, blank=True)
    search_vector = SearchVectorField(null=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    platforms = models.ManyToManyField(
        "Platform",
        through="GamePlatformRelease",
        related_name="games",
        blank=True
    )
    users = models.ManyToManyField(
        User,
        through="UserGame",
        related_name="games",
        blank=True
    )

    objects = GameQuerySet.as_manager()

    class Meta:
        indexes = [
            GinIndex(fields=['search_vector']),
        ]

    def __str__(self):
        return self.title

    def get_cover_url(self, size="cover_small"):
        return f"https://images.igdb.com/igdb/image/upload/t_{size}/{self.cover_image_id}.png"
    
    def get_absolute_url(self):
        return reverse("games:game-detail", kwargs={"slug": self.slug})


class Platform(IGDBIdMixin):
    title = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ReleaseDateFormat(IGDBIdMixin):
    title = models.CharField(max_length=50)

    def __str__(self):
        return self.title


class GamePlatformRelease(IGDBIdMixin):
    class Meta:
        verbose_name = "Game release"
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(fields=['game', 'platform'], name='unique_game_platform')
        ]

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="releases"
    )
    platform = models.ForeignKey(
        Platform,
        on_delete=models.CASCADE,
        related_name="releases"
    )
    date = models.DateField(blank=True, null=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    month = models.PositiveSmallIntegerField(null=True, blank=True)
    day = models.PositiveSmallIntegerField(null=True, blank=True)
    date_format = models.ForeignKey(ReleaseDateFormat,
                                    on_delete=models.SET_NULL,
                                    null=True,
                                    blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_formatted_release_date(self):
        return self.get_formatted_date(
            self.date_format.title if self.date_format else None,
            self.date
        )
        
    @staticmethod
    def get_formatted_date(format_title, date):
        if not date or not format_title:
            return "TBD"

        if format_title == "YYYYMMDD":
            return date.strftime("%Y-%m-%d")
        elif format_title == "YYYYMM":
            return date.strftime("%Y-%m")
        elif format_title == "YYYY":
            return date.strftime("%Y")
        elif format_title in ["YYYYQ1", "YYYYQ2", "YYYYQ3", "YYYYQ4"]:
            quarter = format_title[-1]
            return f"{date.year}-Q{quarter}"
        else:
            return "TBD"

    def __str__(self):
        return f"{self.game.title} on {self.platform.title} @ {self.date}"


class UserGame(models.Model):
    class Status(models.TextChoices):
        WISHLIST = "wishlist"
        PLAYING = "playing"
        COMPLETED = "completed"
        DROPPED = "dropped"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="game_links")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="user_links")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WISHLIST)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'game'], name='unique_user_game')
        ]


class WebhookEvent(models.Model):
    headers = models.JSONField(null=True, blank=True)
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
