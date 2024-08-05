
#from django.conf.urls import patterns
from django.conf.urls import url
from django.views.generic.base import TemplateView

# from registration.backends.default.views import (RegistrationView,
#                                                  ActivationView)
from pbs.registration.forms import RegistrationForm


urlpatterns = [
    '',
    url(r'^activate/complete/$',
        TemplateView.as_view(
            template_name='registration/activation_complete.html'),
        name='registration_activation_complete'),
    # url(r'^activate/(?P<activation_key>\w+)/$',
    #     ActivationView.as_view(),
    #     name='registration_activate'),
    # url(r'^register/$',
    #     RegistrationView.as_view(form_class=RegistrationForm),
    #     name='registration_register'),
    url(r'^register/complete/$',
        TemplateView.as_view(
            template_name='registration/registration_complete.html'),
        name='registration_complete'),
]
