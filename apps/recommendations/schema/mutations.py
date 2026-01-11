"""
GraphQL Mutations for recommendations
"""

import graphene
from apps.core.decorators import auth_required, get_authenticated_user
from apps.core.base_schema import BaseMutation
from apps.recommendations.services import RadioService, TasteProfileService
from .types import UserTasteType, RadioType
from .inputs import CreateRadioInput, UpdateTasteProfileInput


class CreateRadio(BaseMutation):
    """Create a radio station"""

    class Arguments:
        input = CreateRadioInput(required=True)

    radio = graphene.Field(RadioType)

    @classmethod
    @auth_required
    def mutate(cls, root, info, input):
        user = info.context.user

        try:
            radio = RadioService.create_radio(user, input)
            return CreateRadio.success_response(
                message="Radio station created successfully", radio=radio
            )
        except Exception as e:
            return CreateRadio.failure_response(message=str(e))


class DeleteRadio(BaseMutation):
    """Delete a radio station"""

    class Arguments:
        id = graphene.ID(required=True)

    @classmethod
    @auth_required
    def mutate(cls, root, info, id):
        user = get_authenticated_user(info)

        try:
            # Decode relay ID if it's a global ID
            from graphql_relay import from_global_id

            _, db_id = from_global_id(id)
            # If from_global_id returns empty string, use the original id
            radio_id = db_id if db_id else id

            RadioService.delete_radio(user, radio_id)
            return DeleteRadio.success_response(
                message="Radio station deleted successfully"
            )
        except Exception as e:
            return DeleteRadio.failure_response(message=str(e))


class UpdateTasteProfile(BaseMutation):
    """Manually update user taste profile"""

    class Arguments:
        input = UpdateTasteProfileInput(required=True)

    taste_profile = graphene.Field(UserTasteType)

    @classmethod
    @auth_required
    def mutate(cls, root, info, input):
        user = get_authenticated_user(info)

        try:
            taste = TasteProfileService.update_taste_profile_manual(user, input)
            return UpdateTasteProfile.success_response(
                message="Taste profile updated successfully",
                taste_profile=taste,
            )
        except Exception as e:
            return UpdateTasteProfile.failure_response(message=str(e))


class RefreshTasteProfile(BaseMutation):
    """Refresh taste profile based on recent activity"""

    taste_profile = graphene.Field(UserTasteType)

    @classmethod
    @auth_required
    def mutate(cls, root, info):
        user = get_authenticated_user(info)
        try:
            taste = TasteProfileService.update_taste_profile(user)
            return RefreshTasteProfile.success_response(
                message="Taste profile refreshed successfully",
                taste_profile=taste,
            )
        except Exception as e:
            return RefreshTasteProfile.failure_response(message=str(e))


class RecommendationMutation(graphene.ObjectType):
    """Recommendation-related GraphQL mutations"""

    create_radio = CreateRadio.Field()
    delete_radio = DeleteRadio.Field()
    update_taste_profile = UpdateTasteProfile.Field()
    refresh_taste_profile = RefreshTasteProfile.Field()
