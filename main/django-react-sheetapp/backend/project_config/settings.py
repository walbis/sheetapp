import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
import logging.config

# Base directory of the Django project (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file located in the project root (django-react-sheetapp/)
dotenv_path = BASE_DIR.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

# --- Security Settings ---
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'default-insecure-key-for-dev-only') # Provide a fallback for safety

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Hosts allowed to connect to this Django instance
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'backend', '0.0.0.0'] # Allow Docker service name, localhost, any host for dev

# --- Application Definition ---
INSTALLED_APPS = [
    # Django Core Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party Apps
    'rest_framework',
    'corsheaders',

    # Your Local Apps
    'app.apps.AppConfig', # Use AppConfig for clarity and potential setup (like signals)
]

MIDDLEWARE = [
    # CorsMiddleware should be placed high, especially before CommonMiddleware
    'corsheaders.middleware.CorsMiddleware',
    # Standard Django middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', # Handles session management
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', # Handles CSRF protection, crucial with session auth
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Associates user with request
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Root URL configuration module
ROOT_URLCONF = 'project_config.urls'

# Template configuration (if using Django templates)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], # Add template directories if needed
        'APP_DIRS': True, # Allows Django to find templates in app directories
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request', # Adds request object to template context
                'django.contrib.auth.context_processors.auth', # Adds user object
                'django.contrib.messages.context_processors.messages', # Adds messages framework
            ],
        },
    },
]

# WSGI application entry point
WSGI_APPLICATION = 'project_config.wsgi.application'


# --- Database Configuration ---
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'), # Default to SQLite if not set
        'NAME': os.environ.get('DB_NAME', BASE_DIR / 'db.sqlite3'), # Default to db.sqlite3 in backend/
        'USER': os.environ.get('DB_USER'), # Read from .env
        'PASSWORD': os.environ.get('DB_PASSWORD'), # Read from .env
        'HOST': os.environ.get('DB_HOST'), # Read from .env (e.g., 'db' for docker service)
        'PORT': os.environ.get('DB_PORT'), # Read from .env
    }
}
# Validate required DB env vars if using PostgreSQL
if DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    if not all([DATABASES['default'].get(k) for k in ['NAME', 'USER', 'PASSWORD', 'HOST', 'PORT']]):
        # This check helps catch configuration errors early during startup
        raise ValueError("Missing one or more required PostgreSQL environment variables (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)")


# --- Password Validation ---
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Custom User Model
AUTH_USER_MODEL = 'app.User' # Point to your custom User model in the 'app' application

# --- Internationalization ---
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC' # Use UTC for backend storage timezone consistency
USE_I18N = True # Enable Django's translation system
USE_TZ = True # Enable timezone-aware datetimes


# --- Static files (CSS, JavaScript, Images) ---
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = 'static/' # URL prefix for static files
# Define STATIC_ROOT for collectstatic command in production deployments
# STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField' # Modern default


# --- Django REST Framework Settings ---
# https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Use session authentication for browser-based interaction
        'rest_framework.authentication.SessionAuthentication',
        # Add TokenAuthentication or JWTAuthentication later if building a separate API client
        # 'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        # Default policy: Allow read-only access for anyone, require authentication for write actions
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        # More specific permissions will be set at the view level
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20, # Default number of items per page for paginated lists
    # Default exception handler provides standard DRF error responses
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}


# --- CORS (Cross-Origin Resource Sharing) Settings ---
# https://github.com/adamchainz/django-cors-headers
# Allow requests from the frontend development server origin
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
# Allow cookies (like sessionid and csrftoken) to be sent in cross-origin requests
CORS_ALLOW_CREDENTIALS = True


# --- CSRF (Cross-Site Request Forgery) Settings ---
# Required for session authentication safety with non-GET requests from JavaScript
# Ensure the CSRF cookie is accessible by JavaScript on the frontend's domain.
CSRF_COOKIE_HTTPONLY = False # Default is True, set to False to allow JS access
# Trust the frontend origin(s) for CSRF purposes
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
# SameSite setting for CSRF and Session cookies ('Lax' is generally recommended)
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'
# Use secure cookies in production (requires HTTPS)
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG


# --- Logging Configuration ---
# https://docs.djangoproject.com/en/4.2/topics/logging/
LOGGING_CONFIG = None # Disable default config to use dictConfig below
LOGLEVEL = os.environ.get('LOGLEVEL', 'info').upper() # Control log level via environment variable

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False, # Keep default loggers active unless explicitly overridden
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            # Include logger name for context
            'format': '%(levelname)s [%(name)s] %(message)s'
        },
    },
    'handlers': {
        'console': {
            # Log DEBUG level messages and higher only when DEBUG=True
            'level': 'DEBUG' if DEBUG else LOGLEVEL,
            'class': 'logging.StreamHandler', # Output logs to stderr/stdout
            'formatter': 'simple' # Use the simple log format
        },
        # Add file handlers or other handlers for production if needed
        # 'file': {
        #     'level': 'INFO',
        #     'class': 'logging.FileHandler',
        #     'filename': BASE_DIR.parent / 'logs/django.log', # Ensure logs directory exists
        #     'formatter': 'verbose',
        # },
    },
    'loggers': {
        # Django's base loggers
        'django': {
            'handlers': ['console'], # Send Django logs to console
            'level': 'INFO', # Avoid excessive Django internal logs unless needed
            'propagate': False, # Don't pass messages up to root logger
        },
        'django.db.backends': { # Control SQL query logging (can be very verbose)
            'handlers': ['console'],
            'level': 'INFO', # Set to DEBUG to see SQL queries
            'propagate': False,
        },
         'django.request': { # Log server errors (5xx) and potentially warnings (4xx)
            'handlers': ['console'],
            'level': 'WARNING', # Log 4xx and 5xx errors
            'propagate': False,
        },
         'django.security.csrf': { # Log CSRF validation failures
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Your application's logger
        'app': {
            'handlers': ['console'], # Send your app's logs to console
            'level': 'DEBUG' if DEBUG else 'INFO', # Control verbosity based on DEBUG setting
            'propagate': False, # Don't pass to root logger
        },
        # Example: Quieten down a noisy third-party library
        # 'noisy_library': {
        #     'handlers': ['console'],
        #     'level': 'WARNING',
        #     'propagate': False,
        # },
    }
    # Optionally configure root logger as a catch-all if needed
    # 'root': {
    #     'handlers': ['console'],
    #     'level': 'WARNING',
    # },
})