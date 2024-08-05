from django.conf import settings
from django.conf.urls import url

urlpatterns = [
    'swingers.sauth.views',
    url(r'{0}/request_token'.format(settings.SERVICE_NAME),
        'request_access_token', name="request_access_token"),
    url(r'{0}/list_tokens'.format(settings.SERVICE_NAME),
        'list_access_tokens', name="list_access_tokens"),
    url(r'{0}/delete_token'.format(settings.SERVICE_NAME),
        'delete_access_token', name="delete_access_token"),
    url(r'{0}/validate_token'.format(settings.SERVICE_NAME),
        'validate_token', name="validate_token"),
    url(r'^validate_token/$', 'validate_token'),
    url(r'session', 'session', name="session")
]
