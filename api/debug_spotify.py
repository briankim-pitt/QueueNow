#!/usr/bin/env python3
"""
Debug script to check Spotify configuration
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

from django.conf import settings

def debug_spotify_config():
    """Debug Spotify configuration"""
    print("🔍 Spotify Configuration Debug")
    print("=" * 40)
    
    # Check environment variables
    print("Environment Variables:")
    print(f"SPOTIFY_CLIENT_ID: {'✅ Set' if os.getenv('SPOTIFY_CLIENT_ID') else '❌ Not set'}")
    print(f"SPOTIFY_CLIENT_SECRET: {'✅ Set' if os.getenv('SPOTIFY_CLIENT_SECRET') else '❌ Not set'}")
    print(f"SPOTIFY_REDIRECT_URI: {'✅ Set' if os.getenv('SPOTIFY_REDIRECT_URI') else '❌ Not set'}")
    
    print("\nDjango Settings:")
    print(f"SPOTIFY_CLIENT_ID: {'✅ Set' if settings.SPOTIFY_CLIENT_ID else '❌ Not set'}")
    print(f"SPOTIFY_CLIENT_SECRET: {'✅ Set' if settings.SPOTIFY_CLIENT_SECRET else '❌ Not set'}")
    print(f"SPOTIFY_REDIRECT_URI: {settings.SPOTIFY_REDIRECT_URI}")
    
    print("\n🔧 To Fix INVALID_CLIENT Error:")
    print("1. Go to https://developer.spotify.com/dashboard")
    print("2. Select your app")
    print("3. Click 'Edit Settings'")
    print("4. In 'Redirect URIs', add exactly:")
    print(f"   {settings.SPOTIFY_REDIRECT_URI}")
    print("5. Click 'Save'")
    
    print("\n📝 Your .env file should contain:")
    print("SPOTIFY_CLIENT_ID=your-actual-client-id")
    print("SPOTIFY_CLIENT_SECRET=your-actual-client-secret")
    print(f"SPOTIFY_REDIRECT_URI={settings.SPOTIFY_REDIRECT_URI}")
    
    print("\n⚠️  Important Notes:")
    print("- Use 127.0.0.1, NOT localhost")
    print("- The redirect URI must match EXACTLY")
    print("- No trailing slashes unless specified")
    print("- Case sensitive")

if __name__ == "__main__":
    debug_spotify_config() 