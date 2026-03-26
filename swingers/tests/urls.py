# from django.conf.urls import url
from django.urls import re_path
from django.contrib.auth.views import login

from swingers.tests.views import *


urlpatterns = [
    'swingers.sauth.views',
    url(r'^update_counter/(?P<pk>\d+)/$', CounterView.as_view(),
        name="test-update-counter"),
    url(r'^update_counter2/(?P<pk>\d+)/$', CounterView.as_view(),
        name="test-update-counter2"),
    url(r'^create_duck/$', create_duck, name="test-create-duck"),
    url(r'^create_duck2/$', CreateDuck.as_view(),
        name="test-create-duck2"),
    url(r'^create_duck3/$', CreateDuck2.as_view(), name="test-create-duck3"),
    url(r'^create_duck4/(?P<name>.*)/?$', create_duck2,
        name="test-create-duck4"),
    url(r'^accounts/login/$', login, name='login'),
    url(r'test/request_token', 'request_access_token',
        name="request_access_token"),
    url(r'test/list_tokens', 'list_access_tokens', name="list_access_tokens"),
    url(r'test/delete_token', 'delete_access_token',
        name="delete_access_token"),
    url(r'test/validate_token', 'validate_token', name="validate_token"),
    url(r'session', 'session', name="session")
]
