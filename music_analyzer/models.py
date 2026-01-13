from django.db import models
from django.utils import timezone


class SpotifyUser(models.Model):
    spotify_user_id = models.CharField(max_length=64, unique=True)
    access_token = models.CharField(max_length=255, blank=True, default="")
    refresh_token = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.spotify_user_id


class TopTrackSnapshot(models.Model):
    user = models.ForeignKey(SpotifyUser, on_delete=models.CASCADE)
    term = models.CharField(max_length=16)          
    limit = models.IntegerField(default=20)
    fetched_at = models.DateTimeField(default=timezone.now)
    data = models.JSONField(default=dict)

    class Meta:
        ordering = ["-fetched_at"] 


