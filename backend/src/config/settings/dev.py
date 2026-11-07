"""Local development. Never used in CI or production."""

import hashlib

from .base import *
from .base import env

DEBUG = True
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-not-a-real-secret")
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Fixed so a local database survives restarts; derived, so no key-shaped literal is committed.
MASTER_KEY = hashlib.sha256(b"dev-only master key").digest()
BLIND_INDEX_KEY = hashlib.sha256(b"dev-only blind-index key").digest()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "core",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
