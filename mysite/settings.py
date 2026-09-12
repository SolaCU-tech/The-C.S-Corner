"""
Django settings for mysite project.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
# In production, set the DJANGO_SECRET_KEY environment variable.
# This fallback is fine for local development only.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-vq&we$urrgpsua8do+f-rw9xhxn%@^uvf-k=joxy_%i_p48%g5')

# SECURITY WARNING: don't run with debug turned on in production!
# Set DEBUG=False as an environment variable in production.
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'solabomi.pythonanywhere.com']

extra_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if extra_hosts:
    ALLOWED_HOSTS += [h.strip() for h in extra_hosts.split(',') if h.strip()]

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [f'https://{host}' for host in ALLOWED_HOSTS
                         if host not in ('localhost', '127.0.0.1')]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'cloudinary',
    'blog'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'blog.context_processors.cs_tidbit',
                'blog.context_processors.tech_news',
                'blog.context_processors.nav_profile_stats',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# Uses Postgres in production via DATABASE_URL (e.g. from Neon), and
# falls back to local SQLite automatically when that isn't set, so
# local development needs zero extra configuration.

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL, conn_max_age=600, conn_health_checks=True,
            ssl_require=True)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Lagos'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
# WhiteNoise serves these directly from the app in production, no
# separate static file host needed.

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (user-uploaded content, e.g. post images, avatars)
# https://docs.djangoproject.com/en/5.2/topics/files/
# Stored on Cloudinary in production (so uploads survive redeploys),
# and saved to the local media/ folder automatically otherwise.

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')

if CLOUDINARY_URL:
    STORAGES = {
        'default': {
            'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
    DEFAULT_FILE_STORAGE = STORAGES['default']['BACKEND']
else:
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
    DEFAULT_FILE_STORAGE = STORAGES['default']['BACKEND']

# django-cloudinary-storage's collectstatic override still reads this
# legacy setting directly, so it must exist even though STORAGES above
# is the modern (and actually used) way to configure it.
STATICFILES_STORAGE = STORAGES['staticfiles']['BACKEND']

# WhiteNoiseMiddleware (added above) serves these files efficiently at
# runtime — including its own gzip/brotli compression on the fly — so
# a special collectstatic storage backend isn't needed for that.
WHITENOISE_USE_FINDERS = DEBUG

# Files here (favicon, apple-touch-icon, manifest, etc.) are served
# directly at the site root — e.g. /favicon.ico — rather than under
# /static/, which is what browsers and phones actually expect for these.
WHITENOISE_ROOT = BASE_DIR / 'public'

# WhiteNoise uses its own internal media-type map (not Python's stdlib
# mimetypes module) and doesn't know .webmanifest by default, so it
# would otherwise serve it as generic application/octet-stream.
WHITENOISE_MIMETYPES = {
    '.webmanifest': 'application/manifest+json',
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth redirects
LOGIN_REDIRECT_URL = 'post_list'
LOGOUT_REDIRECT_URL = 'post_list'
LOGIN_URL = 'login'

# Production security hardening — only active when DEBUG is off, so
# local HTTP development is never affected.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7  # 1 week to start; raise once stable
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# By default, Django only prints request-handling tracebacks to the
# console when DEBUG=True — otherwise it tries to email admins, which
# we haven't configured, so errors vanish silently. This makes sure
# unhandled exceptions always show up in Render's log stream.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
