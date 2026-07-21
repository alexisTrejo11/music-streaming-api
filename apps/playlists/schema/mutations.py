import graphene
import logging
from graphql import GraphQLError
from apps.core.base_schema import BaseMutation
from apps.core.decorators import auth_required, get_authenticated_user
from .inputs import (
    CreatePlaylistInput,
    UpdatePlaylistInput,
    AddSongToPlaylistInput,
    ReorderPlaylistSongsInput,
)
from .types import PlaylistType, PlaylistSongType
from ..services import PlaylistService

logger = logging.getLogger(__name__)


class CreatePlaylist(BaseMutation):
    """Create a new playlist"""

    class Arguments:
        input = CreatePlaylistInput(required=True)

    playlist = graphene.Field(PlaylistType)

    @classmethod
    @auth_required(message="You must be logged in")
    def mutate(cls, root, info, input):
        user = get_authenticated_user(info)
        logger.info(
            f"User {user.id} attempting to create playlist: {input.get('name')}"
        )

        try:
            playlist = PlaylistService.create_playlist(user, input)
            logger.info(
                f"Playlist created successfully by user {user.id}: {playlist.name}"
            )
            return cls.success_response(
                message="Playlist created successfully", playlist=playlist
            )
        except Exception as e:
            logger.error(f"Failed to create playlist for user {user.id}: {str(e)}")
            return cls.failure_response(message=str(e))


class UpdatePlaylist(BaseMutation):
    """Update an existing playlist"""

    class Arguments:
        id = graphene.ID(required=True)
        input = UpdatePlaylistInput(required=True)

    playlist = graphene.Field(PlaylistType)

    @classmethod
    @auth_required
    def mutate(cls, root, info, id, input):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to update playlist {id}")

        try:
            playlist = PlaylistService.update_playlist(user, id, input)
            logger.info(f"Playlist {id} updated successfully by user {user.id}")
            return cls.success_response(
                message="Playlist updated successfully", playlist=playlist
            )
        except Exception as e:
            logger.error(f"Failed to update playlist {id} for user {user.id}: {str(e)}")
            return cls.failure_response(message=str(e))


class DeletePlaylist(BaseMutation):
    """Delete a playlist"""

    class Arguments:
        id = graphene.ID(required=True)

    @classmethod
    @auth_required
    def mutate(cls, root, info, id):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to delete playlist {id}")

        try:
            PlaylistService.delete_playlist(user, id)
            logger.info(f"Playlist {id} deleted successfully by user {user.id}")
            return cls.success_response(message="Playlist deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete playlist {id} for user {user.id}: {str(e)}")
            return cls.failure_response(message=str(e))


class AddSongToPlaylist(BaseMutation):
    """Add a song to a playlist"""

    class Arguments:
        input = AddSongToPlaylistInput(required=True)

    playlist_song = graphene.Field(PlaylistSongType)

    @classmethod
    @auth_required
    def mutate(cls, root, info, input):
        user = get_authenticated_user(info)
        playlist_id = getattr(input, "playlist_id")
        song_id = getattr(input, "song_id")
        logger.info(
            f"User {user.id} attempting to add song {song_id} to playlist {playlist_id}"
        )

        try:
            playlist_song = PlaylistService.add_song_to_playlist(
                user,
                playlist_id,
                song_id,
                getattr(input, "position", None),
            )
            logger.info(
                f"Song {song_id} added successfully to playlist {playlist_id} by user {user.id}"
            )
            return cls.success_response(
                message="Song added to playlist successfully",
                playlist_song=playlist_song,
            )
        except Exception as e:
            logger.error(
                f"Failed to add song {song_id} to playlist {playlist_id} for user {user.id}: {str(e)}"
            )
            return cls.failure_response(message=str(e))


class RemoveSongFromPlaylist(BaseMutation):
    """Remove a song from a playlist"""

    class Arguments:
        playlist_id = graphene.ID(required=True)
        song_id = graphene.ID(required=True)

    @classmethod
    @auth_required
    def mutate(cls, root, info, playlist_id, song_id):
        user = get_authenticated_user(info)
        logger.info(
            f"User {user.id} attempting to remove song {song_id} from playlist {playlist_id}"
        )

        try:
            PlaylistService.remove_song_from_playlist(user, playlist_id, song_id)
            logger.info(
                f"Song {song_id} removed successfully from playlist {playlist_id} by user {user.id}"
            )
            return cls.success_response(
                message="Song removed from playlist successfully"
            )
        except Exception as e:
            logger.error(
                f"Failed to remove song {song_id} from playlist {playlist_id} for user {user.id}: {str(e)}"
            )
            return cls.failure_response(message=str(e))


