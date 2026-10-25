"""Settings shared by every environment. Environment-specific files import * from here."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]


def env(name: str, default: str | None = None) -> str:
    """Read a required environment variable. Fails loudly rather than defaulting in prod."""
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True
STATIC_URL = "static/"

# SPEC-0001. Accounts hold no plaintext identifier, so Django's User cannot be used (ADR 0004).
AUTH_USER_MODEL = "core.Account"

# The consent texts each version names. Publishing a new version means every account
# accepts it again before using the API. Draft versions refuse to start in production.
CONSENT_VERSIONS = {"terms": "terms-draft-0", "privacy": "privacy-draft-0"}

KAVENEGAR_API_KEY = os.environ.get("KAVENEGAR_API_KEY", "")
KAVENEGAR_TEMPLATE = os.environ.get("KAVENEGAR_TEMPLATE", "ravanyar-code")
