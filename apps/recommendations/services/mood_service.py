from django.db.models import Q
from typing import List

from apps.music.models import Song


class MoodService:
    """Service for mood-based recommendations"""

    @staticmethod
    def get_songs_by_mood(mood: str, limit: int = 30) -> List[Song]:
        """
        Get songs matching a specific mood
        """
        mood = mood.lower()

        # Map moods to audio features
        mood_profiles = {
            "happy": {"valence": (0.6, 1.0), "energy": (0.5, 1.0)},
            "sad": {"valence": (0.0, 0.4), "energy": (0.0, 0.5)},
            "energetic": {"energy": (0.7, 1.0), "danceability": (0.6, 1.0)},
            "chill": {"energy": (0.0, 0.4), "valence": (0.4, 0.7)},
            "party": {"danceability": (0.7, 1.0), "energy": (0.6, 1.0)},
            "focus": {"energy": (0.3, 0.6), "valence": (0.4, 0.7)},
        }

        profile = mood_profiles.get(mood, {"energy": (0.3, 0.7)})

        # Build query
        query = Q()
        for feature, (min_val, max_val) in profile.items():
            query &= Q(**{f"{feature}__gte": min_val, f"{feature}__lte": max_val})

        songs = Song.objects.filter(query).order_by("?")[:limit]
        return list(songs)
