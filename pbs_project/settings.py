import dj_database_url
#import ldap
import os
import json
import pytz
from .env import env
from django.utils import timezone
from datetime import datetime
#from django_auth_ldap.config import LDAPSearch, GroupOfNamesType, LDAPSearchUnion


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
POSTGIS_VERSION = (2, 4)

SECRET_KEY = env('SECRET_KEY', required=True)
FEX_MAIL = env('FEX_MAIL', 'pbs@dpaw.wa.gov.au')  # Do not update this without also updating fex.id
FEX_SVR_HTTP = env('FEX_SVR_HTTP', 'https://fex.dpaw.wa.gov.au')
SEND_URL = env('SEND_URL', 'https://send.dbca.wa.gov.au')
SEND_DOWNLOAD_LIMIT = env('SEND_DOWNLOAD_LIMIT', 1)  # No. of times that files may be downloaded.
PDF_TO_FEXSRV = env('PDF_TO_FEXSRV', True)
DAY_ROLLOVER_HOUR = int(env('DAY_ROLLOVER_HOUR', 17))
KMI_DOWNLOAD_URL = env('KMI_DOWNLOAD_URL', required=True)
CSV_DOWNLOAD_URL = env('CSV_DOWNLOAD_URL', required=True)
SHP_DOWNLOAD_URL = env('SHP_DOWNLOAD_URL', required=True)

FROM_EMAIL = env('FROM_EMAIL', 'PrescribedBurnSystem@dbca.wa.gov.au')
SUPPORT_EMAIL = env('SUPPORT_EMAIL', ['oim.servicedesk@dbca.wa.gov.au'])

NOTIFICATION_EMAIL=env('NOTIFICATION_EMAIL', None)

EMAIL_INSTANCE = env("EMAIL_INSTANCE", default="PROD")
NON_PROD_EMAIL = env("NON_PROD_EMAIL", default="")
PRODUCTION_EMAIL= env("PRODUCTION_EMAIL", default=False)

#BFRS_URL = env('BFRS_URL', 'https://bfrs.dpaw.wa.gov.au/')
BFRS_URL = env('BFRS_URL', 'https://bfrsapi.dbca.wa.gov.au/')
USER_SSO = env('USER_SSO', required=True)
PASS_SSO = env('PASS_SSO', required=True)

# PDF MUTEX - file lock max time 4 mins (4*60)
MAX_LOCK_TIME = env('MAX_LOCK_TIME', 240)

DEBUG = env('DEBUG', False)
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ['127.0.0.1', '::1']
if not DEBUG:
    ALLOWED_HOSTS = env('ALLOWED_DOMAINS', [])
else:
    ALLOWED_HOSTS = ['*']

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
    'django.contrib.sites',

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
    # 'south',
    'guardian',
    #'admin_enhancer',
    'django_select2',
    'chosen',
    'smart_selects',
    'crispy_forms',
    #'registration',
    'django_wsgiserver',
    'swingers',
    'tastypie',
)

# MIDDLEWARE_CLASSES = (
#     'pagination.middleware.PaginationMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'pbs.middleware.SSOLoginMiddleware',
# )
# MIDDLEWARE_CLASSES = (
#     'pagination.middleware.PaginationMiddleware',
#     'django.middleware.security.SecurityMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
#     'pbs.middleware.SSOLoginMiddleware',
# )

MIDDLEWARE = (
    'pagination.middleware.PaginationMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'pbs.middleware.SSOLoginMiddleware',
    'pbs.middleware.PBSV2SSOLoginMiddleware',
)
# TEMPLATE_CONTEXT_PROCESSORS = (
#     "django.contrib.auth.context_processors.auth",
#     "django.core.context_processors.debug",
#     "django.core.context_processors.i18n",
#     "django.core.context_processors.media",
#     "django.core.context_processors.static",
#     "django.core.context_processors.tz",
#     "django.core.context_processors.request",
#     "django.core.context_processors.csrf",
#     "django.contrib.messages.context_processors.messages",
#     "pbs_project.context_processors.standard",
# )

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # "django.core.context_processors.i18n",
                # "django.core.context_processors.media",
                # "django.core.context_processors.static",
                # "django.core.context_processors.tz",
                # "django.core.context_processors.csrf",
                "pbs_project.context_processors.standard",
            ],
            'builtins': [
                'pbs.prescription.templatetags.texify'
            ],
        },
    },
]

ROOT_URLCONF = 'pbs_project.urls'

WSGI_APPLICATION = 'pbs_project.wsgi.application'

# Database
DATABASES = {'default': dj_database_url.config()}
DEFAULT_AUTO_FIELD='django.db.models.AutoField' 
     
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

# TEMPLATE_DIRS = (
#     os.path.join(BASE_DIR, 'templates'),
# )

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)


SOUTH_TESTS_MIGRATE = False
SKIP_SOUTH_TESTS = True

# Application version number
APPLICATION_VERSION_NO = '1.6.6'

# Application title
SITE_TITLE = 'Prescribed Burn System'


# Define a maximum filesize for file uploads.
MAXIMUM_FILESIZE_UPLOAD = 200 * 1024 * 1024

CRISPY_TEMPLATE_PACK = 'bootstrap'

# Hack to get smart_selects working / happy.
ADMIN_MEDIA_PREFIX = os.path.join(STATIC_URL, 'admin/')

ACCOUNT_ACTIVATION_DAYS = 7

FPC_EMAIL_EXT = "@fpc.wa.gov.au"

USE_L10N = False
DATE_FORMAT = 'd-m-Y'
DATETIME_FORMAT = 'd-m-Y H:i'
TIME_FORMAT = 'H:i'

