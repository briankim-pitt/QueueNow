from ninja import NinjaAPI
import dotenv
from app.views import router as spotify_router

dotenv.load_dotenv()

api = NinjaAPI()

# Include Spotify authentication routes
api.add_router("/spotify/", spotify_router)   

