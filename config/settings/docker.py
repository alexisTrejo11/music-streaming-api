"""
Settings for running the app inside Docker Compose (local stack).

Uses PostgreSQL and Redis from compose service hostnames via env vars.
"""

from decouple import config
import dj_database_url

from .development import *

DATABASES = {
    "default": dj_database_url.config(
        default=config(
            "DATABASE_URL",
            default="postgresql://music:music@postgres:5432/music_db",
        ),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Debug toolbar expects host-browser IPs; disable it in containers.
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]
MIDDLEWARE = [m for m in MIDDLEWARE if "debug_toolbar" not in m]

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", default="localhost,127.0.0.1,web"
).split(",")
