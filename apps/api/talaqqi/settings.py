"""Talaqqi API settings. Environment-driven; safe defaults for local development."""
from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent          # apps/api
REPO_ROOT = BASE_DIR.parent.parent                          # repo root
for p in (str(REPO_ROOT), str(BASE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, "dev-only-insecure-secret-change-me"),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    DATABASE_URL=(str, "postgres://talaqqi_app:talaqqi_dev@localhost:5432/talaqqi"),
    REDIS_URL=(str, "redis://localhost:6379/0"),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000", "http://127.0.0.1:3000"]),
    DEFAULT_LANGUAGE=(str, "ar"),
)
environ.Env.read_env(str(REPO_ROOT / ".env"))

DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    "services.common",
    "services.identity",
    "services.tenants",
    "services.rbac",
    "services.audit",
    "services.quran",
    "services.people",
    "services.hifz",
    "services.finance",
    "services.ai",
    "services.reading",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "services.common.middleware.RequestIdMiddleware",
    "services.common.middleware.TenantContextMiddleware",
]

ROOT_URLCONF = "talaqqi.urls"
WSGI_APPLICATION = "talaqqi.wsgi.application"
ASGI_APPLICATION = "talaqqi.asgi.application"

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["TEST"] = {"NAME": "talaqqi_test"}

AUTH_USER_MODEL = "identity.Account"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = env("DEFAULT_LANGUAGE")   # Arabic is the platform default; English supported
LANGUAGES = [("ar", "العربية"), ("en", "English")]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "services.common.pagination.CursorOrPagePagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend",
                                "rest_framework.filters.SearchFilter", "rest_framework.filters.OrderingFilter"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "services.common.exceptions.exception_handler",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"] + (["rest_framework.renderers.BrowsableAPIRenderer"] if DEBUG else []),
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.UserRateThrottle", "rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"user": "600/min", "anon": "60/min", "login": "20/min", "signup": "10/hour"},
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "sub",
}

TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True, "OPTIONS": {}}]  # drf-spectacular Redoc page

# AI is optional. "null" (default) keeps every AI endpoint answering 503; "openai" enables the adapter.
AI_PROVIDER = env.str("AI_PROVIDER", default="null")
OPENAI_API_KEY = env.str("OPENAI_API_KEY", default="")
OPENAI_MODEL = env.str("OPENAI_MODEL", default="gpt-4o-mini")
OPENAI_ASR_MODEL = env.str("OPENAI_ASR_MODEL", default="gpt-4o-mini-transcribe")
OPENAI_BASE_URL = env.str("OPENAI_BASE_URL", default="https://api.openai.com/v1")
ASR_DAILY_QUOTA = env.int("ASR_DAILY_QUOTA", default=60)   # recitation checks per account per day (cost control)

SPECTACULAR_SETTINGS = {
    "TITLE": "Talaqqi API",
    "DESCRIPTION": "Open-source operating system for Quran education. Arabic-first, multi-tenant, capability-enforced.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[o for o in CORS_ALLOWED_ORIGINS if o.startswith("https://")])

# Behind Caddy (TLS terminated at the proxy)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
CORS_ALLOW_HEADERS = ["authorization", "content-type", "x-tenant", "x-request-id", "idempotency-key", "accept-language"]

CELERY_BROKER_URL = env("REDIS_URL")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=DEBUG)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "services.common.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

TALAQQI = {
    "DEFAULT_RIWAYAH": "hafs_asim",
    "DEFAULT_MUSHAF_TYPE": "madani_15_line",
    "QURAN_TEXT_ATTRIBUTION": "Quran text: Tanzil Project — https://tanzil.net",
    # Reciter registry: per-ayah MP3 streamed from the host below (pattern {surah:03}{ayah:03}.mp3). Operators may replace it
    # with their own licensed host via AUDIO_RECITERS_JSON; Talaqqi bundles and redistributes no audio.
    "RECITERS": env.json("AUDIO_RECITERS_JSON", default=[
        {"key": "alafasy", "name_ar": "مشاري راشد العفاسي", "name_en": "Mishary Alafasy", "base": "https://everyayah.com/data/Alafasy_128kbps/"},
        {"key": "husary", "name_ar": "محمود خليل الحصري", "name_en": "Mahmoud Al-Husary", "base": "https://everyayah.com/data/Husary_128kbps/"},
        {"key": "abdulbasit", "name_ar": "عبد الباسط عبد الصمد (مرتّل)", "name_en": "Abdul Basit (Murattal)", "base": "https://everyayah.com/data/Abdul_Basit_Murattal_192kbps/"},
        {"key": "minshawi", "name_ar": "محمد صديق المنشاوي (مرتّل)", "name_en": "Al-Minshawi (Murattal)", "base": "https://everyayah.com/data/Minshawy_Murattal_128kbps/"},
        {"key": "sudais", "name_ar": "عبد الرحمن السديس", "name_en": "Abdurrahman As-Sudais", "base": "https://everyayah.com/data/Abdurrahmaan_As-Sudais_192kbps/"},
        {"key": "ajmi", "name_ar": "أحمد بن علي العجمي", "name_en": "Ahmed Al-Ajmi", "base": "https://everyayah.com/data/Ahmed_ibn_Ali_al-Ajamy_128kbps_ketaballah.net/"},
    ]),
    "AUDIO_PATTERN": "{surah:03d}{ayah:03d}.mp3",
    "AUDIO_SOURCE_NOTE": "Audio is streamed from everyayah.com (Verse-by-verse recitations). Talaqqi does not host or redistribute recordings.",
}
