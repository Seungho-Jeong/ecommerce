import os

from .base import *

DEBUG = True
SECRET_KEY = os.environ.get("SECRET_KEY", "ecommerce")

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
INTERNAL_IPS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django_extensions",
    "debug_toolbar",
] + INSTALLED_APPS

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
