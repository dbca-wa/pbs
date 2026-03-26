from django.template import Context, loader
from django.http import HttpResponseServerError
from django.shortcuts import redirect

import logging
import sys

log = logging.getLogger(__name__)


def handler500(request):
    context = {'request': request}
    t = loader.get_template('500.html')
    return HttpResponseServerError(t.render(Context(context)))

def sso_logout(request):
    return redirect('/sso/auth_logout')
