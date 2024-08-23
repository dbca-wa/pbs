import ldap
import os
import socket

from django.utils.http import urlquote
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType

from swingers.utils import machine_id


HOSTNAME = socket.gethostname()

ALLOWED_HOSTS = ['*']

SITE_ROOT = os.path.dirname(__file__)
SITE_BASE = os.path.basename(__file__)

# Set port suffix for deployment with apache/nginx
SITE_PORT = SITE_ROOT.split('_')[-1]
SITE_NAME = urlquote("FIXME/{{ project_name }}/" + HOSTNAME)
SITE_TITLE = "TODO/FIXME in settings.SITE_TITLE"
SITE_ID = 1

ADMINS = tuple(os.getenv('ADMINS', []))
MANAGERS = ADMINS

APPLICATION_VERSION_NO = 0.1

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', os.getenv('db_name')),
        'USER': os.getenv('DATABASE_USER', os.getenv('db_user')),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', os.getenv('db_pass')),
        'HOST': os.getenv('DATABASE_HOST', os.getenv('db_host')),
        'PORT': os.getenv('DATABASE_PORT', os.getenv('db_port')),
    }
}

TIME_ZONE = 'Australia/Perth'

LANGUAGE_CODE = 'en-us'

USE_I18N = False
USE_L10N = True
USE_TZ = True

MEDIA_ROOT = os.path.join(SITE_ROOT, 'media')
MEDIA_URL = '/media/'

STATIC_ROOT = os.getenv('STATIC_ROOT')
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

# CDN settings
DEC_CDN = '//ge.dec.wa.gov.au/_/'
CDNJS_URL = DEC_CDN + 'cdnjs/ajax/libs/'
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

HELP_URL = os.getenv('HELP_URL')

SECRET_KEY = machine_id()

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'swingers.middleware.html.HtmlMinifyMiddleware',    # needs sessions
    'swingers.middleware.html.JsCssCompressMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'swingers.middleware.auth.AuthenticationMiddleware',
)

# TEMPLATE_CONTEXT_PROCESSORS = (
#     'django.contrib.auth.context_processors.auth',
#     'django_browserid.context_processors.browserid',
#     'django.contrib.messages.context_processors.messages',
#     'django.core.context_processors.media',
#     'django.core.context_processors.request',
#     'django.core.context_processors.csrf',
#     'django.core.context_processors.static',
#     'swingers.base.context_processors.standard',
# )
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'swingers.base.context_processors.standard',
                'django.core.context_processors.media',
                'django.core.context_processors.request',
                'django.core.context_processors.csrf',
                'django.core.context_processors.static',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'swingers.sauth.backends.PersonaBackend',
    'swingers.sauth.backends.EmailBackend',
)

ANONYMOUS_USER_ID = 1

# LDAP settings
AUTH_LDAP_SERVER_URI = os.getenv('LDAP_SERVER_URI')
AUTH_LDAP_BIND_DN = os.getenv('LDAP_BIND_DN')
AUTH_LDAP_BIND_PASSWORD = os.getenv('LDAP_BIND_PASSWORD')

AUTH_LDAP_ALWAYS_UPDATE_USER = False
AUTH_LDAP_AUTHORIZE_ALL_USERS = True
AUTH_LDAP_FIND_GROUP_PERMS = True
AUTH_LDAP_MIRROR_GROUPS = True
AUTH_LDAP_CACHE_GROUPS = False
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 300

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    os.getenv('LDAP_BASE'),
    ldap.SCOPE_SUBTREE, "(sAMAccountName=%(user)s)"
)

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    os.getenv('LDAP_BASE'),
    ldap.SCOPE_SUBTREE, "(objectClass=group)"
)

AUTH_LDAP_GLOBAL_OPTIONS = {
    ldap.OPT_X_TLS_REQUIRE_CERT: False,
    ldap.OPT_REFERRALS: False,
}

AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr="cn")

AUTH_LDAP_USER_ATTR_MAP = {
    'first_name': "givenName",
    'last_name': "sn",
    'email': "mail",
}

AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_staff": os.getenv('LDAP_STAFF_FLAG'),
    "is_superuser": os.getenv('LDAP_SUPERUSER_FLAG')
}

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.cache.RedisCache',
        'LOCATION': 'localhost:6379:1',
        'OPTIONS': {
            'DB': 1,
        },
    },
}

