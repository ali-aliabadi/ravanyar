"""Test settings. Integration tests override DATABASES with a testcontainers Postgres."""

import os

from .base import *

DEBUG = False
SECRET_KEY = "test-only-not-a-real-secret"  # noqa: S105
ALLOWED_HOSTS = ["testserver"]

# Overridden at runtime by the postgres fixture; unit tests never touch it.
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
# Fresh per run: nothing key-shaped in the repo, and no test depends on a fixed key.
MASTER_KEY = os.urandom(32)
BLIND_INDEX_KEY = os.urandom(32)

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
