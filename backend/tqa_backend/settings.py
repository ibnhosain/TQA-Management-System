"""
TQA-MS — Django Settings (Environment-variable ভিত্তিক)

কিভাবে কাজ করে:
  • Local এ:    backend/.env ফাইল থেকে value পড়ে (python-dotenv)
  • Hosting এ:  Railway/Render dashboard এর Environment Variables থেকে পড়ে
  • কোনোটাই না থাকলে: default value (শুধু local development এর জন্য নিরাপদ)
"""
import os
from pathlib import Path
from datetime import timedelta

from django.contrib.admin import AdminSite

AdminSite.site_header = "তারবিয়াতুল কুরআন একাডেমি"
AdminSite.site_title = "TQA প্রশাসন"
AdminSite.index_title = "স্বাগতম"

BASE_DIR = Path(__file__).resolve().parent.parent

# ── .env ফাইল লোড (থাকলে) ─────────────────────────────────────────
# Hosting এ .env থাকে না — তখন dashboard এর env var সরাসরি os.environ এ থাকে
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# ── Security ──────────────────────────────────────────────────────
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-local-dev-only-key"  # শুধু local এ — production এ env var দিন
)

# DEBUG: env এ "True" লিখলে চালু, না লিখলে বন্ধ (production-safe default)
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

# ALLOWED_HOSTS: কমা দিয়ে আলাদা করে দিন, যেমন: tarbiyatulquran.org,api.tarbiyatulquran.org
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]
# Render internal health check
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # TQA additions
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'core',
    'django_celery_beat',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Production এ static files serve করে
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tqa_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tqa_backend.wsgi.application'

# ── Database ──────────────────────────────────────────────────────
# DATABASE_URL দিলে (Railway/Render PostgreSQL) সেটা ব্যবহার হবে,
# না দিলে local SQLite
DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===== TQA-MS =====
AUTH_USER_MODEL = "core.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    # Brute-force ঠেকাতে rate limiting:
    # লগইন না করা অবস্থায় (যেমন: login চেষ্টা) মিনিটে সর্বোচ্চ ২০ বার,
    # লগইন করা user মিনিটে ২৪০ বার — স্বাভাবিক ব্যবহারে কেউ টেরও পাবে না
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/min",
        "user": "240/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
}

# ── CORS ──────────────────────────────────────────────────────────
# CORS_ALLOW_ALL_ORIGINS=True হলে সব origin অনুমতি পাবে (public API-র জন্য)
CORS_ALLOW_ALL_ORIGINS = os.environ.get("CORS_ALLOW_ALL_ORIGINS", "False").lower() in ("true", "1", "yes")

# Frontend এর URL — কমা দিয়ে একাধিক দেওয়া যায়
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get(
        "CORS_ALLOWED_ORIGINS", "http://localhost:5173"
    ).split(",")
    if o.strip()
]

# CSRF (production এ https domain লাগে)
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"  # collectstatic এখানে জমা করবে

# ── Cloud Storage (Cloudinary) ────────────────────────────────────
# CLOUDINARY_URL থাকলে সব uploaded file Cloudinary তে যাবে (permanent)
# না থাকলে local filesystem এ (development)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
# cloudinary package শুধু uploader হিসেবে ব্যবহার হয় — storage backend না
# CLOUDINARY_URL env var থেকে cloudinary package নিজেই config নেয়

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": "ERROR"},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}

LANGUAGE_CODE = "bn"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Celery / Redis ────────────────────────────────────────────────
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_TIMEZONE = 'Asia/Dhaka'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ── Production security (DEBUG বন্ধ থাকলে স্বয়ংক্রিয়) ─────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
