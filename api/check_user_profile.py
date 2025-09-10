#!/usr/bin/env python3
"""
Check user profile image URL from database
"""

import os
import sys
from pathlib import Path

# Add the myproject directory to Python path
sys.path.append(str(Path(__file__).parent / 'myproject'))

# Import Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()

from app.models import User

def check_user_profile():
    """Check user profile data"""
    try:
        # Get the user with the specific Spotify ID
        user = User.objects.get(spotify_id='8x8orrbwhw8dpskzs2zgfjoum')
        
        print(f"User: {user.display_name}")
        print(f"Username: {user.username}")
        print(f"Profile Image URL: {user.profile_image_url}")
        print(f"Email: {user.email}")
        print(f"Country: {user.country}")
        print(f"Spotify ID: {user.spotify_id}")
        
        if user.profile_image_url:
            print(f"\n✅ Profile image URL found: {user.profile_image_url}")
        else:
            print("\n❌ No profile image URL found")
            
    except User.DoesNotExist:
        print("❌ User not found in database")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_user_profile() 