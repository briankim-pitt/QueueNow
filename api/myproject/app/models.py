from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import date

class User(AbstractUser):
    spotify_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    spotify_access_token = models.TextField(null=True, blank=True)
    spotify_refresh_token = models.TextField(null=True, blank=True)
    spotify_token_expires_at = models.DateTimeField(null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    profile_image_url = models.URLField(max_length=500, null=True, blank=True)
    country = models.CharField(max_length=10, null=True, blank=True)
    current_streak = models.PositiveIntegerField(default=0, help_text="Current consecutive days of posting")
    longest_streak = models.PositiveIntegerField(default=0, help_text="Longest streak ever achieved")
    last_post_date = models.DateField(null=True, blank=True, help_text="Date of the last song post")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_spotify_authenticated(self):
        """Check if user has valid Spotify authentication."""
        if not self.spotify_access_token:
            return False
    
        if self.spotify_token_expires_at and self.spotify_token_expires_at <= timezone.now():
            return False
        
        return True


    def get_friends(self):
        """Get all friends of this user"""
        # Get accepted friendships where this user is either the from_user or to_user
        friendships = FriendshipRequest.objects.filter(
            models.Q(from_user=self) | models.Q(to_user=self),
            status='accepted'
        )
        
        friends = []
        for friendship in friendships:
            if friendship.from_user == self:
                friends.append(friendship.to_user)
            else:
                friends.append(friendship.from_user)
        
        return friends

    def get_pending_requests(self):
        """Get pending friend requests sent to this user"""
        return FriendshipRequest.objects.filter(to_user=self, status='pending')

    def get_sent_requests(self):
        """Get friend requests sent by this user that are still pending"""
        return FriendshipRequest.objects.filter(from_user=self, status='pending')

    def update_streak(self, post_date):
        """Update user's streak when they post a song"""
        if self.last_post_date is None:
            # First post ever
            self.current_streak = 1
            self.longest_streak = 1
            self.last_post_date = post_date
        else:
            # Check if this is a consecutive day
            days_difference = (post_date - self.last_post_date).days
            
            if days_difference == 1:
                # Consecutive day - increment streak
                self.current_streak += 1
                self.longest_streak = max(self.longest_streak, self.current_streak)
            elif days_difference == 0:
                # Same day - don't change streak (shouldn't happen due to unique constraint)
                pass
            else:
                # Gap in posting - reset streak
                self.current_streak = 1
            
            self.last_post_date = post_date
        
        self.save()

    def get_streak_info(self):
        """Get current streak information"""
        return {
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'last_post_date': self.last_post_date,
        }

class FriendshipRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')

class SongPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='song_posts')
    song_name = models.CharField(max_length=255)
    artist_name = models.CharField(max_length=255)
    spotify_track_id = models.CharField(max_length=255, null=True, blank=True)
    spotify_track_url = models.URLField(max_length=500, null=True, blank=True)
    album_name = models.CharField(max_length=255, null=True, blank=True)
    album_image_url = models.URLField(max_length=500, null=True, blank=True)
    posted_date = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'posted_date')  # One song per user per day
        ordering = ['-posted_date', '-created_at']
    
    def __str__(self):
        return f"{self.user.display_name or self.user.username} - {self.song_name} by {self.artist_name} ({self.posted_date})"

    def save(self, *args, **kwargs):
        """Override save to update user streak"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Update user's streak when a new song is posted
            self.user.update_streak(self.posted_date)
