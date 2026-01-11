from typing import Dict
import graphene
import logging
from .types import *
from .inputs import *
from ..services import AuthService, UserService
from apps.core.base_schema import BaseMutation
from apps.core.decorators import auth_required, get_authenticated_user

logger = logging.getLogger(__name__)


class AuthMutation(BaseMutation):
    """Base class for authentication mutations"""

    auth_payload = graphene.Field(AuthPayloadType)

    class Meta:
        abstract = True


class Register(AuthMutation):
    """Register a new user"""

    class Arguments:
        input = RegisterInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: Dict):
        logger.info(f"User registration attempt for email: {input.get('email')}")
        result = cls.execute_service_method(AuthService.register_user, input)

        if isinstance(result, BaseMutation):
            logger.warning(f"Registration failed for email: {input.get('email')}")
            return result

        logger.info(f"User registered successfully: {result.get('user').email}")
        auth_payload = cls.create_auth_payload(result)
        return cls.success_response(
            message="Registration successful", auth_payload=auth_payload
        )


class Login(AuthMutation):
    """Login user"""

    class Arguments:
        input = LoginInput(required=True)

    @classmethod
    def mutate(cls, root, info, input: Dict):
        email = input.get("email", "").strip()
        password = input.get("password", "")
        logger.info(f"Login attempt for email: {email}")

        result = cls.execute_service_method(AuthService.login_user, email, password)

        if isinstance(result, BaseMutation):
            logger.warning(f"Login failed for email: {email}")
            return result

        logger.info(f"User logged in successfully: {email}")
        auth_payload = cls.create_auth_payload(result)
        return cls.success_response(
            message="Login successful", auth_payload=auth_payload
        )


class RefreshToken(AuthMutation):
    """Refresh JWT token"""

    class Arguments:
        refresh_token = graphene.String(required=True)

    @classmethod
    def mutate(cls, root, info, refresh_token: str):
        logger.info("Token refresh attempt")
        result = cls.execute_service_method(
            AuthService.refresh_access_token, refresh_token
        )

        if isinstance(result, BaseMutation):
            logger.warning("Token refresh failed")
            return result

        logger.info("Token refreshed successfully")
        auth_payload = cls.create_auth_payload(result)
        return cls.success_response(
            message="Token refreshed successfully", auth_payload=auth_payload
        )


class UpdateProfile(BaseMutation):
    """Update user profile"""

    class Arguments:
        input = UpdateProfileInput(required=True)

    user = graphene.Field(UserType)

    @classmethod
    @auth_required
    def mutate(cls, root, info, input: Dict):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to update profile")

        result = cls.execute_service_method(UserService.update_profile, user, input)

        if isinstance(result, BaseMutation):
            logger.warning(f"Profile update failed for user {user.id}")
            return result

        logger.info(f"Profile updated successfully for user {user.id}")
        return cls.success_response(message="Profile updated successfully", user=result)


class UpdatePreferences(BaseMutation):
    """Update user preferences"""

    class Arguments:
        input = UpdatePreferencesInput(required=True)

    preferences = graphene.Field(UserPreferencesType)

    @classmethod
    @auth_required
    def mutate(cls, root, info, input: Dict):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to update preferences")

        result = cls.execute_service_method(UserService.update_preferences, user, input)

        if isinstance(result, BaseMutation):
            logger.warning(f"Preferences update failed for user {user.id}")
            return result

        logger.info(f"Preferences updated successfully for user {user.id}")
        return cls.success_response(
            message="Preferences updated successfully", preferences=result
        )


class ChangePassword(BaseMutation):
    """Change user password"""

    class Arguments:
        input = ChangePasswordInput(required=True)

    @classmethod
    @auth_required
    def mutate(cls, root, info, input: Dict):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to change password")

        result = cls.execute_service_method(
            AuthService.change_password,
            user,
            input.get("old_password"),
            input.get("new_password"),
        )

        if isinstance(result, BaseMutation):
            logger.warning(f"Password change failed for user {user.id}")
            return result

        logger.info(f"Password changed successfully for user {user.id}")
        return cls.success_response(message="Password changed successfully")


class DeleteAccount(BaseMutation):
    """Delete user account"""

    class Arguments:
        password = graphene.String(required=True)

    @classmethod
    @auth_required
    def mutate(cls, root, info, password: str):
        user = get_authenticated_user(info)
        logger.info(f"User {user.id} attempting to delete account")

        result = cls.execute_service_method(UserService.delete_account, user, password)

        if isinstance(result, BaseMutation):
            logger.warning(f"Account deletion failed for user {user.id}")
            return result

        logger.info(f"Account deleted successfully for user {user.id}")
        return cls.success_response(message="Account deleted successfully")
