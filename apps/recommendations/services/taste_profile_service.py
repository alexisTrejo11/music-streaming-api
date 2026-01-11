from django.db.models import Count, Q, F, Avg
from django.utils import timezone
from datetime import timedelta
from typing import Dict, List
import numpy as np

from apps.music.models import Genre
from apps.artists.models import Artist
from apps.interactions.models import ListeningHistory, LikedSong
from apps.recommendations.models import UserTaste
from .base_service import BaseRecommendationService


class TasteProfileService(BaseRecommendationService):
    """Service for managing user taste profiles"""

    @staticmethod
    def update_taste_profile(user) -> UserTaste:
        """
        Update user's taste profile based on listening history and interactions
        """
        taste, _ = UserTaste.objects.get_or_create(user=user)

        # Get recent listening history (last 200 plays)
        recent_plays = ListeningHistory.objects.filter(
            user=user, played_at__gte=timezone.now() - timedelta(days=90)
        ).select_related("song__genre", "song__artist")[:200]

        if not recent_plays:
            return taste

        # Analyze favorite genres
        genre_counts = {}
        for play in recent_plays:
            if play.song.genre:
                genre_id = play.song.genre_id
                genre_counts[genre_id] = genre_counts.get(genre_id, 0) + 1

        # Get top 5 genres
        top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        favorite_genres = Genre.objects.filter(id__in=[g[0] for g in top_genres])
        taste.favorite_genres.set(favorite_genres)

        # Analyze top artists
        artist_counts = {}
        for play in recent_plays:
            artist_id = play.song.artist_id
            artist_counts[artist_id] = artist_counts.get(artist_id, 0) + 1

        # Get top 10 artists
        top_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]
        top_artist_objs = Artist.objects.filter(id__in=[a[0] for a in top_artists])
        taste.top_artists.set(top_artist_objs)

        # Calculate audio feature preferences
        audio_features = TasteProfileService._calculate_audio_preferences(user)
        taste.energy_preference = audio_features["energy"]
        taste.danceability_preference = audio_features["danceability"]
        taste.valence_preference = audio_features["valence"]

        taste.last_updated = timezone.now()
        taste.save()

        return taste

    @staticmethod
    def update_taste_profile_manual(user, data: Dict) -> UserTaste:
        """
        Manually update taste profile
        """
        taste, _ = UserTaste.objects.get_or_create(user=user)

        # Update favorite genres
        if "favorite_genre_ids" in data:
            genres = Genre.objects.filter(id__in=data["favorite_genre_ids"])
            taste.favorite_genres.set(genres)

        # Update top artists
        if "top_artist_ids" in data:
            artists = Artist.objects.filter(id__in=data["top_artist_ids"])
            taste.top_artists.set(artists)

        taste.last_updated = timezone.now()
        taste.save()

        return taste

    @staticmethod
    def get_audio_preferences(user) -> Dict:
        """Get user's audio feature preferences"""
        features = TasteProfileService._calculate_audio_preferences(user)

        # Calculate tempo range based on liked songs
        liked_songs = LikedSong.objects.filter(
            user=user, song__tempo__isnull=False
        ).values_list("song__tempo", flat=True)[:50]

        if liked_songs:
            tempos = list(liked_songs)
            tempo_range = [
                float(np.percentile(tempos, 25)),
                float(np.percentile(tempos, 75)),
            ]
        else:
            tempo_range = [80.0, 140.0]  # Default range

        return {
            "energy": features["energy"],
            "danceability": features["danceability"],
            "valence": features["valence"],
            "tempo_range": tempo_range,
        }

    @staticmethod
    def _calculate_audio_preferences(user) -> Dict:
        """Calculate user's audio feature preferences from liked songs"""
        liked_songs = LikedSong.objects.filter(
            user=user, song__energy__isnull=False
        ).select_related("song")[:100]

        if not liked_songs:
            return {"energy": 0.5, "danceability": 0.5, "valence": 0.5}

        # Calculate averages using numpy
        energies = [ls.song.energy for ls in liked_songs if ls.song.energy is not None]
        danceabilities = [
            ls.song.danceability
            for ls in liked_songs
            if ls.song.danceability is not None
        ]
        valences = [
            ls.song.valence for ls in liked_songs if ls.song.valence is not None
        ]

        return {
            "energy": float(np.mean(energies)) if energies else 0.5,
            "danceability": float(np.mean(danceabilities)) if danceabilities else 0.5,
            "valence": float(np.mean(valences)) if valences else 0.5,
        }
