import graphene
from apps.music.services import AlbumService
from ..inputs import (
    CreateAlbumInput,
    UpdateAlbumInput,
)
from apps.core.base_schema import BaseMutation
from apps.core.decorators import staff_required


class CreateAlbum(BaseMutation):
    """Create a new album"""

    class Arguments:
        input = CreateAlbumInput(required=True)

    @classmethod
    @staff_required(message="You don't have permission to update albums")
    def mutate(cls, root, info, input):
        try:
            album = AlbumService.create_album(input)
            return CreateAlbum.success_response(
                success=True, message="Album created successfully", data=album
            )
        except Exception as e:
            return CreateAlbum.failure_response(message=str(e))


class UpdateAlbum(BaseMutation):
    """Update an existing album"""

    class Arguments:
        id = graphene.ID(required=True)
        input = UpdateAlbumInput(required=True)

    @classmethod
    @staff_required(message="You don't have permission to update albums")
    def mutate(cls, root, info, id, input):
        try:
            album = AlbumService.update_album(id, input)
            return UpdateAlbum.success_response(
                data=album, message="Album updated successfully"
            )
        except Exception as e:
            return UpdateAlbum(success=False, message=str(e), album=None)


class AlbumMutation(graphene.ObjectType):
    """Album-related GraphQL mutations"""

    create_album = CreateAlbum.Field()
    update_album = UpdateAlbum.Field()
