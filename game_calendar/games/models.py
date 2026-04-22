from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ImproperlyConfigured
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


class IGDBIdMixin(models.Model):
    igdb_id = models.IntegerField(unique=True)

    class Meta:
        abstract = True


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


class GamePlatformRelease(IGDBIdMixin):
    class Format(models.TextChoices):
        YYYYMMDD = "YYYYMMDD", "Exact date"
        YYYYMM = "YYYYMM", "Year and month"
        YYYY = "YYYY", "Year"
        YYYYQ1 = "YYYYQ1", "Year and quarter 1"
        YYYYQ2 = "YYYYQ2", "Year and quarter 2"
        YYYYQ3 = "YYYYQ3", "Year and quarter 3"
        YYYYQ4 = "YYYYQ4", "Year and quarter 4"
        TBD = "TBD", "To be determined"

    class Meta:
        verbose_name = "Game release"
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
    date_format = models.CharField(max_length=10,
                                   choices=Format.choices,
                                   null=True,
                                   blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_formatted_date(self):
        if not self.date:
            return None
        
        if self.date_format == self.Format.YYYYMMDD:
            return self.date.strftime("%Y-%m-%d")
        elif self.date_format == self.Format.YYYYMM:
            return self.date.strftime("%Y-%m")
        elif self.date_format == self.Format.YYYY:
            return self.date.strftime("%Y")
        elif self.date_format in [self.Format.YYYYQ1, self.Format.YYYYQ2, 
                                   self.Format.YYYYQ3, self.Format.YYYYQ4]:
            quarter = self.date_format[-1]
            return f"{self.date.year}-Q{quarter}"
        elif self.date_format == self.Format.TBD:
            return "TBD"
        
        return None

    def __str__(self):
        return f"{self.game.title} on {self.platform.title} @ {self.date}"


class WebhookEvent(models.Model):
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
