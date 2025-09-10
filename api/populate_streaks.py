#!/usr/bin/env python3
"""
Populate streak data for existing users based on their song posts
"""

import os
import sys
from pathlib import Path
from datetime import date, timedelta

# Add the myproject directory to Python path
sys.path.append(str(Path(__file__).parent / 'myproject'))

# Import Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()

from app.models import User, SongPost

def populate_streaks():
    """Populate streak data for all users based on their song posts"""
    print("🔥 Populating streak data for all users...")
    
    users = User.objects.all()
    
    for user in users:
        print(f"\nProcessing user: {user.display_name or user.username}")
        
        # Get all song posts for this user, ordered by date
        song_posts = user.song_posts.all().order_by('posted_date')
        
        if not song_posts.exists():
            print(f"  No song posts found for {user.display_name}")
            continue
        
        current_streak = 0
        longest_streak = 0
        last_post_date = None
        
        # Calculate streaks
        for i, post in enumerate(song_posts):
            if i == 0:
                # First post
                current_streak = 1
                longest_streak = 1
                last_post_date = post.posted_date
            else:
                # Check if this is a consecutive day
                days_difference = (post.posted_date - last_post_date).days
                
                if days_difference == 1:
                    # Consecutive day - increment streak
                    current_streak += 1
                    longest_streak = max(longest_streak, current_streak)
                elif days_difference == 0:
                    # Same day - don't change streak
                    pass
                else:
                    # Gap in posting - reset streak
                    current_streak = 1
                
                last_post_date = post.posted_date
        
        # Update user's streak data
        user.current_streak = current_streak
        user.longest_streak = longest_streak
        user.last_post_date = last_post_date
        user.save()
        
        print(f"  Current streak: {current_streak}")
        print(f"  Longest streak: {longest_streak}")
        print(f"  Last post date: {last_post_date}")
    
    print("\n✅ Streak data populated successfully!")

if __name__ == "__main__":
    populate_streaks() 