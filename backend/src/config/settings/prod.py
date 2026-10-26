"""Production. Every secret comes from the environment and fails loudly when absent."""

from django.core.exceptions import ImproperlyConfigured

from core.crypto import load_key

from .base import *
from .base import CONSENT_VERSIONS, env

DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS").split(",")

# ADR 0004: both keys live outside the database; a missing or malformed key stops startup.
MASTER_KEY = load_key("RAVANYAR_MASTER_KEY", env("RAVANYAR_MASTER_KEY"))
BLIND_INDEX_KEY = load_key("RAVANYAR_BLIND_INDEX_KEY", env("RAVANYAR_BLIND_INDEX_KEY"))
KAVENEGAR_API_KEY = env("KAVENEGAR_API_KEY")

if any("-draft-" in version for version in CONSENT_VERSIONS.values()):
    raise ImproperlyConfigured("placeholder consent versions cannot run in production (SPEC-0001)")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
