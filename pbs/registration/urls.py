
#from django.conf.urls import patterns
# from django.conf.urls import url
from django.urls import re_path
from django.views.generic.base import TemplateView

# from registration.backends.default.views import (RegistrationView,
#                                                  ActivationView)
from pbs.registration.forms import RegistrationForm


urlpatterns = [
    # '',
   re_path(r'^activate/complete/$',
        TemplateView.as_view(
            template_name='registration/activation_complete.html'),
        name='registration_activation_complete'),
    #re_path(r'^activate/(?P<activation_key>\w+)/$',
    #     ActivationView.as_view(),
    #     name='registration_activate'),
    #re_path(r'^register/$',
    #     RegistrationView.as_view(form_class=RegistrationForm),
    #     name='registration_register'),
   re_path(r'^register/complete/$',
        TemplateView.as_view(
            template_name='registration/registration_complete.html'),
        name='registration_complete'),
]
