"""Production. Every secret comes from the environment and fails loudly when absent."""

from django.core.exceptions import ImproperlyConfigured

from core.crypto import load_key, normalise_phone

from .base import *
from .base import BASE_DIR, CONSENT_VERSIONS, env

DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS").split(",")

# ADR 0004: both keys live outside the database; a missing or malformed key stops startup.
MASTER_KEY = load_key("RAVANYAR_MASTER_KEY", env("RAVANYAR_MASTER_KEY"))
BLIND_INDEX_KEY = load_key("RAVANYAR_BLIND_INDEX_KEY", env("RAVANYAR_BLIND_INDEX_KEY"))
KAVENEGAR_API_KEY = env("KAVENEGAR_API_KEY")

# Pre-launch deployments (AGENTS.md §1) hold no real users, so draft consent texts are allowed.
PRELAUNCH = env("RAVANYAR_PRELAUNCH", "") == "1"
if not PRELAUNCH and any("-draft-" in version for version in CONSENT_VERSIONS.values()):
    raise ImproperlyConfigured("placeholder consent versions cannot run in production (SPEC-0001)")

# SPEC-0002: staging test sign-in. Fails closed: refused unless RAVANYAR_PRELAUNCH=1, so the
# launch server, which must not set it, cannot run with a fixed sign-in code.
TEST_PHONES = frozenset(
    normalise_phone(raw) for raw in env("RAVANYAR_TEST_PHONES", "").split(",") if raw.strip()
)
TEST_CODE = env("RAVANYAR_TEST_CODE", "")
if TEST_PHONES and not PRELAUNCH:
    raise ImproperlyConfigured("RAVANYAR_TEST_PHONES needs RAVANYAR_PRELAUNCH=1 (SPEC-0002)")
if TEST_PHONES and not (len(TEST_CODE) == 6 and TEST_CODE.isascii() and TEST_CODE.isdigit()):
    raise ImproperlyConfigured("RAVANYAR_TEST_CODE must be 6 digits (SPEC-0002)")

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

STATIC_ROOT = BASE_DIR / "static"
STATIC_URL = "/api/static/"

# nginx terminates TLS and talks plain HTTP to the app on localhost.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
