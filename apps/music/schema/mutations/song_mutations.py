import graphene
from graphql import GraphQLError
from ..types import SongType
from ...services import SongService
from ..inputs import (
    CreateSongInput,
    UpdateSongInput,
)
from apps.core.base_schema import BaseMutation
from apps.core.decorators import (
    auth_required,
    staff_required,
    superuser_required,
    get_authenticated_user,
)


class CreateSong(BaseMutation):
    """Create a new song (artist/admin only)"""

    class Arguments:
        input = CreateSongInput(required=True)

    @classmethod
    @staff_required(message="You don't have permission to create songs")
    def mutate(cls, root, info, input):
        try:
            song = SongService.create_song(input)
            return CreateSong.success_response(
                data=song, message="Song created successfully"
            )
        except Exception as e:
            return CreateSong.failure_response(message=str(e))


class UpdateSong(BaseMutation):
    """Update an existing song"""

    class Arguments:
        id = graphene.ID(required=True)
        input = UpdateSongInput(required=True)

    @classmethod
    @staff_required(message="You don't have permission to update songs")
    def mutate(cls, root, info, id, input):
        try:
            song = SongService.update_song(id, input)
            return UpdateSong.success_response(
                data=song, message="Song updated successfully"
            )
        except Exception as e:
            return UpdateSong.failure_response(message=str(e))


class DeleteSong(BaseMutation):
    """Delete a song (admin only)"""

    class Arguments:
        id = graphene.ID(required=True)

    @classmethod
    @superuser_required(message="Only superusers can delete songs")
    def mutate(cls, root, info, id):
        try:
            SongService.delete_song(id)
            return DeleteSong.success_response(message="Song deleted successfully")
        except Exception as e:
            return DeleteSong.failure_response(message=str(e))


class LikeSong(BaseMutation):
    """Like a song"""

    class Arguments:
        song_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    song = graphene.Field(SongType)

    @classmethod
    @auth_required(message="You must be logged in to like songs")
    def mutate(cls, root, info, song_id):
        user = get_authenticated_user(info)

        try:
            result = SongService.like_song(user, song_id)
            return LikeSong(
                success=result["success"],
                message=result["message"],
                song=result["song"],
            )
        except Exception as e:
            raise GraphQLError(str(e))


class UnlikeSong(BaseMutation):
    """Unlike a song"""

    class Arguments:
        song_id = graphene.ID(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    @auth_required(message="You must be logged in to unlike songs")
    def mutate(cls, root, info, song_id):
        user = get_authenticated_user(info)

        try:
            result = SongService.unlike_song(user, song_id)
            return UnlikeSong(success=result["success"], message=result["message"])
        except Exception as e:
            raise GraphQLError(str(e))


class PlaySong(graphene.Mutation):
    """Track song play for listening history"""

    class Arguments:
        song_id = graphene.ID(required=True)
        source = graphene.String()  # playlist, album, radio, search
        source_id = graphene.String()

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    @auth_required(message="You must be logged in")
    def mutate(cls, root, info, song_id, source=None, source_id=None):
        user = get_authenticated_user(info)

        try:
            SongService.track_play(user, song_id, source, source_id)
            return PlaySong(success=True, message="Play tracked successfully")
        except Exception as e:
            return PlaySong(success=False, message=str(e))


class SongMutation(graphene.ObjectType):
    """Song-related GraphQL mutations"""

    create_song = CreateSong.Field()
    update_song = UpdateSong.Field()
    delete_song = DeleteSong.Field()
    like_song = LikeSong.Field()
    unlike_song = UnlikeSong.Field()
    play_song = PlaySong.Field()
