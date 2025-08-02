from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    """Custom user model for Spotify authentication."""
    
    # Spotify-specific fields
    spotify_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    spotify_access_token = models.TextField(null=True, blank=True)
    spotify_refresh_token = models.TextField(null=True, blank=True)
    spotify_token_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Profile information from Spotify
    display_name = models.CharField(max_length=255, null=True, blank=True)
    profile_image_url = models.URLField(max_length=500, null=True, blank=True)
    country = models.CharField(max_length=2, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.display_name or self.username
    
    @property
    def is_spotify_authenticated(self):
        """Check if user has valid Spotify authentication."""
        if not self.spotify_access_token:
            return False
        
        if self.spotify_token_expires_at and self.spotify_token_expires_at <= timezone.now():
            return False
            
        return True
