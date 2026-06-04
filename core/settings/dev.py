"""
PaaMoja — Development Settings
Uses SQLite, DEBUG on, no real M-Pesa keys needed.
"""

from .base import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Allow all hosts locally
ALLOWED_HOSTS = ['*']

# Django Debug Toolbar (optional — install separately)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
# INTERNAL_IPS = ['127.0.0.1']

# Override static storage to simpler version in dev
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'