import dj_database_url
import ldap
import os

from django_auth_ldap.config import (LDAPSearch, GroupOfNamesType,
                                     LDAPSearchUnion)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

POSTGIS_VERSION = (2,1)

SECRET_KEY = os.environ['SECRET_KEY']
FEX_MAIL = os.environ.get('FEX_MAIL', 'pbs@dpaw.wa.gov.au')
FEX_SVR_HTTP = os.environ.get('FEX_SVR_HTTP', 'https://fex.dpaw.wa.gov.au')
PDF_TO_FEXSRV = os.environ.get('PDF_TO_FEXSRV', True)
DAY_ROLLOVER_HOUR = int(os.environ.get('DAY_ROLLOVER_HOUR', 17))

# PDF MUTEX - file lock max time 4 mins (4*60)
MAX_LOCK_TIME = os.environ.get('MAX_LOCK_TIME', 240)

DEBUG = os.environ.get('DEBUG', None) in ["True", "on", "1", "DEBUG"]
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ['127.0.0.1', '::1']
if not DEBUG:
    # Localhost, UAT and Production hosts
    ALLOWED_HOSTS = [
        'localhost',
        '127.0.0.1',
        'pbs.dpaw.wa.gov.au',
        'pbs.dpaw.wa.gov.au.',
        'pbs-training.dpaw.wa.gov.au',
        'pbs-training.dpaw.wa.gov.au.',
    ]

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # PBS model breakdown
    'pbs',
    'pbs.prescription',
    'pbs.stakeholder',
    'pbs.risk',
    'pbs.document',
    'pbs.implementation',
    'pbs.report',
    'pbs.review',

    # third-party applications
    'pagination',
    'django_extensions',
    #'reversion',
    'south',
    'guardian',
    'admin_enhancer',
    'django_select2',
    'chosen',
    'smart_selects',
    'debug_toolbar',
    #'debug_toolbar_htmltidy',
    'crispy_forms',
    'registration',
    'django_wsgiserver',
    'swingers',
)


MIDDLEWARE_CLASSES = (
    'pagination.middleware.PaginationMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'dpaw_utils.middleware.SSOLoginMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.core.context_processors.request",
    "django.core.context_processors.csrf",
    "django.contrib.messages.context_processors.messages",
    "pbs_project.context_processors.standard",
)

ROOT_URLCONF = 'pbs_project.urls'

WSGI_APPLICATION = 'pbs_project.wsgi.application'

# Database
DATABASES = {'default': dj_database_url.config()}
CONN_MAX_AGE = None

# Internationalization
SITE_ID = 1
SITE_NAME = "PBS"
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Australia/Perth'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# Ensure that the media directory exists:
if not os.path.exists(os.path.join(BASE_DIR, 'media')):
    os.mkdir(os.path.join(BASE_DIR, 'media'))
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)


SOUTH_TESTS_MIGRATE = False
SKIP_SOUTH_TESTS = True

# Application version number
APPLICATION_VERSION_NO = '1.4.8'

# Application title
SITE_TITLE = 'Prescribed Burn System'


# Define a maximum filesize for file uploads.
MAXIMUM_FILESIZE_UPLOAD = 200 * 1024 * 1024

CRISPY_TEMPLATE_PACK = 'bootstrap'

# Hack to get smart_selects working / happy.
ADMIN_MEDIA_PREFIX = os.path.join(STATIC_URL, 'admin/')

ACCOUNT_ACTIVATION_DAYS = 7
RAVEN_CONFIG = {
    'dsn': 'http://2173137037584e57b94a699d3a282afc:1681a05fd3254a5898a86a455bf14610@kens-apache-001-dev:9000/2',
}

FPC_EMAIL_EXT = "@fpc.wa.gov.au"

USE_L10N = False
DATE_FORMAT = 'd-m-Y'
DATETIME_FORMAT = 'd-m-Y H:i'
TIME_FORMAT = 'H:i'

# Defines whether anonymous users have access to any views
# (via restless middleware)
ALLOW_ANONYMOUS_ACCESS = False
ANONYMOUS_USER_ID = -1

# Authentication settings
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'swingers.sauth.backends.EmailBackend',
)
AUTH_PROFILE_MODULE = 'pbs.Profile'
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL_FAILURE = LOGIN_URL
LOGOUT_URL = '/logout/'
LOGOUT_REDIRECT_URL = LOGOUT_URL

# LDAP settings
AUTH_LDAP_SERVER_URI = os.environ.get('LDAP_SERVER_URI')
AUTH_LDAP_BIND_DN = os.environ.get('LDAP_BIND_DN')
AUTH_LDAP_BIND_PASSWORD = os.environ.get('LDAP_BIND_PASSWORD')

AUTH_LDAP_ALWAYS_UPDATE_USER = False
AUTH_LDAP_AUTHORIZE_ALL_USERS = True
AUTH_LDAP_FIND_GROUP_PERMS = False
AUTH_LDAP_MIRROR_GROUPS = False
AUTH_LDAP_CACHE_GROUPS = False
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 300

AUTH_LDAP_USER_SEARCH = LDAPSearchUnion(
    LDAPSearch("DC=corporateict,DC=domain", ldap.SCOPE_SUBTREE,
               "(sAMAccountName=%(user)s)"),
    LDAPSearch("DC=corporateict,DC=domain", ldap.SCOPE_SUBTREE,
               "(mail=%(user)s)"),
)

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "DC=corporateict,DC=domain",
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

# Misc settings
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = os.environ.get('EMAIL_PORT', 25)

COMPRESS_ENABLED = False

SOUTH_TESTS_MIGRATE = False
SKIP_SOUTH_TESTS = True

DEBUG_TOOLBAR_CONFIG = {
    'HIDE_DJANGO_SQL': False,
    'INTERCEPT_REDIRECTS': False,
}

# Logging configuration
# Ensure that the logs directory exists:
if not os.path.exists(os.path.join(BASE_DIR, 'logs')):
    os.mkdir(os.path.join(BASE_DIR, 'logs'))
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)-.19s [%(process)d] [%(levelname)s] '
                      '%(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'pbs.log'),
            'formatter': 'standard',
            'maxBytes': '16777216'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'pdf_debugging': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'pdf_debugging.log'),
            'formatter': 'standard',
            'maxBytes': '16777216'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'pbs': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        },
        'pdf_debugging': {
            'handlers': ['pdf_debugging'],
            'level': 'DEBUG'
        }
    }
}

if DEBUG:
    # Set up logging differently to give us some more information about what's
    # going on
    LOGGING['loggers'] = {
        'django_auth_ldap': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True
        },
        'pbs': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True
        },
    }

    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )
    if os.environ.get('INTERNAL_IP', False):  # Optionally add developer local IP
        INTERNAL_IPS.append(os.environ['INTERNAL_IP'])
    DEBUG_TOOLBAR_PATCH_SETTINGS = True
