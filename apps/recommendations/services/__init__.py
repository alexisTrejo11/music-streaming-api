"""
Main service module that aggregates all recommendation services.

For backward compatibility, this module imports and re-exports all services.
New code should import directly from specific service modules.
"""

from .taste_profile_service import TasteProfileService
from .recommendation_service import RecommendationService
from .radio_service import RadioService
from .mood_service import MoodService
from .trending_service import TrendingService

# Re-export for backward compatibility
update_taste_profile = TasteProfileService.update_taste_profile
update_taste_profile_manual = TasteProfileService.update_taste_profile_manual
get_audio_preferences = TasteProfileService.get_audio_preferences
get_personalized_recommendations = (
    RecommendationService.get_personalized_recommendations
)
get_similar_songs = RecommendationService.get_similar_songs
generate_discover_weekly = RecommendationService.generate_discover_weekly
create_radio = RadioService.create_radio
delete_radio = RadioService.delete_radio
generate_radio_songs = RadioService.generate_radio_songs
get_songs_by_mood = MoodService.get_songs_by_mood
get_recommended_artists = TrendingService.get_recommended_artists
get_recommended_albums = TrendingService.get_recommended_albums
get_trending_for_you = TrendingService.get_trending_for_you

__all__ = [
    "TasteProfileService",
    "RecommendationService",
    "RadioService",
    "MoodService",
    "TrendingService",
    "update_taste_profile",
    "update_taste_profile_manual",
    "get_audio_preferences",
    "get_personalized_recommendations",
    "get_similar_songs",
    "generate_discover_weekly",
    "create_radio",
    "delete_radio",
    "generate_radio_songs",
    "get_songs_by_mood",
    "get_recommended_artists",
    "get_recommended_albums",
    "get_trending_for_you",
]
