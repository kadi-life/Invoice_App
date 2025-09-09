from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-)pzbpjk*m#@$=9^izz1bbg8i-&t*ejy4=iwhqs&l)_qpi3r-ny'

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.vercel.app']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'users',
    'quotations',
    'invoices',
    'storages',   # ✅ add django-storages
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # serves static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.CacheControlMiddleware',
]

# Add Whitenoise Middleware settings
WHITENOISE_USE_FINDERS = True
WHITENOISE_ROOT = STATIC_ROOT
WHITENOISE_MAX_AGE = 31536000  # 1 year in seconds

ROOT_URLCONF = 'invoice_project.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'invoice_project.wsgi.application'

# --------------------
# DATABASE
# --------------------
NEON_DATABASE_URL = "postgresql://neondb_owner:npg_xsSl9Xehk1qR@ep-tiny-haze-adklh2w6-pooler.c-2.us-east-1.aws.neon.tech/Invoicer_App%20DB?sslmode=require&channel_binding=require"

DATABASES = {
    'default': dj_database_url.config(
        default=NEON_DATABASE_URL if os.environ.get('VERCEL_ENV') else f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# --------------------
# PASSWORD VALIDATORS
# --------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# --------------------
# INTERNATIONALIZATION
# --------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --------------------
# STATIC FILES
# --------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'  # ✅ fix for Vercel

# --------------------
# MEDIA FILES (Supabase S3)
# --------------------
# Always use S3 storage in production (Vercel)
if not DEBUG or os.environ.get('VERCEL_ENV'):
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "media")
    AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "eu-north-1")
    AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", "https://mujgzkhcibgoqxjxlhhi.storage.supabase.co/storage/v1/s3")
    AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN", "mujgzkhcibgoqxjxlhhi.storage.supabase.co")
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'public-read'
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# --------------------
# DEFAULT PRIMARY KEY
# --------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------
# AUTH SETTINGS
# --------------------
AUTH_USER_MODEL = 'users.CustomUser'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'
LOGIN_URL = '/login/'

# --------------------
# CRISPY FORMS
# --------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# --------------------
# VAT & EMAIL
# --------------------
VAT_PERCENTAGE = 7.5
DEFAULT_FROM_EMAIL = 'no-reply@example.com'

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
