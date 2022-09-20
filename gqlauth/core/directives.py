from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext as _
from jwt import PyJWTError
import strawberry
from strawberry.schema_directive import Location
from strawberry.types import Info

from gqlauth.core.exceptions import TokenExpired
from gqlauth.core.types_ import GQLAuthError, GQLAuthErrors
from gqlauth.core.utils import get_status
from gqlauth.jwt.types_ import TokenType
from gqlauth.settings import gqlauth_settings as app_settings

USER_MODEL = get_user_model()

__all__ = ["BaseAuthDirective", "IsAuthenticated", "HasPermission", "IsVerified", "TokenRequired"]


class BaseAuthDirective(ABC):
    @abstractmethod
    def resolve_permission(
        self,
        user: Union[USER_MODEL, AnonymousUser],
        source: Any,
        info: Info,
        args: list,
        kwargs: dict,
    ) -> Optional[GQLAuthError]:
        ...


@strawberry.schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
    ],
    description="This field requires a JWT token, this token will be used to find the user object.",
)
class TokenRequired(BaseAuthDirective):
    def resolve_permission(
        self,
        user: Union[USER_MODEL, AnonymousUser],
        source: Any,
        info: Info,
        args: list,
        kwargs: dict,
    ) -> Optional[GQLAuthError]:
        token = app_settings.JWT_TOKEN_FINDER(info)
        try:
            token_type = TokenType.from_token(token)
        except PyJWTError:  # raised by python-jwt
            return GQLAuthError(code=GQLAuthErrors.INVALID_TOKEN)

        except TokenExpired:
            return GQLAuthError(code=GQLAuthErrors.EXPIRED_TOKEN)
        user = token_type.get_user_instance()
        info.context.user = user
        return None


@strawberry.schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
    ],
    description="This field requires authentication",
)
class IsAuthenticated(BaseAuthDirective):
    def resolve_permission(self, user: USER_MODEL, source: Any, info: Info, *args, **kwargs):
        if not user.is_authenticated:
            return GQLAuthError(code=GQLAuthErrors.UNAUTHENTICATED)
        return None


@strawberry.schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
    ],
    description="This field requires the user to be verified",
)
class IsVerified(BaseAuthDirective):
    def resolve_permission(self, user: USER_MODEL, source: Any, info: Info, *args, **kwargs):
        if (status := get_status(user)) and status.verified:
            return None
        return GQLAuthError(code=GQLAuthErrors.NOT_VERIFIED)


@strawberry.schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
    ],
    description="This field requires a certain permissions to be resolved.",
)
class HasPermission(BaseAuthDirective):
    permissions: strawberry.Private[List[str]]

    def resolve_permission(self, user: USER_MODEL, source: Any, info: Info, *args, **kwargs):
        for permission in self.permissions:
            if not user.has_perm(permission):
                return GQLAuthError(
                    code=GQLAuthErrors.NO_SUFFICIENT_PERMISSIONS,
                    message=_(
                        f"User {user.first_name or getattr(user, user.USERNAME_FIELD, None)}, has not sufficient permissions for {info.path.key}"
                    ),
                )
        return None