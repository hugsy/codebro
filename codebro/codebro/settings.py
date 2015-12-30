#
# Django settings for codebro project.
#

from unipath import Path


APP_PATH         = Path(__file__).ancestor(2)
SRC_PATH         = APP_PATH.child("sources")
CACHE_PATH       = APP_PATH.child("cache")
DB_PATH          = APP_PATH.child("db").child("codebro.sqlite3")
MAX_UPLOAD_SIZE  = 100 * 1024 * 1024
DEBUG            = True
TEMPLATE_DEBUG   = DEBUG
SECRET_KEY       = "c0d3Br0_k1ck_@$$"
ROOT_URLCONF     = "codebro.urls"
WSGI_APPLICATION = "codebro.wsgi.application"
TIME_ZONE        = "Europe/Madrid"
LANGUAGE_CODE    = "es"
SITE_ID          = 1
USE_I18N         = True
USE_L10N         = True
USE_TZ           = True
MEDIA_ROOT       = APP_PATH.child("media")
MEDIA_URL        = "/media/"
STATIC_ROOT      = APP_PATH.child("static")
STATIC_URL       = "/static/"
ADMINS           = ( ("admin", "devnull@libcrack.so"), )
MANAGERS         = ADMINS
TEMPLATE_DIRS    = ( APP_PATH.child("templates"), )
STATICFILES_DIRS = ( APP_PATH.child("assets"), )
CACHED_SVG_FMT   = "project#%d-fromFunc#%d-fu%d-%s@depth#%d"


CLANG_PARSE_OPTIONS = [ "-Wextra",
                        "-O0",
                        "-Wall",
                        "-Wunused-function",
                        "-Wtautological-compare",
                        "-Wformat-security",
                        "-I/usr/lib/gcc/x86_64-unknown-linux-gnu/5.3.0/include",
                        "-I/usr/include",
                        "-I/usr/lib/clang/3.7.0/include"
                        ]

DATABASES = {
    "default": {
        "ENGINE": 	"django.db.backends.sqlite3",
        "NAME": 	DB_PATH,
     }
}


STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "dajaxice.finders.DajaxiceFinder",
)

TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
    "django.template.loaders.eggs.Loader",
)

MIDDLEWARE_CLASSES = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
)

INSTALLED_APPS = (
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "dajaxice",
    "browser",
    "analyzer",
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse"
        }
    },

    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler"
        }
    },

    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
            },

        }
}
