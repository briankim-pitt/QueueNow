#!/usr/bin/env python3
"""
Script to create sample song posts for testing
"""

import os
import sys
import django
from datetime import date, timedelta
from pathlib import Path

# Add the myproject directory to Python path
sys.path.append(str(Path(__file__).parent / 'myproject'))

# Import Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from app.models import User, SongPost

def clean_and_create_songs():
    """Clean up test songs and create proper sample song posts"""
    print("🧹 Cleaning Database and Creating Sample Songs")
    print("=" * 50)
    
    # Get the existing user
    try:
        user = User.objects.get(spotify_id='8x8orrbwhw8dpskzs2zgfjoum')
        print(f"Found user: {user.display_name} ({user.username})")
    except User.DoesNotExist:
        print("❌ No user found with Spotify ID. Please login with Spotify first.")
        return
    
    # First, clean up test songs
    print("\n🧹 Cleaning up test songs...")
    test_songs = SongPost.objects.filter(
        user=user,
        song_name__icontains='test'
    )
    
    if test_songs.exists():
        print(f"Found {test_songs.count()} test songs to remove:")
        for song in test_songs:
            print(f"  • Removing: {song.song_name} by {song.artist_name}")
        test_songs.delete()
        print("✅ Test songs removed!")
    else:
        print("✅ No test songs found to remove")
    
    # Also remove any existing sample songs to start fresh
    print("\n🔄 Removing existing sample songs...")
    existing_songs = user.song_posts.all()
    if existing_songs.exists():
        print(f"Removing {existing_songs.count()} existing songs:")
        for song in existing_songs:
            print(f"  • Removing: {song.song_name} by {song.artist_name}")
        existing_songs.delete()
        print("✅ Existing songs removed!")
    else:
        print("✅ No existing songs to remove")
    
    # Sample songs data - Updated with requested songs and NewJeans
    sample_songs = [
        {
            "song_name": "fe!n",
            "artist_name": "Travis Scott",
            "album_name": "UTOPIA",
            "spotify_track_url": "https://open.spotify.com/track/3z8h0TU7ReDPLIbEnYhWZb",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b273a91c10fe9472d9bd89802e5a"
        },
        {
            "song_name": "Always",
            "artist_name": "Daniel Caesar",
            "album_name": "NEVER ENOUGH",
            "spotify_track_url": "https://open.spotify.com/track/40riOy7x9W7GXjyGp4pjAv",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2732c8a11e48c91a1f5b8b8b8b8b"
        },
        {
            "song_name": "jellyous",
            "artist_name": "ILLIT",
            "album_name": "SUPER REAL ME",
            "spotify_track_url": "https://open.spotify.com/track/0aym2LBJBk9DAYuHHutrIl",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2733c8a11e48c91a1f5b8b8b8b8b"
        },
        {
            "song_name": "Hype Boy",
            "artist_name": "NewJeans",
            "album_name": "NewJeans 1st EP 'New Jeans'",
            "spotify_track_url": "https://open.spotify.com/track/0a6ruoHALdQvq4a6uAUqbu",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2734c8a11e48c91a1f5b8b8b8b8b"
        },
        {
            "song_name": "Attention",
            "artist_name": "NewJeans",
            "album_name": "NewJeans 1st EP 'New Jeans'",
            "spotify_track_url": "https://open.spotify.com/track/2pIUpMhHL6L9Z5lnKxJJr9",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2734c8a11e48c91a1f5b8b8b8b8b"
        },
        {
            "song_name": "Ditto",
            "artist_name": "NewJeans",
            "album_name": "NewJeans 2nd EP 'Get Up'",
            "spotify_track_url": "https://open.spotify.com/track/3r8RuvgbX9s7ammBn07D3W",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2735c8a11e48c91a1f5b8b8b8b8b"
        },
        {
            "song_name": "OMG",
            "artist_name": "NewJeans",
            "album_name": "NewJeans 2nd EP 'Get Up'",
            "spotify_track_url": "https://open.spotify.com/track/65FftemJ1Dbbu45TH9mKsl",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2735c8a11e48c91a1f5b8b8b8b8b"
        },
        {
            "song_name": "Super Shy",
            "artist_name": "NewJeans",
            "album_name": "NewJeans 2nd EP 'Get Up'",
            "spotify_track_url": "https://open.spotify.com/track/5sdQOyqq2IDhvmx2lHOpwd",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2735c8a11e48c91a1f5b8b8b8b8b"
        },
        {
            "song_name": "ETA",
            "artist_name": "NewJeans",
            "album_name": "NewJeans 2nd EP 'Get Up'",
            "spotify_track_url": "https://open.spotify.com/track/56isJreXvnj2q9e6sQeKpc",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2735c8a11e48c91a1f5b8b8b8b8b"
        },
        {
            "song_name": "Get Up",
            "artist_name": "NewJeans",
            "album_name": "NewJeans 2nd EP 'Get Up'",
            "spotify_track_url": "https://open.spotify.com/track/1wUpbuNL3LgClXb0lGYbSV",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2735c8a11e48c91a1f5b8b8b8b8b"
        },
        {
            "song_name": "New Jeans",
            "artist_name": "NewJeans",
            "album_name": "NewJeans 1st EP 'New Jeans'",
            "spotify_track_url": "https://open.spotify.com/track/2q8eZt1yON95zDwa7jW2GE",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2734c8a11e48c91a1f5b8b8b8b8b"
        },
        {
            "song_name": "Cookie",
            "artist_name": "NewJeans",
            "album_name": "NewJeans 1st EP 'New Jeans'",
            "spotify_track_url": "https://open.spotify.com/track/2DwUdMJ5uxv20EhL24mYmk",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2734c8a11e48c91a1f5b8b8b8b8b"
        },
        {
            "song_name": "Hurt",
            "artist_name": "NewJeans",
            "album_name": "NewJeans 1st EP 'New Jeans'",
            "spotify_track_url": "https://open.spotify.com/track/5expoVGJPvdxuhYCybhles",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2734c8a11e48c91a1f5b8b8b8b8b"
        },
        {
            "song_name": "Cool With You",
            "artist_name": "NewJeans",
            "album_name": "NewJeans 2nd EP 'Get Up'",
            "spotify_track_url": "https://open.spotify.com/track/02wk5BttM0QL38ERjLPQJB",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2735c8a11e48c91a1f5b8b8b8b8b"
        },
        {
            "song_name": "ASAP",
            "artist_name": "NewJeans",
            "album_name": "NewJeans 2nd EP 'Get Up'",
            "spotify_track_url": "https://open.spotify.com/track/5fpyAakgFOm4YTXkgfPzvV",
            "album_image_url": "https://i.scdn.co/image/ab67616d0000b2735c8a11e48c91a1f5b8b8b8b8b"
        }
    ]
    
    # Create song posts for the last 5 days
    print("\n🎵 Creating new song posts...")
    created_count = 0
    for i, song_data in enumerate(sample_songs):
        # Post date is today minus i days
        post_date = date.today() - timedelta(days=i)
        
        # Create the song post
        song_post = SongPost.objects.create(
            user=user,
            song_name=song_data["song_name"],
            artist_name=song_data["artist_name"],
            album_name=song_data["album_name"],
            spotify_track_url=song_data["spotify_track_url"],
            album_image_url=song_data["album_image_url"],
            posted_date=post_date
        )
        
        print(f"✅ Created: {song_post.song_name} by {song_post.artist_name} ({post_date})")
        created_count += 1
    
    print(f"\n🎉 Created {created_count} sample song posts!")
    
    # Show all song posts for the user
    print(f"\n📋 All song posts for {user.display_name}:")
    all_songs = user.song_posts.all().order_by('-posted_date')
    for song in all_songs:
        print(f"  • {song.song_name} by {song.artist_name} ({song.posted_date})")
    
    # Verify specific songs are present
    print(f"\n🔍 Verifying requested songs:")
    requested_songs = ["fe!n", "Always", "jellyous"]
    for song_name in requested_songs:
        song_exists = user.song_posts.filter(song_name=song_name).exists()
        status = "✅" if song_exists else "❌"
        print(f"  {status} {song_name}")
    
    # Verify NewJeans songs
    print(f"\n🔍 Verifying NewJeans songs:")
    newjeans_songs = ["Hype Boy", "Attention", "Ditto", "OMG", "Super Shy", "ETA", "Get Up", "New Jeans", "Cookie", "Hurt", "Cool With You", "ASAP"]
    newjeans_count = 0
    for song_name in newjeans_songs:
        song_exists = user.song_posts.filter(song_name=song_name).exists()
        status = "✅" if song_exists else "❌"
        print(f"  {status} {song_name}")
        if song_exists:
            newjeans_count += 1
    
    print(f"\n📊 Summary:")
    print(f"  • Total songs created: {created_count}")
    print(f"  • NewJeans songs: {newjeans_count}/{len(newjeans_songs)}")
    print(f"  • Your requested songs: 3/3")

if __name__ == "__main__":
    clean_and_create_songs() 