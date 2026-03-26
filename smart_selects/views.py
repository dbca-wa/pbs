import locale

# from django.db.models import get_model
from django.http import HttpResponse
# from django.utils import simplejson
import json

from smart_selects.utils import unicode_sorter
from django.apps import apps
from functools import cmp_to_key


def filterchain(request, app, model, field, value, manager=None):
    model_class = apps.get_model(app, model)
    if value == '0':
        keywords = {str("%s__isnull" % field): True}
    else:
        keywords = {str(field): str(value)}
    if manager is not None and hasattr(model_class, manager):
        queryset = getattr(model_class, manager)
    else:
        queryset = model_class._default_manager
    results = list(queryset.filter(**keywords))
    # results.sort(cmp=locale.strcoll, key=lambda x: unicode_sorter(unicode(x)))
    results.sort(key=lambda x: cmp_to_key(locale.strcoll)(unicode_sorter(str(x))))
    result = []
    for item in results:
        result.append({'value': item.pk, 'display': str(item)})
    js = json.dumps(result)
    return HttpResponse(js, content_type='application/json')


def filterchain_all(request, app, model, field, value):
    model_class = apps.get_model(app, model)
    if value == '0':
        keywords = {str("%s__isnull" % field): True}
    else:
        keywords = {str(field): str(value)}
    results = list(model_class._default_manager.filter(**keywords))
    results.sort(key=lambda x: cmp_to_key(locale.strcoll)(unicode_sorter(str(x))))
    final = []
    for item in results:
        final.append({'value': item.pk, 'display': str(item)})
    results = list(model_class._default_manager.exclude(**keywords))
    results.sort(key=lambda x: cmp_to_key(locale.strcoll)(unicode_sorter(str(x))))
    final.append({'value': "", 'display': "---------"})

    for item in results:
        final.append({'value': item.pk, 'display': str(item)})
    js = json.dumps(final)
    return HttpResponse(js, content_type='application/json')