# Session settings
SESSION_COOKIE_NAME = SITE_NAME.replace("/", "|").encode("ascii")
SESSION_ENGINE = 'redis_sessions.session'

ROOT_URLCONF = '{{ project_name }}.urls'

WSGI_APPLICATION = 'wsgi.application'

INSTALLED_APPS = (
    # current project applications
    '{{ project_name }}',

    # DPaW applications
    'swingers',

    # third-party applications
    'django_browserid',
    'django_extensions',
    'reversion',
    'compressor',
    'south',
    'guardian',

    # django
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.markup',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
)


# Debug toolbar settings
def show_debug_toolbar(request):
    if "debug" in request.GET:
        request.session['debug'] = request.GET['debug'] == "on"
    elif not "debug" in request.session:
        request.session['debug'] = False
    return DEBUG and request.session['debug']

DEBUG_MIDDLEWARE_CLASSES = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

DEBUG_INSTALLED_APPS = (
    'debug_toolbar',
)

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)

DEBUG_TOOLBAR_CONFIG = {
    'HIDE_DJANGO_SQL': False,
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TOOLBAR_CALLBACK': show_debug_toolbar
}

LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'database': {
            'format': '%(levelname)s %(asctime)s %(module)s %(param)s %(duration)d %(sql)s %(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(MEDIA_ROOT, 'django.log'),
            'formatter': 'verbose',
            'maxBytes': '16777216'
        },
        'django_browserid': {
            'level': 'INFO',
            'class': 'logging.StreamHandler'
        },
        'mail-admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['file', 'mail-admins'],
            'level': 'INFO'
        },
        'log': {
            'handlers': ['file'],
            'level': 'INFO'
        },
        'django_browserid.base': {
            'handlers': ['django_browserid']
        }
    }
}

DEBUG_LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'database': {
            'format': '%(levelname)s %(asctime)s %(module)s %(param)s %(duration)d %(sql)s %(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(MEDIA_ROOT, "django.log"),
            'formatter': 'verbose',
            'maxBytes': '16777216'
        },
        'db': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(MEDIA_ROOT, "djangodb.log"),
            'formatter': 'verbose',
            'maxBytes': '16777216'
        }
    },
    'loggers': {
        'django_auth_ldap': {
            'handlers': ['file'],
            'level': 'DEBUG'
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG'
        },
        'django.db.backends.disabled': {
            'handlers': ['db'],
            'level': 'INFO'
        },
        'log': {
            'handlers': ['file'],
            'level': 'DEBUG'
        }
    }
}

# Set debug flag if project directory contains a file called 'debug'
# (case-insensitive):
project_dir = [i.upper() for i in os.listdir(SITE_ROOT)]
DEBUG = 'DEBUG' in project_dir

if DEBUG:
    LOGGING = DEBUG_LOGGING
    TEMPLATE_DEBUG = True
    MIDDLEWARE_CLASSES += DEBUG_MIDDLEWARE_CLASSES
    INSTALLED_APPS += DEBUG_INSTALLED_APPS

EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')

# Login and redirect URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_URL = '/logout/'
# Set this to False to hide the "Login with Persona" button in the navbar:
PERSONA_LOGIN = True

HTML_MINIFY = True  # minify the HTML when debug toolbar is not shown

STATIC_CONTEXT_VARS = {}
SERVICE_NAME = "localonly"

# Sensible AU date input formats
DATE_INPUT_FORMATS = (
    '%d/%m/%y',
    '%d/%m/%Y',
    '%d-%m-%y',
    '%d-%m-%Y',
    '%d %b %Y',
    '%d %b, %Y',
    '%d %B %Y',
    '%d %B, %Y'
)

DATETIME_INPUT_FORMATS = [
    '%d/%m/%y %H:%M',
    '%d/%m/%Y %H:%M',
    '%d-%m-%y %H:%M',
    '%d-%m-%Y %H:%M',
]

COMPRESS_ENABLED = True
COMPRESS_JS_COMPRESSOR = 'swingers.compress.JsCssCompressor'
COMPRESS_PARSER = 'swingers.compress.CompressParser'

if DEBUG:
    # we might not want to bother setting up environment variables during
    # developing
    try:
        from local_settings import *
    except ImportError:
        pass
