import graphene
from graphene_django import DjangoObjectType
from ..models import UserTaste, Radio
from ..services import RadioService


def get_song_type():
    """Lazy import to avoid circular dependency"""
    from apps.music.schema.types import SongType

    return SongType


class UserTasteType(DjangoObjectType):
    """Type for user taste profile"""

    class Meta:
        model = UserTaste
        fields = (
            "id",
            "user",
            "favorite_genres",
            "top_artists",
            "energy_preference",
            "danceability_preference",
            "valence_preference",
            "last_updated",
        )
        interfaces = (graphene.relay.Node,)


class RadioType(DjangoObjectType):
    """Type for radio stations"""

    songs = graphene.List(lambda: get_song_type())

    class Meta:
        model = Radio
        fields = (
            "id",
            "user",
            "name",
            "seed_artist",
            "seed_song",
            "seed_genre",
            "created_at",
            "updated_at",
        )
        interfaces = (graphene.relay.Node,)

    def resolve_songs(self, info):
        """Generate songs for this radio station"""
        from apps.recommendations.services import RecommendationService

        return RadioService.generate_radio_songs(self, limit=50)


class RecommendationReasonType(graphene.ObjectType):
    """Type for recommendation reasoning"""

    type = graphene.String()  # genre_match, artist_match, similar_users, audio_features
    description = graphene.String()


class RecommendedSongType(graphene.ObjectType):
    """Type for recommended songs with reasoning"""

    song = graphene.Field(lambda: get_song_type())
    score = graphene.Float()
    reasons = graphene.List(RecommendationReasonType)


class DiscoverWeeklyType(graphene.ObjectType):
    """Type for Discover Weekly playlist"""

    id = graphene.String()
    name = graphene.String()
    description = graphene.String()
    songs = graphene.List(lambda: get_song_type())
    refresh_date = graphene.DateTime()


class AudioPreferencesType(graphene.ObjectType):
    """Type for audio feature preferences"""

    energy = graphene.Float()
    danceability = graphene.Float()
    valence = graphene.Float()
    tempo_range = graphene.List(graphene.Float)
