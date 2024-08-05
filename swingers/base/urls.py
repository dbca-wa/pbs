from django.conf import settings
from django.conf.urls import url, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.views.generic import RedirectView

urlpatterns = [
    '',
    url(r'^browserid/', include('django_browserid.urls')),
    url(r'^api/persona$', 'django.contrib.auth.views.login',
        name='login_persona',
        kwargs={'template_name': 'base/login_persona.html'}),
    url(r'^login/$', 'django.contrib.auth.views.login', name='login',
        kwargs={'template_name': 'base/login.html'}),
    url(r'^logout/$', 'django.contrib.auth.views.logout', name='logout',
        kwargs={'template_name': 'base/logged_out.html'}),
    url(r'^confluence', RedirectView.as_view(url=settings.HELP_URL),
        name='help_page'),
    url(r'^api/swingers/v1/', include('swingers.sauth.urls')),
    url(r'^favicon\.ico$',
        RedirectView.as_view(url='/static/img/favicon.ico')),
    url(r'^docs/', include('django.contrib.admindocs.urls')),
]

urlpatterns += staticfiles_urlpatterns()
