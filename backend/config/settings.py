from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env", overwrite=False)

SECRET_KEY = env("SECRET_KEY", default="dev-only-insecure-key-change-me")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"] if DEBUG else [])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "rest_framework_simplejwt",
    "apps.accounts",
    "apps.routes",
    "apps.activities",
    "apps.leagues",
    "apps.training",
    "apps.integrations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

DATABASES = {"default": env.db("DATABASE_URL", default="postgis://stryde:stryde@localhost:5432/stryde")}
DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"

AUTH_USER_MODEL = "accounts.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DATA_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024  # FIT/GPX uploads

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_THROTTLE_RATES": {"uploads": "60/hour"},
}
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(hours=1), "REFRESH_TOKEN_LIFETIME": timedelta(days=60)}

# Celery (Redis). In tests and simple local dev, run tasks inline.
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = None
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BEAT_SCHEDULE = {
    "close-seasons": {"task": "apps.leagues.tasks.close_due_seasons", "schedule": 3600.0},
}

# Encryption key for watch-platform tokens. Set FIELD_ENCRYPTION_KEY in production (Fernet key).
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY", default="")

# Watch providers: client ids/secrets arrive after each developer program approves the app.
PROVIDERS = {
    "garmin": {"client_id": env("GARMIN_CLIENT_ID", default=""), "client_secret": env("GARMIN_CLIENT_SECRET", default="")},
    "polar": {"client_id": env("POLAR_CLIENT_ID", default=""), "client_secret": env("POLAR_CLIENT_SECRET", default="")},
    "coros": {"client_id": env("COROS_CLIENT_ID", default=""), "client_secret": env("COROS_CLIENT_SECRET", default="")},
    "suunto": {"client_id": env("SUUNTO_CLIENT_ID", default=""), "client_secret": env("SUUNTO_CLIENT_SECRET", default="")},
}
WEBHOOK_SECRET = env("WEBHOOK_SECRET", default="dev-webhook-secret")
PUBLIC_BASE_URL = env("PUBLIC_BASE_URL", default="http://localhost:8000")
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

if dsn := env("SENTRY_DSN", default=""):
    import sentry_sdk

    sentry_sdk.init(dsn=dsn, traces_sample_rate=0.1)

LOGGING = {
    "version": 1,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
