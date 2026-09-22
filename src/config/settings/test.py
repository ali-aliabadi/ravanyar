"""Test settings. Integration tests override DATABASES with a testcontainers Postgres."""

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
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
