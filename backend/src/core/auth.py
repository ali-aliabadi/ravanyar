"""Bearer-token auth. `consented` is the NinjaAPI default, so every route is closed unless it
says otherwise (SPEC-0001)."""

from django.http import HttpRequest
from django.utils import timezone
from ninja.security import HttpBearer

from core.errors import ConsentRequiredError
from core.models import AuthSession
from core.services import has_current_consent, token_hash


class Bearer(HttpBearer):
    """A live session on an active account. For routes a person without consent still needs."""

    def authenticate(self, request: HttpRequest, token: str) -> AuthSession | None:
        return (
            AuthSession.objects.select_related("account")
            .filter(
                token_hash=token_hash(token),
                revoked_at=None,
                expires_at__gt=timezone.now(),
                account__is_active=True,
            )
            .first()
        )


class ConsentedBearer(Bearer):
    """Bearer, plus the current terms and privacy versions accepted and not withdrawn."""

    def authenticate(self, request: HttpRequest, token: str) -> AuthSession | None:
        session = super().authenticate(request, token)
        if session is not None and not has_current_consent(session.account):
            raise ConsentRequiredError
        return session


bearer = Bearer()
consented = ConsentedBearer()


def current(request: HttpRequest) -> AuthSession:
    session = request.auth  # type: ignore[attr-defined]  # set by ninja after authenticate()
    if not isinstance(session, AuthSession):
        raise TypeError("route has no session auth")
    return session
