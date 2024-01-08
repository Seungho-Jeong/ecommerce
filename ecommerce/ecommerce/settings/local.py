import os

from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]
INTERNAL_IPS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django_extensions",
    "debug_toolbar",
] + INSTALLED_APPS

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