class ReorderPlaylistSongs(BaseMutation):
    """Reorder songs in a playlist"""

    class Arguments:
        input = ReorderPlaylistSongsInput(required=True)

    @classmethod
    @auth_required
    def mutate(cls, root, info, input):
        user = get_authenticated_user(info)
        playlist_id = getattr(input, "playlist_id")
        song_id = getattr(input, "song_id")
        logger.info(
            f"User {user.id} attempting to reorder song {song_id} in playlist {playlist_id}"
        )

        try:
            PlaylistService.reorder_songs(
                user,
                playlist_id,
                song_id,
                getattr(input, "new_position"),
            )
            logger.info(
                f"Song {song_id} reordered successfully in playlist {playlist_id} by user {user.id}"
            )
            return cls.success_response(message="Playlist songs reordered successfully")
        except Exception as e:
            logger.error(
                f"Failed to reorder song {song_id} in playlist {playlist_id} for user {user.id}: {str(e)}"
            )
            return cls.failure_response(message=str(e))


class FollowPlaylist(BaseMutation):
    """Follow a playlist"""

    class Arguments:
        playlist_id = graphene.ID(required=True)

    playlist = graphene.Field(PlaylistType)

    @classmethod
    @auth_required
    def mutate(cls, root, info, playlist_id):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to follow playlist {playlist_id}")

        try:
            result = PlaylistService.follow_playlist(user, playlist_id)
            if not result["success"]:
                return cls.failure_response(message=result["message"])
            logger.info(
                f"Playlist {playlist_id} followed successfully by user {user.id}"
            )
            return cls.success_response(
                message=result["message"],
                playlist=result["playlist"],
            )
        except Exception as e:
            logger.error(
                f"Failed to follow playlist {playlist_id} for user {user.id}: {str(e)}"
            )
            raise GraphQLError(str(e))


class UnfollowPlaylist(BaseMutation):
    """Unfollow a playlist"""

    class Arguments:
        playlist_id = graphene.ID(required=True)

    @classmethod
    @auth_required
    def mutate(cls, root, info, playlist_id):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to unfollow playlist {playlist_id}")

        try:
            result = PlaylistService.unfollow_playlist(user, playlist_id)
            if not result["success"]:
                return cls.failure_response(message=result["message"])
            logger.info(
                f"Playlist {playlist_id} unfollowed successfully by user {user.id}"
            )
            return cls.success_response(message=result["message"])
        except Exception as e:
            logger.error(
                f"Failed to unfollow playlist {playlist_id} for user {user.id}: {str(e)}"
            )
            raise GraphQLError(str(e))


class DuplicatePlaylist(BaseMutation):
    """Duplicate a playlist to current user's library"""

    class Arguments:
        playlist_id = graphene.ID(required=True)
        new_name = graphene.String()

    playlist = graphene.Field(PlaylistType)

    @classmethod
    @auth_required
    def mutate(cls, root, info, playlist_id, new_name=None):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to duplicate playlist {playlist_id}")

        try:
            playlist = PlaylistService.duplicate_playlist(user, playlist_id, new_name)
            logger.info(
                f"Playlist {playlist_id} duplicated successfully by user {user.id}"
            )
            return cls.success_response(
                message="Playlist duplicated successfully",
                playlist=playlist,
            )
        except Exception as e:
            logger.error(
                f"Failed to duplicate playlist {playlist_id} for user {user.id}: {str(e)}"
            )
            return cls.failure_response(message=str(e))


class AddCollaborator(BaseMutation):
    """Add a collaborator to a playlist"""

    class Arguments:
        playlist_id = graphene.ID(required=True)
        user_id = graphene.ID(required=True)

    @classmethod
    @auth_required
    def mutate(cls, root, info, playlist_id, user_id):
        user = get_authenticated_user(info)
        logger.info(
            f"User {user.id} attempting to add collaborator {user_id} to playlist {playlist_id}"
        )

        try:
            PlaylistService.add_collaborator(user, playlist_id, user_id)
            logger.info(
                f"Collaborator {user_id} added successfully to playlist {playlist_id} by user {user.id}"
            )
            return cls.success_response(message="Collaborator added successfully")
        except Exception as e:
            logger.error(
                f"Failed to add collaborator {user_id} to playlist {playlist_id} for user {user.id}: {str(e)}"
            )
            return cls.failure_response(message=str(e))


class RemoveCollaborator(BaseMutation):
    """Remove a collaborator from a playlist"""

    class Arguments:
        playlist_id = graphene.ID(required=True)
        user_id = graphene.ID(required=True)

    @classmethod
    @auth_required
    def mutate(cls, root, info, playlist_id, user_id):
        user = get_authenticated_user(info)
        logger.info(
            f"User {user.id} attempting to remove collaborator {user_id} from playlist {playlist_id}"
        )

        try:
            PlaylistService.remove_collaborator(user, playlist_id, user_id)
            logger.info(
                f"Collaborator {user_id} removed successfully from playlist {playlist_id} by user {user.id}"
            )
            return cls.success_response(message="Collaborator removed successfully")
        except Exception as e:
            logger.error(
                f"Failed to remove collaborator {user_id} from playlist {playlist_id} for user {user.id}: {str(e)}"
            )
            return cls.failure_response(message=str(e))
