# Django settings for codebro project.
#

import os

########### CHANGE THOSE SETTINGS ###############
APP_PATH = os.getenv("HOME") + "/code/codebro"
SRC_PATH = APP_PATH + "/src"
MAX_UPLOAD_SIZE = 104857600 # 100 MB maximum archive size
CACHE_PATH = APP_PATH + "/cache"
SQLITE_DB_PATH = APP_PATH + "/db.sqlite3"
CODEBRO_KEY = "c0d3Br0_k1ck_@$$"
CLANG_PARSE_OPTIONS = [ 
                        "-Wextra",
                        "-Wformat-security",
                        "-I/usr/lib/gcc/x86_64-unknown-linux-gnu/4.7.2/include",
                        "-I/usr/include/",
                       ]

########### CHANGE THOSE SETTINGS ###############

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('hugsy', 'hugsy@pyc.li'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': SQLITE_DB_PATH,                 # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

SECRET_KEY = CODEBRO_KEY

ROOT_URLCONF = 'codebro.urls'

WSGI_APPLICATION = 'codebro.wsgi.application'

TIME_ZONE = 'Australia/Melbourne'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_ROOT = ''

MEDIA_URL = ''

STATIC_ROOT = 'static/'

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    APP_PATH + "/static_local/",
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'dajaxice.finders.DajaxiceFinder',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)


TEMPLATE_DIRS = (
    APP_PATH+"/templates"
)

INSTALLED_APPS = (
    # 'django.contrib.auth',
    'django.contrib.contenttypes',
    # 'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dajaxice',
    'browser',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
            },

        }
}
