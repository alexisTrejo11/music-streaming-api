from functools import wraps
from django.core.exceptions import PermissionDenied


def _get_info_from_args(args):
    """
    Extract GraphQL ResolveInfo from mutation/query resolver args.
    Classmethods: (cls, root, info, ...)
    Instance methods: (self, info, ...)
    """
    if len(args) >= 3:
        return args[2]
    if len(args) >= 2:
        return args[1]
    raise ValueError("Invalid arguments for auth decorator")


def _get_user_from_info(info):
    if not hasattr(info, "context") or not hasattr(info.context, "user"):
        raise PermissionDenied("Authentication context not available")
    return info.context.user


def require_auth(*, staff=False, superuser=False, message=None, auth_message=None):
    """
    Parameterized auth/authorization decorator for GraphQL resolvers.

    Examples:
        @require_auth()
        @require_auth(auth_message="You must be logged in")
        @require_auth(staff=True)
        @require_auth(staff=True, message="You don't have permission to create artists")
        @require_auth(superuser=True, message="Only superusers can delete songs")
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = _get_user_from_info(_get_info_from_args(args))

            if not user.is_authenticated:
                raise PermissionDenied(auth_message or "Authentication required")

            if superuser and not user.is_superuser:
                raise PermissionDenied(
                    message or "Only superusers can perform this action"
                )

            if staff and not (user.is_staff or user.is_superuser):
                raise PermissionDenied(
                    message or "You don't have permission to perform this action"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def auth_required(func=None, *, message="Authentication required"):
    """
    Require an authenticated user.

    Usage:
        @auth_required
        @auth_required(message="You must be logged in")
    """

    def decorator(f):
        return require_auth(auth_message=message)(f)

    if func is not None:
        return decorator(func)
    return decorator


def staff_required(func=None, *, message=None):
    """
    Require an authenticated staff or superuser.

    Usage:
        @staff_required
        @staff_required(message="You don't have permission to create artists")
    """

    def decorator(f):
        return require_auth(
            staff=True,
            message=message or "You don't have permission to perform this action",
        )(f)

    if func is not None:
        return decorator(func)
    return decorator


def superuser_required(func=None, *, message=None):
    """
    Require an authenticated superuser.

    Usage:
        @superuser_required
        @superuser_required(message="Only superusers can delete songs")
    """

    def decorator(f):
        return require_auth(
            superuser=True,
            message=message or "Only superusers can perform this action",
        )(f)

    if func is not None:
        return decorator(func)
    return decorator


def get_authenticated_user(info):
    user = _get_user_from_info(info)
    if not user.is_authenticated:
        raise PermissionDenied("Authentication required")
    return user
