"""
Django settings for stacksync_manager project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'r-m(fq9l-$kji*@=20)#_vc!j&wvy@3+z9@fpzokeh^1t^iqme'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Mail settings
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = "mail@gmail.com"
EMAIL_HOST_PASSWORD = "password"

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'oauth',
    'groups',
    # 'djangosecure'
     'django_pg'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'djangosecure.middleware.SecurityMiddleware',
    'django.middleware.locale.LocaleMiddleware',
)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

ROOT_URLCONF = 'stacksync_manager.urls'

WSGI_APPLICATION = 'stacksync_manager.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'stacksync',
        'USER': 'stacksync_user',
        'PASSWORD': 'stacksync',
        'HOST': '123.123.123.123',
        'PORT': '5432',
    }
}

#Database manager
MANAGER_HOST = '123.123.123.123'
MANAGER_USER = 'stacksync_user'
MANAGER_PASS = 'stacksync'
MANAGER_PORT = '5432'
MANAGER_DATABASE = 'stacksync'

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGES = (
    ('es', 'Spanish'),
    ('en', 'English'),
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'conf', 'locale'),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'


# StackSync Settings

USER_TABLE = 'user1'
WORKSPACE_TABLE = 'workspace'
MEMBERSHIP_TABLE = 'workspace_user'

KEYSTONE_AUTH_URL = 'https://123.123.123.123:5000/v2.0'
#KEYSTONE_AUTH_URL = 'http://192.168.56.101:5000/v2.0'
KEYSTONE_MANAGEMENT_URL = 'https://123.123.123.123:35357/v2.0'
#KEYSTONE_MANAGEMENT_URL = 'http://192.168.56.101:35357/v2.0'
KEYSTONE_TENANT = 'stacksync'
KEYSTONE_ADMIN_USER = 'stacksync_admin'
KEYSTONE_ADMIN_PASSWORD = 'secret'
SWIFT_URL = 'https://123.123.123.123:8080/v1'
#SWIFT_URL = 'http://192.168.56.101:8080/v1'

# Administration settings #
# To change visualization and insertion of values of the DB in bytes to MBy #
B_2_MBY = 1048576

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)