# Defines whether anonymous users have access to any views
# (via restless middleware)
ALLOW_ANONYMOUS_ACCESS = False
ANONYMOUS_USER_ID = -1

EMAIL_BACKEND = 'wagov_utils.components.utils.email_backend.EmailBackend'

# Authentication settings
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    # 'swingers.sauth.backends.EmailBackend',
    # 'wagov_utils.components.utils.email_backend.EmailBackend',
)
AUTH_PROFILE_MODULE = 'pbs.Profile'
LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL_FAILURE = LOGIN_URL
LOGOUT_URL = '/logout/'
LOGOUT_REDIRECT_URL = LOGOUT_URL

# LDAP settings
# AUTH_LDAP_SERVER_URI = env('LDAP_SERVER_URI', 'ldap_server')
# AUTH_LDAP_BIND_DN = env('LDAP_BIND_DN', 'ldap_bind')
# AUTH_LDAP_BIND_PASSWORD = env('LDAP_BIND_PASSWORD', 'ldap_password')

# AUTH_LDAP_ALWAYS_UPDATE_USER = False
# AUTH_LDAP_AUTHORIZE_ALL_USERS = True
# AUTH_LDAP_FIND_GROUP_PERMS = False
# AUTH_LDAP_MIRROR_GROUPS = False
# AUTH_LDAP_CACHE_GROUPS = False
# AUTH_LDAP_GROUP_CACHE_TIMEOUT = 300

# AUTH_LDAP_USER_SEARCH = LDAPSearchUnion(
#     LDAPSearch("DC=corporateict,DC=domain", ldap.SCOPE_SUBTREE,
#                "(sAMAccountName=%(user)s)"),
#     LDAPSearch("DC=corporateict,DC=domain", ldap.SCOPE_SUBTREE,
#                "(mail=%(user)s)"),
# )

# AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
#     "DC=corporateict,DC=domain",
#     ldap.SCOPE_SUBTREE, "(objectClass=group)"
# )

# AUTH_LDAP_GLOBAL_OPTIONS = {
#     ldap.OPT_X_TLS_REQUIRE_CERT: False,
#     ldap.OPT_REFERRALS: False,
# }

# AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr="cn")

# AUTH_LDAP_USER_ATTR_MAP = {
#     'first_name': "givenName",
#     'last_name': "sn",
#     'email': "mail",
# }

# Misc settings
EMAIL_HOST = env('EMAIL_HOST', 'smtp')
EMAIL_PORT = env('EMAIL_PORT', 25)
ANNUAL_INDIC_PROGRAM_PATH = env("ANNUAL_INDIC_PROGRAM_PATH", "burnprogram.shp")
SHP_LAYER = env("SHP_LAYER", "BPP_AN_Statewide_Albers")

COMPRESS_ENABLED = False

SOUTH_TESTS_MIGRATE = False
SKIP_SOUTH_TESTS = True

DEBUG_TOOLBAR_CONFIG = {
    'HIDE_DJANGO_SQL': False,
    'INTERCEPT_REDIRECTS': False,
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'console': {'format': '%(asctime)s %(levelname)s %(message)s'},
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'pdf_debugging': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'pbs': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'pdf_debugging': {
            'handlers': ['pdf_debugging'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}


ENV_TYPE = env('ENV_TYPE') or None
if not ENV_TYPE:
    try:
        ENV_TYPE = os.getcwd().split('-')[1].split('.')[0]  # will return either 'dev' or 'uat'
    except:
        ENV_TYPE = "TEST"
ENV_TYPE = ENV_TYPE.upper() if ENV_TYPE else "TEST"

BASE_URL = env("BASE_URL","")

try:
    #TCD_EXCLUSIONS format is '[["go-live date or datetime","filename"],["","filename"]]'
    tcd_exclusions = env("TCD_EXCLUSIONS")
    if tcd_exclusions:
        tz = pytz.timezone(TIME_ZONE)
        for tcd_exclusion in tcd_exclusions:
            #parse tcd_exclusion active date
            d = None
            tcd_exclusion[0] = tcd_exclusion[0].strip() if tcd_exclusion[0] else None
            if tcd_exclusion[0]:
                for f in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%d %H","%Y-%m-%d"):
                    try:
                        d = timezone.make_aware(datetime.strptime(tcd_exclusion[0],f),tz)
                        break
                    except:
                        continue
                if not d:
                    raise Exception("TCD_EXCLUSIONS({}) is invalid.".format(tcd_exclusion))

            tcd_exclusion[0] = d
            #parse tcd_exclusion exclusion list
            tcd_exclusion[1] = [line.rstrip('\n') for line in open(tcd_exclusion[1]) if not line.rstrip('\n')==''] if tcd_exclusion[1] else []
            #convert it to json string
            tcd_exclusion[1] = json.dumps(tcd_exclusion[1])


        #sort by active date desc, the active date of the last one shoule be None if have
        # TCD_EXCLUSIONS = sorted(tcd_exclusions,cmp=lambda data1,data2: 0 if data1[0] == data2[0] else (-1 if data1[0] is None else (1 if data2[0] is None else (-1 if data1[0] < data2[0] else 1))),reverse=True)
        TCD_EXCLUSIONS = sorted(
                            tcd_exclusions,
                            key=lambda data: (data[0] is None, data[0] if data[0] is not None else float('-inf')),
                            reverse=True
                        )
    else:
        TCD_EXCLUSIONS = []
except Exception as ex:
    raise Exception("TCD_EXCLUSIONS is invalid.{}".format(str(ex)))

import sys 
COLLECTSTATIC_ACTIVATED = False
if len(sys.argv) > 1:
    if sys.argv[1] == 'collectstatic':
        COLLECTSTATIC_ACTIVATED = True


