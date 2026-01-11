from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from typing import Dict, List
import numpy as np

from apps.music.models import Song
from apps.interactions.models import ListeningHistory, LikedSong, FollowedArtist
from apps.recommendations.models import UserTaste
from .base_service import BaseRecommendationService
from .taste_profile_service import TasteProfileService


class RecommendationService(BaseRecommendationService):
    """Service for personalized recommendations"""

    @staticmethod
    def get_personalized_recommendations(user, limit: int = 30) -> List[Dict]:
        """
        Get personalized song recommendations with explanations
        """
        # Ensure taste profile is up to date
        taste, _ = UserTaste.objects.get_or_create(user=user)
        if not taste.last_updated or (timezone.now() - taste.last_updated) > timedelta(
            days=7
        ):
            TasteProfileService.update_taste_profile(user)
            taste.refresh_from_db()

        # Get songs user already knows
        known_song_ids = set()

        # Add listened songs
        listened = ListeningHistory.objects.filter(user=user).values_list(
            "song_id", flat=True
        )
        known_song_ids.update(listened)

        # Add liked songs
        liked = LikedSong.objects.filter(user=user).values_list("song_id", flat=True)
        known_song_ids.update(liked)

        # Build candidate pool
        candidates = Song.objects.exclude(id__in=known_song_ids).select_related(
            "artist", "album", "genre"
        )

        # Filter by favorite genres
        favorite_genres = list(taste.favorite_genres.values_list("id", flat=True))
        if favorite_genres:
            candidates = candidates.filter(
                Q(genre_id__in=favorite_genres)
                | Q(artist__genres__id__in=favorite_genres)
            ).distinct()

        # Get followed artists
        followed_artists = FollowedArtist.objects.filter(user=user).values_list(
            "artist_id", flat=True
        )

        # Score and rank candidates
        recommendations = []

        # Get a reasonable sample to score
        sample_size = min(500, candidates.count())
        candidate_sample = candidates.order_by("?")[:sample_size]

        for song in candidate_sample:
            score = 0.0
            reasons = []

            # Genre match (30% weight)
            if song.genre_id in favorite_genres:
                score += 0.3
                reasons.append(
                    {
                        "type": "genre_match",
                        "description": f"Matches your favorite genre: {song.genre.name}",
                    }
                )

            # Artist match (25% weight)
            if song.artist_id in followed_artists:
                score += 0.25
                reasons.append(
                    {
                        "type": "artist_match",
                        "description": f"By {song.artist.name}, an artist you follow",
                    }
                )

            # Audio features similarity (25% weight)
            if all(
                [
                    song.energy is not None,
                    song.danceability is not None,
                    song.valence is not None,
                ]
            ):
                feature_score = RecommendationService._calculate_audio_similarity(
                    song,
                    taste.energy_preference,
                    taste.danceability_preference,
                    taste.valence_preference,
                )
                score += 0.25 * feature_score

                if feature_score > 0.7:
                    reasons.append(
                        {
                            "type": "audio_features",
                            "description": "Matches your listening preferences",
                        }
                    )

            # Popularity factor (20% weight)
            if song.play_count > 1000:
                normalized_popularity = min(song.play_count / 100000, 1.0)
                score += 0.2 * normalized_popularity

                if song.play_count > 10000:
                    reasons.append(
                        {
                            "type": "popular",
                            "description": "Popular track you might enjoy",
                        }
                    )

            if score > 0.3:  # Minimum threshold
                recommendations.append(
                    {"song": song, "score": score, "reasons": reasons}
                )

        # Sort by score and return top results
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]

    @staticmethod
    def get_similar_songs(song_id: str, limit: int = 20) -> List[Song]:
        """
        Get songs similar to a given song using audio features
        """
        from django.core.exceptions import ValidationError

        try:
            reference_song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            raise ValidationError(f"Song with ID {song_id} not found")

        # If no audio features, fall back to genre/artist matching
        if not all(
            [reference_song.energy, reference_song.danceability, reference_song.valence]
        ):
            similar = (
                Song.objects.filter(
                    Q(genre=reference_song.genre) | Q(artist=reference_song.artist)
                )
                .exclude(id=song_id)
                .order_by("-play_count")[:limit]
            )
            return list(similar)

        # Use audio features for similarity
        candidates = Song.objects.exclude(id=song_id).filter(
            energy__isnull=False, danceability__isnull=False, valence__isnull=False
        )

        # Boost songs from same genre/artist
        candidates = candidates.filter(
            Q(genre=reference_song.genre)
            | Q(artist=reference_song.artist)
            | Q(artist__genres__in=reference_song.artist.genres.all())
        ).distinct()[
            :200
        ]  # Limit candidates for performance

        # Calculate similarity scores
        similar_songs = []
        for song in candidates:
            similarity = RecommendationService._calculate_audio_similarity(
                song,
                reference_song.energy,
                reference_song.danceability,
                reference_song.valence,
            )

            # Boost if same tempo range
            if reference_song.tempo and song.tempo:
                tempo_diff = abs(reference_song.tempo - song.tempo)
                if tempo_diff < 20:
                    similarity += 0.1

            similar_songs.append((song, similarity))

        # Sort by similarity
        similar_songs.sort(key=lambda x: x[1], reverse=True)

        return [song for song, _ in similar_songs[:limit]]

    @staticmethod
    def generate_discover_weekly(user) -> Dict:
        """
        Generate a Discover Weekly style playlist
        """
        # Get deep cuts and lesser-known songs that match user taste
        recommendations = RecommendationService.get_personalized_recommendations(
            user, limit=50
        )

        # Filter for discovery (lower play counts)
        discover_songs = [
            rec["song"]
            for rec in recommendations
            if rec["song"].play_count < 50000  # Relatively undiscovered
        ][:30]

        return {
            "id": f"discover_weekly_{user.id}",
            "name": "Discover Weekly",
            "description": "Your weekly mixtape of fresh music",
            "songs": discover_songs,
            "refresh_date": RecommendationService._get_next_monday(),
        }
