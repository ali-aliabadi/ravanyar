from django.http import HttpRequest, HttpResponse
from django.urls import path
from ninja import NinjaAPI
from ninja.errors import ValidationError

from core.api import router as core_router
from core.auth import consented
from core.errors import ServiceError

# Default-deny: every route requires a session with current consent unless it opts out.
api = NinjaAPI(title="core", version="0.1.0", auth=consented)
api.add_router("", core_router)


@api.exception_handler(ServiceError)
def service_error(request: HttpRequest, exc: ServiceError) -> HttpResponse:
    return api.create_response(request, {"detail": exc.code}, status=exc.status)


@api.exception_handler(ValidationError)
def invalid(request: HttpRequest, exc: ValidationError) -> HttpResponse:
    """Pydantic echoes the rejected input; a rejected phone number must not come back."""
    detail = [{"loc": e.get("loc"), "msg": e.get("msg")} for e in exc.errors]
    return api.create_response(request, {"detail": detail}, status=422)


urlpatterns = [path("api/", api.urls)]
