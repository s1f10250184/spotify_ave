from django.db import models
from django.utils import timezone

# Create your models here.
class SpotifyUser(models.Model):
    spotify_user_id = models.CharField(max_length=64, unique=True)
    display_name = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

def __str__(self):
    return self.display_name or self.spotify_user_id

