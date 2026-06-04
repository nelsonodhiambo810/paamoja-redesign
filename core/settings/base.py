"""
PaaMoja Initiative — Base Settings
Shared across dev, staging, and production.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─── SECURITY ────────────────────────────────────────────────────────────────

SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Used in team alert emails to link directly to the CMS record
SITE_URL = os.environ.get('SITE_URL', 'https://paamoja.org')

# ─── APPLICATIONS ─────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    # Third-party
    'corsheaders',
    # Local
    'website',
    'mpesa',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # Static files in production
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'website' / 'templates', BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'

# ─── PASSWORD VALIDATION ──────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── INTERNATIONALISATION ─────────────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# ─── STATIC & MEDIA ───────────────────────────────────────────────────────────

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── JAZZMIN CMS ──────────────────────────────────────────────────────────────

JAZZMIN_SETTINGS = {
    "site_title": "PaaMoja CMS",
    "site_header": "PaaMoja",
    "site_brand": "PaaMoja Administration",
    "welcome_sign": "Welcome to the PaaMoja Content Portal",
    "copyright": "PaaMoja Initiative Ltd",
    "show_ui_builder": True,
    
    "order_with_respect_to": [
        "website.Program",
        "website.NewsUpdate",
        "website.SuccessStory",
        "website.Donation",
    ],

    "custom_links": {
        "website": [{
            "name": "📊 Live Dashboard",
            "url":  "/admin/dashboard/",
            "icon": "fas fa-chart-line",
        }]
    },
    
    "icons": {
        "website.Program":              "fas fa-hands-helping",
        "website.NewsUpdate":           "fas fa-newspaper",
        "website.SuccessStory":         "fas fa-star",
        "website.Donation":             "fas fa-hand-holding-usd",
        "website.VolunteerApplication": "fas fa-user-plus",
        "website.ImpactReport":         "fas fa-file-pdf",
        "website.ContactInquiry":       "fas fa-envelope",
        "website.NewsletterSubscriber": "fas fa-mail-bulk",
        "website.TeamMember":           "fas fa-users",
        "website.Milestone":            "fas fa-flag",
    },
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": "darkly",
}

# ─── M-PESA DARAJA ────────────────────────────────────────────────────────────

MPESA_ENVIRONMENT = os.environ.get('MPESA_ENVIRONMENT', 'sandbox')
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', '')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', '')
MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '174379')          # sandbox default
MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY', '')
MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL', '')

# ─── CORS ─────────────────────────────────────────────────────────────────────

_cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
CORS_ALLOWED_ORIGINS = _cors_origins.split(',') if _cors_origins else []