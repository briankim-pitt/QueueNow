#!/usr/bin/env python3
"""
Test script to verify user creation and database saving
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
from django.utils import timezone

def test_user_creation():
    """Test user creation and database operations"""
    print("🧪 Testing User Creation and Database Operations")
    print("=" * 50)
    
    # Check if we can access the User model
    print("1. Testing User model access...")
    try:
        user_count = User.objects.count()
        print(f"✅ User model accessible. Current user count: {user_count}")
    except Exception as e:
        print(f"❌ Error accessing User model: {e}")
        return
    
    # Test creating a sample user
    print("\n2. Testing user creation...")
    try:
        test_user, created = User.objects.get_or_create(
            spotify_id="test_spotify_id_123",
            defaults={
                'username': 'test_user_123',
                'email': 'test@example.com',
                'display_name': 'Test User',
                'spotify_access_token': 'test_token',
                'spotify_refresh_token': 'test_refresh_token',
                'spotify_token_expires_at': timezone.now(),
            }
        )
        
        if created:
            print(f"✅ Test user created successfully!")
            print(f"   User ID: {test_user.id}")
            print(f"   Username: {test_user.username}")
            print(f"   Spotify ID: {test_user.spotify_id}")
        else:
            print(f"✅ Test user already exists!")
            print(f"   User ID: {test_user.id}")
            print(f"   Username: {test_user.username}")
        
        # Test updating user
        print("\n3. Testing user update...")
        old_name = test_user.display_name
        test_user.display_name = "Updated Test User"
        test_user.save()
        print(f"✅ User updated successfully!")
        print(f"   Old name: {old_name}")
        print(f"   New name: {test_user.display_name}")
        
        # Test user properties
        print("\n4. Testing user properties...")
        print(f"   Is authenticated: {test_user.is_spotify_authenticated}")
        print(f"   Created at: {test_user.created_at}")
        print(f"   Updated at: {test_user.updated_at}")
        
        # Clean up test user
        print("\n5. Cleaning up test user...")
        test_user.delete()
        print("✅ Test user deleted successfully!")
        
    except Exception as e:
        print(f"❌ Error during user creation test: {e}")
        return
    
    # Show final user count
    final_count = User.objects.count()
    print(f"\n📊 Final user count: {final_count}")
    
    print("\n" + "=" * 50)
    print("🎉 User creation and database tests completed!")
    print("\n📝 The Spotify authentication flow will:")
    print("1. Create a new user when someone logs in for the first time")
    print("2. Update existing user's tokens and profile on subsequent logins")
    print("3. Save all user data to the database")
    print("4. Log the user in automatically")

if __name__ == "__main__":
    test_user_creation() 