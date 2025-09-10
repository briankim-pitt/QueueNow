# QueueNow - Daily Music Sharing App

QueueNow is a social music sharing application that allows users to post one song per day and discover music through their friends' daily posts. The app integrates with Spotify for authentication and music discovery.

## Tech Stack

### Frontend (Flutter)
- **Framework**: Flutter 3.8.1+ with Dart
- **Platforms**: Web, iOS, Android, macOS, Windows, Linux
- **Key Dependencies**:
  - `http`: API communication
  - `url_launcher`: External URL handling
  - `shared_preferences`: Local data storage
  - `audioplayers`: Audio preview playback
  - `firebase_core` & `firebase_auth`: Authentication
  - `google_sign_in`: Google authentication

### Backend (Django)
- **Framework**: Django 5.2 with Django Ninja for API
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Custom user model with Spotify OAuth
- **Key Dependencies**:
  - `django-ninja`: Modern API framework
  - `requests`: Spotify API integration
  - `python-dotenv`: Environment variable management
  - `django-cors-headers`: CORS handling
  - `psycopg2-binary`: PostgreSQL adapter
  - `gunicorn`: Production WSGI server

### External Services
- **Spotify Web API**: Music search, track information, and user authentication
- **Firebase**: Additional authentication services
- **AWS**: Production deployment (Elastic Beanstalk, RDS)

## Getting Started

### Prerequisites
- Flutter SDK 3.8.1+
- Python 3.8+
- Spotify Developer Account
- Git

### Backend Setup

1. **Clone and Navigate**
   ```bash
   git clone <repository-url>
   cd project/api
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create `.env` file in `api/` directory:
   ```env
   SECRET_KEY=your-django-secret-key
   DEBUG=True
   SPOTIFY_CLIENT_ID=your-spotify-client-id
   SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
   SPOTIFY_REDIRECT_URI=http://localhost:8000/api/spotify/callback
   ```

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Run Server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Navigate to Frontend**
   ```bash
   cd ../frontend
   ```

2. **Install Dependencies**
   ```bash
   flutter pub get
   ```

3. **Run App**
   ```bash
   # For web
   flutter run -d chrome
   
   # For mobile
   flutter run
   ```


## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.


