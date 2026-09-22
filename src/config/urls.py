from django.urls import path
from ninja import NinjaAPI

from core.api import router as core_router

api = NinjaAPI(title="core", version="0.1.0")
api.add_router("", core_router)

urlpatterns = [path("api/", api.urls)]
