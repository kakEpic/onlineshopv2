"""
Development settings - PostgreSQL + DEBUG=True
"""
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# SQLite (for development)
DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Email Configuration (for development - console backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# For production, use:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = config('EMAIL_HOST')
# EMAIL_PORT = config('EMAIL_PORT', cast=int)
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = config('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# File-based email backend - write emails to files for inspection
EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'

# Django Debug Toolbar
INTERNAL_IPS = ['127.0.0.1']