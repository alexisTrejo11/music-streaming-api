from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from typing import List

from apps.music.models import Song, Album
from apps.artists.models import Artist
from apps.recommendations.models import UserTaste
from apps.interactions.models import FollowedArtist


class TrendingService:
    """Service for trending recommendations"""

    @staticmethod
    def get_recommended_artists(user, limit: int = 20) -> List[Artist]:
        """Get recommended artists"""
        taste, _ = UserTaste.objects.get_or_create(user=user)

        # Get followed artists
        followed = FollowedArtist.objects.filter(user=user).values_list(
            "artist_id", flat=True
        )

        # Get favorite genres
        favorite_genres = list(taste.favorite_genres.values_list("id", flat=True))

        # Find artists in favorite genres that user doesn't follow
        recommended = (
            Artist.objects.filter(genres__id__in=favorite_genres)
            .exclude(id__in=followed)
            .distinct()
            .order_by("-monthly_listeners")[:limit]
        )

        return list(recommended)

    @staticmethod
    def get_recommended_albums(user, limit: int = 20) -> List[Album]:
        """Get recommended albums"""
        taste, _ = UserTaste.objects.get_or_create(user=user)

        # Get top artists
        top_artists = list(taste.top_artists.values_list("id", flat=True))

        # Get albums from top artists
        artist_albums = Album.objects.filter(artist_id__in=top_artists).order_by(
            "-release_date"
        )[:10]

        # Get albums in favorite genres
        favorite_genres = list(taste.favorite_genres.values_list("id", flat=True))
        genre_albums = (
            Album.objects.filter(songs__genre_id__in=favorite_genres)
            .distinct()
            .order_by("-play_count")[:10]
        )

        # Combine and deduplicate
        all_albums = list(artist_albums) + list(genre_albums)
        seen = set()
        unique_albums = []

        for album in all_albums:
            if album.id not in seen:
                seen.add(album.id)
                unique_albums.append(album)
                if len(unique_albums) >= limit:
                    break

        return unique_albums

    @staticmethod
    def get_trending_for_you(user, limit: int = 30) -> List[Song]:
        """Get personalized trending songs"""
        taste, _ = UserTaste.objects.get_or_create(user=user)

        # Get favorite genres
        favorite_genres = list(taste.favorite_genres.values_list("id", flat=True))

        # Get trending songs in user's favorite genres
        time_filter = timezone.now() - timedelta(weeks=1)

        trending = (
            Song.objects.filter(
                genre_id__in=favorite_genres, plays__played_at__gte=time_filter
            )
            .annotate(recent_plays=Count("plays"))
            .order_by("-recent_plays", "-play_count")[:limit]
        )

        return list(trending)
