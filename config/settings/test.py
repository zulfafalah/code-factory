"""
With these settings, tests run faster.
"""

from .base import *  # noqa: F403
from .base import TEMPLATES
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="yOnVbxTdq2F2UjcsDFUEK7i09T123L3G38k4xjsVVBZ8mSowOFdc18bcaemDwF1D",
)

# DATABASES
# ------------------------------------------------------------------------------
# Use SQLite for tests when DATABASE_URL is not available or empty
try:
    # Try to get DATABASE_URL, but provide fallback if empty or not set
    database_url = env("DATABASE_URL", default="")
    if database_url:
        DATABASES = {"default": env.db("DATABASE_URL")}
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        }
except (KeyError, ValueError):
    # Fallback to SQLite if there's any issue with DATABASE_URL
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

DATABASES["default"]["ATOMIC_REQUESTS"] = True

# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORD
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# CELERY
# ------------------------------------------------------------------------------
# Use memory backend for tests when CELERY_BROKER_URL is not available
try:
    celery_broker_url = env("CELERY_BROKER_URL", default="")
    if celery_broker_url:
        CELERY_BROKER_URL = celery_broker_url
    else:
        CELERY_BROKER_URL = "memory://"
        CELERY_TASK_ALWAYS_EAGER = True
        CELERY_TASK_EAGER_PROPAGATES = True
except (KeyError, ValueError):
    CELERY_BROKER_URL = "memory://"
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore[index]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "http://media.testserver"
