"""
Production settings - Vercel + Render PostgreSQL
"""
from .base import *

DEBUG = False

# =========================
# Database - Render PostgreSQL
# =========================
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=0,
        ssl_require=True,
    )
}

# =========================
# Hosts
# =========================
ALLOWED_HOSTS = [
    'onlineshopv2.vercel.app',
    '.vercel.app',
    'localhost',
    '127.0.0.1',
]

# =========================
# CSRF
# =========================
CSRF_TRUSTED_ORIGINS = [
    'https://onlineshopv2.vercel.app',
]

# =========================
# Security
# =========================
SECURE_SSL_REDIRECT = True

SECURE_PROXY_SSL_HEADER = (
    'HTTP_X_FORWARDED_PROTO',
    'https',
)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# =========================
# Static files - WhiteNoise
# =========================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.'
            'CompressedManifestStaticFilesStorage'
        ),
    },
}

# =========================
# Email
# =========================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

WHITENOISE_MANIFEST_STRICT = False