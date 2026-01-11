"""
GraphQL Query resolvers for recommendations
"""

import graphene
from graphql import GraphQLError

from apps.recommendations.models import UserTaste, Radio
from apps.core.decorators import auth_required, get_authenticated_user
from apps.recommendations.services import (
    RecommendationService,
    TasteProfileService,
    RadioService,
    MoodService,
    TrendingService,
)
from .types import (
    UserTasteType,
    AudioPreferencesType,
    RecommendedSongType,
    DiscoverWeeklyType,
    RadioType,
)


class RecommendationQuery(graphene.ObjectType):
    """Recommendation-related GraphQL queries"""

    # Taste Profile
    my_taste_profile = graphene.Field(
        UserTasteType, description="Get current user's taste profile"
    )

    audio_preferences = graphene.Field(
        AudioPreferencesType, description="Get user's audio feature preferences"
    )

    # Recommendations
    recommended_songs = graphene.List(
        RecommendedSongType,
        limit=graphene.Int(default_value=30),
        description="Get personalized song recommendations with explanations",
    )

    similar_songs = graphene.List(
        "apps.music.schema.types.SongType",
        song_id=graphene.ID(required=True),
        limit=graphene.Int(default_value=20),
        description="Get songs similar to a specific song",
    )

    discover_weekly = graphene.Field(
        DiscoverWeeklyType,
        description="Get user's personalized Discover Weekly playlist",
    )

    recommended_artists = graphene.List(
        "apps.artists.schema.types.ArtistType",
        limit=graphene.Int(default_value=20),
        description="Get recommended artists based on user taste",
    )

    recommended_albums = graphene.List(
        "apps.music.schema.types.AlbumType",
        limit=graphene.Int(default_value=20),
        description="Get recommended albums",
    )

    # Radio
    my_radios = graphene.List(RadioType, description="Get user's radio stations")

    radio = graphene.Field(
        RadioType,
        id=graphene.ID(required=True),
        description="Get a specific radio station with generated songs",
    )

    # Mood-based
    songs_by_mood = graphene.List(
        "apps.music.schema.types.SongType",
        mood=graphene.String(required=True),
        limit=graphene.Int(default_value=30),
        description="Get songs matching a specific mood",
    )

    trending_for_you = graphene.List(
        "apps.music.schema.types.SongType",
        limit=graphene.Int(default_value=30),
        description="Get trending songs personalized for user",
    )

    # === Resolvers ===

    @auth_required
    def resolve_my_taste_profile(self, info):
        """Get user's taste profile"""
        user = get_authenticated_user(info)

        taste, _ = UserTaste.objects.get_or_create(user=user)

        # Update taste profile if outdated
        from django.utils import timezone
        from datetime import timedelta

        if not taste.last_updated or (timezone.now() - taste.last_updated) > timedelta(
            days=7
        ):
            TasteProfileService.update_taste_profile(user)
            taste.refresh_from_db()

        return taste

    @auth_required
    def resolve_audio_preferences(self, info):
        """Get user's audio preferences"""
        user = get_authenticated_user(info)

        return TasteProfileService.get_audio_preferences(user)

    def resolve_recommended_songs(self, info, limit=30):
        """Get personalized recommendations with reasoning"""
        user = info.context.user
        if not user.is_authenticated:
            # Return popular songs for non-authenticated users
            from apps.music.models import Song

            popular_songs = Song.objects.order_by("-play_count")[:limit]
            return [
                {
                    "song": song,
                    "score": 0.5,
                    "reasons": [{"type": "popular", "description": "Popular song"}],
                }
                for song in popular_songs
            ]

        return RecommendationService.get_personalized_recommendations(user, limit)

    def resolve_similar_songs(self, info, song_id, limit=20):
        """Get similar songs"""
        return RecommendationService.get_similar_songs(song_id, limit)

    @auth_required
    def resolve_discover_weekly(self, info):
        """Get Discover Weekly playlist"""
        user = get_authenticated_user(info)

        return RecommendationService.generate_discover_weekly(user)

    @auth_required
    def resolve_recommended_artists(self, info, limit=20):
        """Get recommended artists"""
        user = get_authenticated_user(info)

        return TrendingService.get_recommended_artists(user, limit)

    @auth_required
    def resolve_recommended_albums(self, info, limit=20):
        """Get recommended albums"""
        user = get_authenticated_user(info)

        return TrendingService.get_recommended_albums(user, limit)

    @auth_required
    def resolve_my_radios(self, info):
        """Get user's radio stations"""
        user = get_authenticated_user(info)

        return Radio.objects.filter(user=user).order_by("-created_at")

    @auth_required
    def resolve_radio(self, info, id):
        """Get specific radio station"""
        user = get_authenticated_user(info)

        try:
            return Radio.objects.get(id=id, user=user)
        except Radio.DoesNotExist:
            raise GraphQLError(f"Radio with ID {id} not found")

    def resolve_songs_by_mood(self, info, mood, limit=30):
        """Get songs by mood"""
        return MoodService.get_songs_by_mood(mood, limit)

    def resolve_trending_for_you(self, info, limit=30):
        """Get personalized trending songs"""
        user = info.context.user
        if not user.is_authenticated:
            # Return global trending for non-authenticated users
            from apps.music.services import SongService

            return SongService.get_trending_songs("WEEK", limit)

        return TrendingService.get_trending_for_you(user, limit)
