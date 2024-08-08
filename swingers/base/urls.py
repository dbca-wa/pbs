from django.conf import settings
from django.conf.urls import include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import re_path

from django.views.generic import RedirectView

urlpatterns = [
    '',
   re_path(r'^browserid/', include('django_browserid.urls')),
   re_path(r'^api/persona$', 'django.contrib.auth.views.login',
        name='login_persona',
        kwargs={'template_name': 'base/login_persona.html'}),
   re_path(r'^login/$', 'django.contrib.auth.views.login', name='login',
        kwargs={'template_name': 'base/login.html'}),
   re_path(r'^logout/$', 'django.contrib.auth.views.logout', name='logout',
        kwargs={'template_name': 'base/logged_out.html'}),
   re_path(r'^confluence', RedirectView.as_view(url=settings.HELP_URL),
        name='help_page'),
   re_path(r'^api/swingers/v1/', include('swingers.sauth.urls')),
   re_path(r'^favicon\.ico$',
        RedirectView.as_view(url='/static/img/favicon.ico')),
   re_path(r'^docs/', include('django.contrib.admindocs.urls')),
]

urlpatterns += staticfiles_urlpatterns()
