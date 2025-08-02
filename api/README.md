# Spotify Authentication API

This Django API provides Spotify OAuth authentication for users to login using their Spotify accounts.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the `api/` directory with the following variables:

```env
# Django Settings
SECRET_KEY=your-django-secret-key-here
DEBUG=True

# Spotify API Configuration
SPOTIFY_CLIENT_ID=your-spotify-client-id-here
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret-here
SPOTIFY_REDIRECT_URI=http://localhost:8000/api/spotify/callback
```

### 3. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Add `http://localhost:8000/api/spotify/callback` to the Redirect URIs
4. Copy the Client ID and Client Secret to your `.env` file

### 4. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Run the Server

```bash
python manage.py runserver
```

## API Endpoints

### Spotify Authentication

- `GET /api/spotify/login` - Get Spotify authorization URL
- `GET /api/spotify/callback` - Handle OAuth callback
- `GET /api/spotify/user` - Get current user information
- `POST /api/spotify/refresh` - Refresh access token
- `POST /api/spotify/logout` - Logout and clear tokens

### Usage Flow

1. **Initiate Login**: Call `GET /api/spotify/login` to get the authorization URL
2. **Redirect User**: Redirect the user to the returned authorization URL
3. **Handle Callback**: Spotify will redirect back to `/api/spotify/callback` with an authorization code
4. **User Authenticated**: The user is now logged in and can access protected endpoints

### Example Usage

```javascript
// Frontend example
fetch('/api/spotify/login')
  .then(response => response.json())
  .then(data => {
    // Redirect user to Spotify authorization
    window.location.href = data.authorization_url;
  });
```

## User Model

The custom User model includes:

- `spotify_id` - Unique Spotify user ID
- `spotify_access_token` - Current access token
- `spotify_refresh_token` - Refresh token for getting new access tokens
- `spotify_token_expires_at` - Token expiration timestamp
- `display_name` - User's Spotify display name
- `profile_image_url` - User's profile image URL
- `country` - User's country code

## Security Notes

- Never commit `.env` files to version control
- Use different credentials for development and production
- Regularly rotate your Spotify API credentials
- Implement proper session management for production use 