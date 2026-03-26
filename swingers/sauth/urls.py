from django.conf import settings
# from django.conf.urls import url
from django.urls import re_path

urlpatterns = [
    'swingers.sauth.views',
   re_path(r'{0}/request_token'.format(settings.SERVICE_NAME),
        'request_access_token', name="request_access_token"),
   re_path(r'{0}/list_tokens'.format(settings.SERVICE_NAME),
        'list_access_tokens', name="list_access_tokens"),
   re_path(r'{0}/delete_token'.format(settings.SERVICE_NAME),
        'delete_access_token', name="delete_access_token"),
   re_path(r'{0}/validate_token'.format(settings.SERVICE_NAME),
        'validate_token', name="validate_token"),
   re_path(r'^validate_token/$', 'validate_token'),
   re_path(r'session', 'session', name="session")
]
