from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth import login
from django.utils import timezone
from datetime import timedelta
import requests
import base64
import json
from ninja import Router
from .models import User

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
        return {"error": f"Spotify authorization failed: {error}"}
    
    if not code:
        return {"error": "No authorization code provided"}
    
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
        
        if not created:
            # Update existing user's tokens and profile
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
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "email": user.email,
                "profile_image_url": user.profile_image_url,
                "country": user.country,
                "spotify_id": user.spotify_id,
                "is_authenticated": user.is_spotify_authenticated
            }
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to exchange code for token: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@router.get("/user")
def get_user_info(request):
    """
    Get current user information.
    """
    if not request.user.is_authenticated:
        return {"error": "User not authenticated"}
    
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
            "is_authenticated": user.is_spotify_authenticated,
            "created_at": user.created_at,
            "updated_at": user.updated_at
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

