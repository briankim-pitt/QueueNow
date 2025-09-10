# Spotify Authentication Test App

A simple Flutter app to test the Spotify authentication API endpoints.

## Features

- Test API connection
- Initiate Spotify OAuth login
- Get user information
- Logout functionality
- Real-time status updates
- User data display

## Setup

### 1. Install Dependencies

```bash
cd frontend
flutter pub get
```

### 2. Start the Django API Server

Make sure your Django API server is running:

```bash
cd ../api/myproject
python3 manage.py runserver
```

### 3. Configure Spotify Credentials

Ensure your `.env` file in the `api/` directory has the correct Spotify credentials:

```env
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/api/spotify/callback
```

### 4. Run the Flutter App

```bash
cd frontend
flutter run
```

## Usage

### 1. Test API Connection

Click the "Test API Connection" button to verify that the Flutter app can communicate with your Django API server.

### 2. Login with Spotify

1. Click the "Login with Spotify" button
2. The app will open your browser with the Spotify authorization page
3. Log in with your Spotify account and authorize the app
4. You'll be redirected back to the callback URL
5. The user will be created/updated in the database

### 3. Get User Info

After successful login, click "Get User Info" to retrieve the current user's information from the API.

### 4. Logout

Click "Logout" to clear the user's authentication tokens.

## API Endpoints Tested

- `GET /api/add` - Test basic API functionality
- `GET /api/spotify/login` - Get Spotify authorization URL
- `GET /api/spotify/user` - Get current user information
- `POST /api/spotify/logout` - Logout user

## Troubleshooting

### Connection Issues

- Make sure the Django server is running on `http://127.0.0.1:8000`
- Check that the API Base URL in the app matches your server
- Verify that your Spotify app settings include the correct redirect URI

### Authentication Issues

- Ensure your Spotify app credentials are correct in the `.env` file
- Check that the redirect URI in Spotify Developer Dashboard matches exactly
- Make sure you're using `127.0.0.1` instead of `localhost`

### Flutter Issues

- Run `flutter doctor` to check for any Flutter setup issues
- Make sure all dependencies are installed with `flutter pub get`

## Development

The app is built with:
- Flutter 3.8+
- HTTP package for API calls
- URL Launcher for opening external URLs
- Material Design 3 for UI

## Notes

- This is a test app for development purposes
- The app opens Spotify authorization in an external browser
- User sessions are managed by the Django backend
- The app displays real-time status updates for all operations
