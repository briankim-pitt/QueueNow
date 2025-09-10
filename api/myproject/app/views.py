from django.shortcuts import redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth import login
from django.utils import timezone
from django.db import models
from datetime import timedelta, date
import requests
import base64
import json
import logging
from ninja import Router
from .models import User, FriendshipRequest, SongPost
import secrets
import hashlib
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

# Store active tokens in memory (in production, use Redis or database)
active_tokens = {}  # token -> (user_id, expires_at)

def generate_auth_token(user_id):
    """Generate a secure authentication token for the user."""
    token = secrets.token_urlsafe(32)
    expires_at = timezone.now() + timedelta(hours=24)  # 24 hour expiry
    active_tokens[token] = (user_id, expires_at)
    return token

def get_user_from_token(request):
    """Get user from auth token in request headers."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    if token not in active_tokens:
        return None
    
    user_id, expires_at = active_tokens[token]
    if timezone.now() > expires_at:
        # Token expired, remove it
        del active_tokens[token]
        return None
    
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        # User doesn't exist, remove token
        del active_tokens[token]
        return None

router = Router()

@router.get("/login")
def spotify_login(request):
    """
    Initiate Spotify OAuth login flow.
    Returns the Spotify authorization URL.
    """
    if not settings.SPOTIFY_CLIENT_ID:
        return {"error": "Spotify client ID not configured"}
    
    # Spotify OAuth scopes
    scopes = [
        'user-read-private',
        'user-read-email',
        'user-read-playback-state',
        'user-modify-playback-state',
        'user-read-currently-playing',
        'playlist-read-private',
        'playlist-read-collaborative',
        'playlist-modify-public',
        'playlist-modify-private'
    ]
    
    # Build authorization URL
    auth_url = "https://accounts.spotify.com/authorize"
    params = {
        'client_id': settings.SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
        'scope': ' '.join(scopes),
        'show_dialog': 'true'  # Force user to authorize each time
    }
    
    # Convert params to URL query string
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    authorization_url = f"{auth_url}?{query_string}"
    
    return {"authorization_url": authorization_url}

@router.get("/callback")
def spotify_callback(request, code: str = None, error: str = None):
    """
    Handle Spotify OAuth callback.
    Exchange authorization code for access token and create/update user.
    """
    if error:
        flutter_app_url = f"http://localhost:3000?error=Spotify authorization failed: {error}"
        return redirect(flutter_app_url)
    
    if not code:
        flutter_app_url = "http://localhost:3000?error=No authorization code provided"
        return redirect(flutter_app_url)
    
    # Exchange code for access token
    token_url = "https://accounts.spotify.com/api/token"
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
    }
    
    # Encode client credentials
    client_credentials = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(client_credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        token_response = requests.post(token_url, data=token_data, headers=headers)
        token_response.raise_for_status()
        token_info = token_response.json()
        
        access_token = token_info['access_token']
        refresh_token = token_info.get('refresh_token')
        expires_in = token_info.get('expires_in', 3600)
        
        # Get user profile from Spotify
        profile_url = "https://api.spotify.com/v1/me"
        profile_headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        profile_response = requests.get(profile_url, headers=profile_headers)
        profile_response.raise_for_status()
        profile_data = profile_response.json()
        
        # Create or update user
        spotify_id = profile_data['id']
        user, created = User.objects.get_or_create(
            spotify_id=spotify_id,
            defaults={
                'username': f"spotify_{spotify_id}",
                'email': profile_data.get('email', ''),
                'display_name': profile_data.get('display_name', ''),
                'profile_image_url': profile_data.get('images', [{}])[0].get('url', '') if profile_data.get('images') else '',
                'country': profile_data.get('country', ''),
                'spotify_access_token': access_token,
                'spotify_refresh_token': refresh_token,
                'spotify_token_expires_at': timezone.now() + timedelta(seconds=expires_in),
            }
        )
        
        if created:
            logger.info(f"New user created: {user.username} (Spotify ID: {spotify_id})")
        else:
            # Update existing user's tokens and profile
            logger.info(f"Existing user updated: {user.username} (Spotify ID: {spotify_id})")
            user.spotify_access_token = access_token
            if refresh_token:
                user.spotify_refresh_token = refresh_token
            user.spotify_token_expires_at = timezone.now() + timedelta(seconds=expires_in)
            user.display_name = profile_data.get('display_name', user.display_name)
            user.profile_image_url = profile_data.get('images', [{}])[0].get('url', '') if profile_data.get('images') else user.profile_image_url
            user.country = profile_data.get('country', user.country)
            user.save()
        
        # Log the user in
        login(request, user)
        
        # Generate auth token for Flutter web
        auth_token = generate_auth_token(user.id)
        
        logger.info(f"User authenticated: {user.username} (ID: {user.id})")
        logger.info(f"Generated auth token: {auth_token[:10]}...")
        
        # Return JSON response for Firebase Auth
        return {
            "success": True,
            "spotify_access_token": access_token,
            "spotify_refresh_token": refresh_token,
            "auth_token": auth_token,
            "user": {
                "id": user.id,
                "spotify_id": user.spotify_id,
                "display_name": user.display_name,
                "email": user.email,
                "profile_image_url": user.profile_image_url,
            }
        }
        
    except requests.exceptions.RequestException as e:
        flutter_app_url = f"http://localhost:3000?error=Failed to exchange code for token: {str(e)}"
        return redirect(flutter_app_url)
    except Exception as e:
        flutter_app_url = f"http://localhost:3000?error=Unexpected error: {str(e)}"
        return redirect(flutter_app_url)

@router.get("/user")
def get_user_info(request):
    """
    Get current user information using token authentication.
    """
    # Try token authentication first
    user = get_user_from_token(request)
    if user:
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "email": user.email,
                "profile_image_url": user.profile_image_url,
                "country": user.country,
                "spotify_id": user.spotify_id,
                "is_authenticated": True,
                "current_streak": getattr(user, 'current_streak', 0),
                "longest_streak": getattr(user, 'longest_streak', 0),
                "created_at": user.date_joined.isoformat(),
                "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') else user.date_joined.isoformat(),
            }
        }
    
    # Fallback to Django session authentication
    if request.user.is_authenticated:
        user = request.user
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "email": user.email,
                "profile_image_url": user.profile_image_url,
                "country": user.country,
                "spotify_id": user.spotify_id,
                "is_authenticated": True,
                "current_streak": getattr(user, 'current_streak', 0),
                "longest_streak": getattr(user, 'longest_streak', 0),
                "created_at": user.date_joined.isoformat(),
                "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') else user.date_joined.isoformat(),
            }
        }
    
    return {"error": "User not authenticated"}

@router.get("/profile")
def get_profile(request):
    """
    Get current user's profile information for profile page.
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    user = request.user
    
    # Get user's friends count
    friends_count = user.get_friends().count()
    
    # Get pending friend requests count
    pending_requests_count = user.get_pending_friend_requests().count()
    
    # Get streak information
    streak_info = user.get_streak_info()
    
    return {
        "profile": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "email": user.email,
            "profile_image_url": user.profile_image_url,
            "country": user.country,
            "spotify_id": user.spotify_id,
            "is_spotify_authenticated": user.is_spotify_authenticated,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "stats": {
                "friends_count": friends_count,
                "pending_requests_count": pending_requests_count,
                "current_streak": streak_info['current_streak'],
                "longest_streak": streak_info['longest_streak'],
            }
        }
    }

