import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

LOGIN_REDIRECT_URL = '/'

AUTH_USER_MODEL = "events.CustomAdmin"

# SECURITY WARNING: Keep the secret key used in production secret!
SECRET_KEY = 'your-secret-key'

# SECURITY WARNING: Don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'events',  # Replace with your actual app name
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eventx.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'events' / 'templates',  # Our app templates first
            BASE_DIR / 'templates',
        ],
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

WSGI_APPLICATION = 'eventx.wsgi.application'

# **Updated to Use SQLite**
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / "db.sqlite3",
    }
}

# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# **Static files configuration**
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# Ensure the static folder exists
os.makedirs(BASE_DIR / "static", exist_ok=True)

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Ensure the media folder exists
os.makedirs(MEDIA_ROOT, exist_ok=True)

# **Logging Configuration**
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# Ensure the logs directory exists
os.makedirs(BASE_DIR / "logs", exist_ok=True)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Razorpay Configuration
RAZORPAY_KEY_ID = 'rzp_test_R00Zy6ve0bPcx1'  # Replace with your test key
RAZORPAY_KEY_SECRET = 'XGPWyeenCcs8pRDhcFEz2WOl'  # Replace with your test secret
RAZORPAY_CURRENCY = 'INR'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # For Gmail
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'pb132001@gmail.com'  # Replace with your Gmail address
EMAIL_HOST_PASSWORD = 'lgqp xlhr ekeg snmo'  # Replace with your Gmail app password
