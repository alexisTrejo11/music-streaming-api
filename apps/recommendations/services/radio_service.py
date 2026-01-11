from django.core.exceptions import ValidationError
from typing import Dict, List

from apps.music.models import Song, Genre
from apps.artists.models import Artist
from apps.recommendations.models import Radio
from .base_service import BaseRecommendationService


class RadioService(BaseRecommendationService):
    """Service for radio station functionality"""

    @staticmethod
    def create_radio(user, data: Dict) -> Radio:
        """Create a radio station"""
        name = data.get("name", "").strip()

        if not name:
            raise ValidationError("Radio name is required")

        # At least one seed is required
        seed_artist_id = data.get("seed_artist_id")
        seed_song_id = data.get("seed_song_id")
        seed_genre_id = data.get("seed_genre_id")

        if not any([seed_artist_id, seed_song_id, seed_genre_id]):
            raise ValidationError(
                "At least one seed (artist, song, or genre) is required"
            )

        # Validate seeds
        seed_artist = None
        seed_song = None
        seed_genre = None

        if seed_artist_id:
            try:
                seed_artist = Artist.objects.get(id=seed_artist_id)
            except Artist.DoesNotExist:
                raise ValidationError(f"Artist with ID {seed_artist_id} not found")

        if seed_song_id:
            try:
                seed_song = Song.objects.get(id=seed_song_id)
            except Song.DoesNotExist:
                raise ValidationError(f"Song with ID {seed_song_id} not found")

        if seed_genre_id:
            try:
                seed_genre = Genre.objects.get(id=seed_genre_id)
            except Genre.DoesNotExist:
                raise ValidationError(f"Genre with ID {seed_genre_id} not found")

        # Create radio
        radio = Radio.objects.create(
            user=user,
            name=name,
            seed_artist=seed_artist,
            seed_song=seed_song,
            seed_genre=seed_genre,
        )

        return radio

    @staticmethod
    def delete_radio(user, radio_id: str) -> bool:
        """Delete a radio station"""
        try:
            radio = Radio.objects.get(id=radio_id, user=user)
            radio.delete()
            return True
        except Radio.DoesNotExist:
            raise ValidationError(f"Radio with ID {radio_id} not found")

    @staticmethod
    def generate_radio_songs(radio: Radio, limit: int = 50) -> List[Song]:
        """Generate songs for a radio station"""
        from apps.recommendations.services.recommendation_service import (
            RecommendationService,
        )
        from django.db.models import Q

        base_query = Song.objects.all()

        # Build query based on seeds
        if radio.seed_song:
            # Use similar songs logic
            return RecommendationService.get_similar_songs(radio.seed_song_id, limit)

        if radio.seed_artist:
            # Get songs from artist and similar artists
            similar_artists = Artist.objects.filter(
                genres__in=radio.seed_artist.genres.all()
            ).distinct()[:10]

            base_query = base_query.filter(artist__in=similar_artists)

        if radio.seed_genre:
            # Get songs from genre
            base_query = base_query.filter(genre=radio.seed_genre)

        # Order by variety
        songs = base_query.order_by("?")[:limit]
        return list(songs)