@router.get("/profile/{user_id}")
def get_user_profile(request, user_id: int):
    """
    Get another user's public profile information.
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    current_user = request.user
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User not found"}
    
    # Check if the current user is friends with the target user
    friends = current_user.get_friends()
    is_friend = friends.filter(id=user_id).exists()
    
    # Check if there's a pending friend request
    pending_request = FriendshipRequest.objects.filter(
        from_user=current_user,
        to_user=user,
        status='pending'
    ).first()
    
    reverse_pending_request = FriendshipRequest.objects.filter(
        from_user=user,
        to_user=current_user,
        status='pending'
    ).first()
    
    # Determine relationship status
    if is_friend:
        relationship_status = "friend"
    elif pending_request:
        relationship_status = "request_sent"
    elif reverse_pending_request:
        relationship_status = "request_received"
    else:
        relationship_status = "none"
    
    # Get public stats (only show friends count if they're friends)
    public_stats = {}
    if is_friend:
        public_stats["friends_count"] = user.get_friends().count()
    
    return {
        "profile": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "profile_image_url": user.profile_image_url,
            "country": user.country,
            "is_spotify_authenticated": user.is_spotify_authenticated,
            "created_at": user.created_at,
            "relationship_status": relationship_status,
            "stats": public_stats,
            # Only show email if they're friends
            "email": user.email if is_friend else None,
        }
    }

@router.post("/refresh")
def refresh_token(request):
    """
    Refresh Spotify access token using refresh token.
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    user = request.user
    
    if not user.spotify_refresh_token:
        return {"error": "No refresh token available"}
    
    token_url = "https://accounts.spotify.com/api/token"
    token_data = {
        'grant_type': 'refresh_token',
        'refresh_token': user.spotify_refresh_token,
    }
    
    # Encode client credentials
    client_credentials = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(client_credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        token_response = requests.post(token_url, data=token_data, headers=headers)
        token_response.raise_for_status()
        token_info = token_response.json()
        
        access_token = token_info['access_token']
        refresh_token = token_info.get('refresh_token', user.spotify_refresh_token)
        expires_in = token_info.get('expires_in', 3600)
        
        # Update user's tokens
        user.spotify_access_token = access_token
        user.spotify_refresh_token = refresh_token
        user.spotify_token_expires_at = timezone.now() + timedelta(seconds=expires_in)
        user.save()
        
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "is_authenticated": user.is_spotify_authenticated
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to refresh token: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@router.post("/logout")
def logout(request):
    """
    Logout user and clear Spotify tokens.
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    user = request.user
    
    # Clear Spotify tokens
    user.spotify_access_token = None
    user.spotify_refresh_token = None
    user.spotify_token_expires_at = None
    user.save()
    
    return {"success": True, "message": "Logged out successfully"}

# Friend Management Endpoints

@router.get("/friends")
def get_friends(request):
    """
    Get current user's friends list.
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    user = request.user
    friends = user.get_friends()
    
    return {
        "friends": [
            {
                "id": friend.id,
                "username": friend.username,
                "display_name": friend.display_name,
                "profile_image_url": friend.profile_image_url,
                "spotify_id": friend.spotify_id,
                "is_online": friend.is_spotify_authenticated,
            }
            for friend in friends
        ]
    }

@router.get("/friends/requests")
def get_friend_requests(request):
    """
    Get pending friend requests for current user.
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    user = request.user
    pending_requests = user.get_pending_friend_requests()
    sent_requests = user.get_sent_friend_requests()
    
    return {
        "pending_requests": [
            {
                "id": req.id,
                "from_user": {
                    "id": req.from_user.id,
                    "username": req.from_user.username,
                    "display_name": req.from_user.display_name,
                    "profile_image_url": req.from_user.profile_image_url,
                },
                "message": req.message,
                "created_at": req.created_at,
            }
            for req in pending_requests
        ],
        "sent_requests": [
            {
                "id": req.id,
                "to_user": {
                    "id": req.to_user.id,
                    "username": req.to_user.username,
                    "display_name": req.to_user.display_name,
                    "profile_image_url": req.to_user.profile_image_url,
                },
                "status": req.status,
                "message": req.message,
                "created_at": req.created_at,
            }
            for req in sent_requests
        ]
    }

@router.post("/friends/request")
def send_friend_request(request, to_user_id: int, message: str = ""):
    """
    Send a friend request to another user.
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    from_user = request.user
    
    # Check if user is trying to add themselves
    if from_user.id == to_user_id:
        return {"error": "Cannot send friend request to yourself"}
    
    # Check if target user exists
    try:
        to_user = User.objects.get(id=to_user_id)
    except User.DoesNotExist:
        return {"error": "User not found"}
    
    # Check if friend request already exists
    existing_request = FriendshipRequest.objects.filter(
        from_user=from_user,
        to_user=to_user
    ).first()
    
    if existing_request:
        if existing_request.status == 'pending':
            return {"error": "Friend request already sent"}
        elif existing_request.status == 'accepted':
            return {"error": "Already friends with this user"}
        elif existing_request.status == 'rejected':
            # Allow sending a new request if previous was rejected
            existing_request.delete()
    
    # Check if reverse request exists
    reverse_request = FriendshipRequest.objects.filter(
        from_user=to_user,
        to_user=from_user
    ).first()
    
    if reverse_request and reverse_request.status == 'pending':
        # Auto-accept if reverse request exists
        reverse_request.accept()
        logger.info(f"Auto-accepted friend request between {from_user.username} and {to_user.username}")
        return {
            "success": True,
            "message": "Friend request accepted automatically",
            "friendship_status": "accepted"
        }
    
    # Create new friend request
    friend_request = FriendshipRequest.objects.create(
        from_user=from_user,
        to_user=to_user,
        message=message
    )
    
    logger.info(f"Friend request sent from {from_user.username} to {to_user.username}")
    
    return {
        "success": True,
        "message": "Friend request sent successfully",
        "request_id": friend_request.id
    }

@router.post("/friends/accept/{request_id}")
def accept_friend_request(request, request_id: int):
    """
    Accept a friend request.
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    user = request.user
    
    try:
        friend_request = FriendshipRequest.objects.get(
            id=request_id,
            to_user=user,
            status='pending'
        )
    except FriendshipRequest.DoesNotExist:
        return {"error": "Friend request not found or already processed"}
    
    friend_request.accept()
    logger.info(f"Friend request accepted by {user.username}")
    
    return {
        "success": True,
        "message": "Friend request accepted",
        "friend": {
            "id": friend_request.from_user.id,
            "username": friend_request.from_user.username,
            "display_name": friend_request.from_user.display_name,
            "profile_image_url": friend_request.from_user.profile_image_url,
        }
    }

@router.post("/friends/reject/{request_id}")
def reject_friend_request(request, request_id: int):
    """
    Reject a friend request.
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    user = request.user
    
    try:
        friend_request = FriendshipRequest.objects.get(
            id=request_id,
            to_user=user,
            status='pending'
        )
    except FriendshipRequest.DoesNotExist:
        return {"error": "Friend request not found or already processed"}
    
    friend_request.reject()
    logger.info(f"Friend request rejected by {user.username}")
    
    return {
        "success": True,
        "message": "Friend request rejected"
    }

@router.delete("/friends/{friend_id}")
def remove_friend(request, friend_id: int):
    """
    Remove a friend (delete the friendship).
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    user = request.user
    
    # Check if they are actually friends
    friends = user.get_friends()
    if not friends.filter(id=friend_id).exists():
        return {"error": "User is not in your friends list"}
    
    # Delete all friendship requests between these users
    FriendshipRequest.objects.filter(
        models.Q(from_user=user, to_user_id=friend_id) |
        models.Q(from_user_id=friend_id, to_user=user)
    ).delete()
    
    logger.info(f"Friendship removed between {user.username} and user {friend_id}")
    
    return {
        "success": True,
        "message": "Friend removed successfully"
    }

@router.get("/users/search")
def search_users(request, query: str):
    """
    Search for users by display name or username.
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    user = request.user
    
    if len(query) < 2:
        return {"error": "Search query must be at least 2 characters"}
    
    # Search for users by display name or username
    users = User.objects.filter(
        models.Q(display_name__icontains=query) |
        models.Q(username__icontains=query)
    ).exclude(id=user.id)[:20]  # Limit to 20 results
    
    # Get current user's friends and pending requests
    friends = user.get_friends()
    pending_requests = user.get_pending_friend_requests()
    sent_requests = user.get_sent_friend_requests()
    
    results = []
    for found_user in users:
        # Determine relationship status
        if friends.filter(id=found_user.id).exists():
            status = "friend"
        elif pending_requests.filter(from_user=found_user).exists():
            status = "pending_request_received"
        elif sent_requests.filter(to_user=found_user, status='pending').exists():
            status = "pending_request_sent"
        else:
            status = "none"
        
        results.append({
            "id": found_user.id,
            "username": found_user.username,
            "display_name": found_user.display_name,
            "profile_image_url": found_user.profile_image_url,
            "relationship_status": status,
        })
    
    return {"users": results}

# Song Post Endpoints

@router.post("/song-post")
def create_song_post(request, song_name: str, artist_name: str, spotify_track_id: str = None, 
                    spotify_track_url: str = None, album_name: str = None, album_image_url: str = None):
    """
    Create a daily song post for the current user.
    Users can only post one song per day.
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    user = request.user
    today = date.today()
    
    # Check if user already posted a song today
    existing_post = SongPost.objects.filter(user=user, posted_date=today).first()
    if existing_post:
        return {"error": "You have already posted a song today"}
    
    # Create new song post
    song_post = SongPost.objects.create(
        user=user,
        song_name=song_name,
        artist_name=artist_name,
        spotify_track_id=spotify_track_id,
        spotify_track_url=spotify_track_url,
        album_name=album_name,
        album_image_url=album_image_url,
        posted_date=today
    )
    
    logger.info(f"Song post created by {user.username}: {song_name} by {artist_name}")
    
    return {
        "success": True,
        "message": "Song posted successfully",
        "song_post": {
            "id": song_post.id,
            "song_name": song_post.song_name,
            "artist_name": song_post.artist_name,
            "album_name": song_post.album_name,
            "album_image_url": song_post.album_image_url,
            "spotify_track_url": song_post.spotify_track_url,
            "posted_date": song_post.posted_date.isoformat()
        }
    }

@router.get("/song-posts")
def get_user_song_posts(request, user_id: int = None, limit: int = 10):
    """
    Get song posts for a user (defaults to current user).
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    current_user = request.user
    
    # If no user_id provided, use current user
    target_user_id = user_id if user_id else current_user.id
    
    try:
        user = User.objects.get(id=target_user_id)
    except User.DoesNotExist:
        return {"error": "User not found"}
    
    song_posts = user.song_posts.all()[:limit]
    
    return {
        "song_posts": [
            {
                "id": post.id,
                "song_name": post.song_name,
                "artist_name": post.artist_name,
                "album_name": post.album_name,
                "album_image_url": post.album_image_url,
                "spotify_track_url": post.spotify_track_url,
                "posted_date": post.posted_date.isoformat(),
                "created_at": post.created_at.isoformat()
            }
            for post in song_posts
        ]
    }

@router.get("/today-song")
def get_today_song(request):
    """
    Get current user's song post for today.
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
    user = request.user
    today = date.today()
    
    song_post = SongPost.objects.filter(user=user, posted_date=today).first()
    
    if song_post:
        return {
            "song_post": {
                "id": song_post.id,
                "song_name": song_post.song_name,
                "artist_name": song_post.artist_name,
                "album_name": song_post.album_name,
                "album_image_url": song_post.album_image_url,
                "spotify_track_url": song_post.spotify_track_url,
                "posted_date": song_post.posted_date.isoformat()
            }
        }
    else:
        return {"song_post": None}

@router.get("/track/{track_id}")
def get_track_info(request, track_id: str):
    """
    Get track information from Spotify API including album cover and audio preview.
    """
    # Try token authentication first
    user = get_user_from_token(request)
    if not user:
        # Fallback to Django session authentication
        if not request.user.is_authenticated:
            return {"error": "User not authenticated"}
        user = request.user
    
    if not user.is_spotify_authenticated:
        return {"error": "User not authenticated with Spotify"}
    
    # Check if token is expired and refresh if needed
    if user.is_token_expired():
        refresh_result = refresh_token(request)
        if "error" in refresh_result:
            return {"error": "Failed to refresh token"}
    
    # Get track information from Spotify API
    track_url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {
        'Authorization': f'Bearer {user.spotify_access_token}'
    }
    
    try:
        response = requests.get(track_url, headers=headers)
        response.raise_for_status()
        track_data = response.json()
        
        # Extract album cover URL (use the largest available)
        album_images = track_data.get('album', {}).get('images', [])
        album_image_url = None
        if album_images:
            # Get the largest image (first in the list)
            album_image_url = album_images[0].get('url')
        
        return {
            "track_id": track_data.get('id'),
            "track_name": track_data.get('name'),
            "artist_name": track_data.get('artists', [{}])[0].get('name') if track_data.get('artists') else None,
            "album_name": track_data.get('album', {}).get('name'),
            "album_image_url": album_image_url,
            "preview_url": track_data.get('preview_url'),  # 30-second audio preview
            "spotify_track_url": track_data.get('external_urls', {}).get('spotify'),
            "duration_ms": track_data.get('duration_ms'),
            "popularity": track_data.get('popularity'),
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching track info from Spotify: {e}")
        return {"error": f"Failed to fetch track information: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in get_track_info: {e}")
        return {"error": "An unexpected error occurred"}

@router.get("/search")
def search_tracks(request, query: str, limit: int = 10):
    """
    Search for tracks using Spotify API.
    """
    logger.info(f"Search request for query: {query}")
    
    # Try token authentication first
    user = get_user_from_token(request)
    access_token = None
    
    if user and user.is_spotify_authenticated:
        logger.info("User is authenticated with Spotify")
        # Check if token is expired and refresh if needed
        if user.is_token_expired():
            refresh_result = refresh_token(request)
            if "error" not in refresh_result:
                access_token = user.spotify_access_token
        else:
            access_token = user.spotify_access_token
    
    # If no user token, try to get client credentials token
    if not access_token:
        logger.info("No user token, trying client credentials")
        try:
            # Get client credentials token for public search
            from django.conf import settings
            client_id = settings.SPOTIFY_CLIENT_ID
            client_secret = settings.SPOTIFY_CLIENT_SECRET
            
            logger.info(f"Client ID: {client_id[:10]}... (length: {len(client_id) if client_id else 0})")
            logger.info(f"Client Secret: {client_secret[:10]}... (length: {len(client_secret) if client_secret else 0})")
            
            if not client_id or not client_secret:
                logger.error("Spotify credentials not found in environment variables")
                return {"error": "Spotify credentials not configured"}
            
            # Get client credentials token
            token_url = "https://accounts.spotify.com/api/token"
            token_data = {
                'grant_type': 'client_credentials'
            }
            token_headers = {
                'Authorization': f'Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            logger.info("Attempting to get client credentials token...")
            token_response = requests.post(token_url, data=token_data, headers=token_headers)
            logger.info(f"Token response status: {token_response.status_code}")
            logger.info(f"Token response text: {token_response.text}")
            
            if token_response.status_code != 200:
                logger.error(f"Token response error: {token_response.text}")
                return {"error": f"Spotify token error: {token_response.status_code}"}
            
            token_info = token_response.json()
            access_token = token_info.get('access_token')
            
            if not access_token:
                logger.error("No access token in response")
                return {"error": "Failed to get Spotify access token"}
            
            logger.info("Successfully obtained client credentials token")
                
        except Exception as e:
            logger.error(f"Error getting client credentials token: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": "Failed to authenticate with Spotify"}
    
    if not access_token:
        logger.error("No access token available")
        return {"error": "No access token available"}
    
    logger.info("Proceeding with search using access token")
    
    params = {
        'q': query,
        'type': 'track',
        'limit': limit
    }
    
    search_url = "https://api.spotify.com/v1/search"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        logger.info(f"Making search request to: {search_url}")
        response = requests.get(search_url, headers=headers, params=params)
        logger.info(f"Search response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Search response error: {response.text}")
            return {"error": f"Search failed: {response.status_code}"}
        
        response.raise_for_status()
        search_data = response.json()
        
        tracks = []
        for track in search_data.get('tracks', {}).get('items', []):
            # Get album cover URL
            album_images = track.get('album', {}).get('images', [])
            album_image_url = album_images[0].get('url') if album_images else None
            
            tracks.append({
                "track_id": track.get('id'),
                "track_name": track.get('name'),
                "artist_name": track.get('artists', [{}])[0].get('name') if track.get('artists') else None,
                "album_name": track.get('album', {}).get('name'),
                "album_image_url": album_image_url,
                "preview_url": track.get('preview_url'),  # 30-second audio preview (only with user auth)
                "spotify_track_url": track.get('external_urls', {}).get('spotify'),
                "duration_ms": track.get('duration_ms'),
                "popularity": track.get('popularity'),
            })
        
        logger.info(f"Successfully found {len(tracks)} tracks")
        return {"tracks": tracks}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching tracks on Spotify: {e}")
        return {"error": f"Failed to search tracks: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in search_tracks: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": "An unexpected error occurred"}

@router.get("/sample-tracks")
def get_sample_tracks(request):
    """
    Get sample tracks with real album covers from Spotify API.
    Note: Preview URLs require user authentication and are not available with client credentials.
    This endpoint doesn't require authentication.
    """
    # Sample tracks with real Spotify track IDs
    # Note: Preview URLs are only available with user authentication, not client credentials
    sample_tracks = [
        {
            "track_id": "4iV5W9uYEdYUVa79Axb7Rh",
            "track_name": "Blinding Lights",
            "artist_name": "The Weeknd",
            "album_name": "After Hours",
        },
        {
            "track_id": "0V3wPSX9ygBnCm8psKOegu",
            "track_name": "As It Was",
            "artist_name": "Harry Styles",
            "album_name": "Harry's House",
        },
        {
            "track_id": "5QO79kh1waicV47BqGRL3g",
            "track_name": "Bad Guy",
            "artist_name": "Billie Eilish",
            "album_name": "WHEN WE ALL FALL ASLEEP, WHERE DO WE GO?",
        },
        {
            "track_id": "3CRDbSIZ4r5MsZ0YwxuEkn",
            "track_name": "Stressed Out",
            "artist_name": "Twenty One Pilots",
            "album_name": "Blurryface",
        },
        {
            "track_id": "6rqhFgbbKwnb9MLmUQDhG6",
            "track_name": "Shape of You",
            "artist_name": "Ed Sheeran",
            "album_name": "÷ (Divide)",
        },
        {
            "track_id": "7qiZfU4dY1lWnlzDn6eLre",
            "track_name": "Uptown Funk",
            "artist_name": "Mark Ronson ft. Bruno Mars",
            "album_name": "Uptown Special",
        },
        {
            "track_id": "2LBqCSwhJGcFQeTHMVGwy3",
            "track_name": "Die For You",
            "artist_name": "The Weeknd",
            "album_name": "Starboy",
        },
        {
            "track_id": "3yfqSUWxFvZELEM4PmlwIR",
            "track_name": "Circles",
            "artist_name": "Post Malone",
            "album_name": "Hollywood's Bleeding",
        },
        {
            "track_id": "6ocbgoVGwYJhOv1GgI9NsF",
            "track_name": "Levitating",
            "artist_name": "Dua Lipa",
            "album_name": "Future Nostalgia",
        },
    ]
    
    # Get Spotify client credentials token
    try:
        token_url = "https://accounts.spotify.com/api/token"
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': settings.SPOTIFY_CLIENT_ID,
            'client_secret': settings.SPOTIFY_CLIENT_SECRET,
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_info = token_response.json()
        access_token = token_info['access_token']
        
        logger.info(f"Got Spotify access token: {access_token[:10]}...")
        
        # Fetch album covers for each track
        tracks_with_covers = []
        for track in sample_tracks:
            try:
                track_url = f"https://api.spotify.com/v1/tracks/{track['track_id']}"
                headers = {'Authorization': f'Bearer {access_token}'}
                
                track_response = requests.get(track_url, headers=headers)
                track_response.raise_for_status()
                track_data = track_response.json()
                
                # Get the highest quality album image
                album_images = track_data.get('album', {}).get('images', [])
                album_image_url = album_images[0]['url'] if album_images else None
                
                # Note: Preview URLs require user authentication and are not available with client credentials
                # For demo purposes, we'll set a placeholder that indicates this limitation
                preview_url = None  # Would be track_data.get('preview_url') with user auth
                
                logger.info(f"Track {track['track_name']}: preview_url = {preview_url}")
                
                tracks_with_covers.append({
                    "track_id": track['track_id'],
                    "track_name": track['track_name'],
                    "artist_name": track['artist_name'],
                    "album_name": track['album_name'],
                    "album_image_url": album_image_url,
                    "preview_url": preview_url,  # Will be null with client credentials
                    "spotify_track_url": f"https://open.spotify.com/track/{track['track_id']}",
                })
                
            except Exception as e:
                logger.error(f"Error fetching album cover for {track['track_name']}: {e}")
                # Fallback to track without cover
                tracks_with_covers.append({
                    "track_id": track['track_id'],
                    "track_name": track['track_name'],
                    "artist_name": track['artist_name'],
                    "album_name": track['album_name'],
                    "album_image_url": None,
                    "preview_url": None,
                    "spotify_track_url": f"https://open.spotify.com/track/{track['track_id']}",
                })
        
        return {"tracks": tracks_with_covers}
        
    except Exception as e:
        logger.error(f"Error getting Spotify token: {e}")
        # Return tracks without covers if Spotify API fails
        return {"tracks": sample_tracks}

@router.get("/health")
def health_check(request):
    """
    Simple health check endpoint to verify the API is running.
    """
    return {
        "status": "healthy",
        "message": "Spotify API is running",
        "spotify_configured": bool(settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET)
    }

