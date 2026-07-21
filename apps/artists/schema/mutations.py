import graphene
import logging
from apps.core.base_schema import TypedBaseMutation
from apps.core.decorators import staff_required, get_authenticated_user
from .inputs import CreateArtistInput, UpdateArtistInput, AddArtistMemberInput
from .types import ArtistType
from ..services import ArtistService

logger = logging.getLogger(__name__)


class CreateArtist(TypedBaseMutation):
    """Create a new artist (admin/verified users only)"""

    data = graphene.Field(ArtistType)

    class Arguments:
        input = CreateArtistInput(required=True)

    @classmethod
    @staff_required(message="You don't have permission to create artists")
    def mutate(cls, root, info, input):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to create artist: {input.get('name')}")

        try:
            artist = ArtistService.create_artist(input)
            logger.info(f"Artist created successfully by user {user.id}: {artist.name}")
            return cls.success_response(
                data=artist, message="Artist created successfully"
            )
        except Exception as e:
            logger.error(f"Failed to create artist for user {user.id}: {str(e)}")
            return cls.failure_response(message=str(e))


class UpdateArtist(TypedBaseMutation):
    """Update an existing artist (admin/verified users only)"""

    data = graphene.Field(ArtistType)

    class Arguments:
        id = graphene.ID(required=True)
        input = UpdateArtistInput(required=True)

    @classmethod
    @staff_required(message="You don't have permission to update artists")
    def mutate(cls, root, info, id, input):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to update artist {id}")

        try:
            artist = ArtistService.update_artist(id, input)
            logger.info(f"Artist {id} updated successfully by user {user.id}")
            return cls.success_response(
                data=artist, message="Artist updated successfully"
            )
        except Exception as e:
            logger.error(f"Failed to update artist {id} for user {user.id}: {str(e)}")
            return cls.failure_response(message=str(e))


class DeleteArtist(TypedBaseMutation):
    """Delete an existing artist (admin/verified users only)"""

    class Arguments:
        id = graphene.ID(required=True)

    @classmethod
    @staff_required(message="You don't have permission to delete artists")
    def mutate(cls, root, info, id):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to delete artist {id}")

        try:
            ArtistService.delete_artist(id)
            logger.info(f"Artist {id} deleted successfully by user {user.id}")
            return cls.success_response(message="Artist deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete artist {id} for user {user.id}: {str(e)}")
            return cls.failure_response(message=str(e))


class AddArtistMember(TypedBaseMutation):
    """Add a member to an artist (admin/verified users only)"""

    data = graphene.Field(ArtistType)

    class Arguments:
        input = AddArtistMemberInput(required=True)

    @classmethod
    @staff_required(message="You don't have permission to add artist members")
    def mutate(cls, root, info, input):
        user = get_authenticated_user(info)
        logger.info(
            f"User {user.id} attempting to add member to artist {input.get('artist_id')}"
        )

        try:
            artist = ArtistService.add_member(input)
            logger.info(f"Member added successfully to artist by user {user.id}")
            return cls.success_response(
                data=artist, message="Artist member added successfully"
            )
        except Exception as e:
            logger.error(f"Failed to add member to artist for user {user.id}: {str(e)}")
            return cls.failure_response(message=str(e))


class RemoveArtistMember(TypedBaseMutation):
    """Remove a member from an artist (admin/verified users only)"""

    data = graphene.Field(ArtistType)

    class Arguments:
        artist_id = graphene.ID(required=True)
        member_id = graphene.ID(required=True)

    @classmethod
    @staff_required(message="You don't have permission to remove artist members")
    def mutate(cls, root, info, artist_id, member_id):
        user = get_authenticated_user(info)
        logger.info(
            f"User {user.id} attempting to remove member {member_id} from artist {artist_id}"
        )

        try:
            artist = ArtistService.remove_member(member_id)
            logger.info(
                f"Member {member_id} removed successfully from artist {artist_id} by user {user.id}"
            )
            return cls.success_response(
                data=artist, message="Artist member removed successfully"
            )
        except Exception as e:
            logger.error(
                f"Failed to remove member {member_id} from artist {artist_id} for user {user.id}: {str(e)}"
            )
            return cls.failure_response(message=str(e))


class ArtistMutationMixin:
    """Artist-related GraphQL mutations"""

    # TODO: implement these later
    # follow_artist = FollowArtist.Field()
    # unfollow_artist = UnfollowArtist.Field()
    create_artist = CreateArtist.Field()
    update_artist = UpdateArtist.Field()
    delete_artist = DeleteArtist.Field()
    add_artist_member = AddArtistMember.Field()
    remove_artist_member = RemoveArtistMember.Field()
