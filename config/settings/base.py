"""
Base settings - common configuration for both development and production
"""
from pathlib import Path
from decouple import config, Csv

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------- Security ----------
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())

# ---------- Applications ----------
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'channels',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.products',
    'apps.customer',
    'apps.order',
    'apps.cart',
    'apps.payment',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------- Middleware ----------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # for multi-language support
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ---------- URLs & WSGI/ASGI ----------
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ---------- Django Channels ----------
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}
# For production with Redis:
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             'hosts': [('127.0.0.1', 6379)],
#         },
#     },
# }

# ---------- Templates ----------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'apps.cart.context_processors.cart',
            ],
        },
    },
]

# ---------- Password Validation ----------
AUTH_PASSWORD_VALIDATORS = [
    {
        # Lower the minimum length requirement to 6
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
    # REMOVE or comment out CommonPasswordValidator and NumericPasswordValidator
    # to allow numeric PINs like "123456" or "987654"
]

# ---------- Internationalization ----------
LANGUAGE_CODE = 'en'
TIME_ZONE = 'Asia/Phnom_Penh'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('km', 'ខ្មែរ'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# ---------- Custom User Model ----------
# Important: set your custom user model here if using one
AUTH_USER_MODEL = 'accounts.User'

# ---------- Static & Media ----------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ---------- Default ----------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------- Telegram Notifications ----------
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_CHAT_ID = config('TELEGRAM_CHAT_ID', default='')
TELEGRAM_TOPIC_ID = config('TELEGRAM_TOPIC_ID', default='', cast=lambda v: int(v) if v else None)

# ---------- Bakong (for payments app in a later phase) ----------
BAKONG_API_TOKEN = config('BAKONG_TOKEN', default='')
BAKONG_MERCHANT_ID = config('BAKONG_ACCOUNT', default='')
BAKONG_MERCHANT_NAME = config('MERCHANT_NAME', default='Online Shop')
BAKONG_MERCHANT_CITY = config('MERCHANT_CITY', default='Phnom Penh')
BAKONG_CURRENCY = config('BAKONG_CURRENCY', default='USD')

# ---------- Authentication ----------
LOGIN_URL = 'accounts:login'              # ទំព័រ login
LOGIN_REDIRECT_URL = 'accounts:profile'   # បន្ទាប់ login ទៅណា
LOGOUT_REDIRECT_URL = 'accounts:login'    # បន្ទាប់ logout ទៅណា

# ---------- Email ----------
DEFAULT_FROM_EMAIL = 'noreply@eshop.com'

# បិទ quoted-printable encoding ដើម្បីឱ្យ URL មិន break
import email.charset
email.charset.add_charset('utf-8', email.charset.SHORTEST, None, 'utf-8')