from django.conf.urls import url
from django.conf import settings
from django.db.models import Count, Sum
from tastypie.resources import ModelResource, Resource
from tastypie.authorization import Authorization, ReadOnlyAuthorization, DjangoAuthorization
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.api import Api
from tastypie import fields
from pbs.review.models import current_finyear, PrescribedBurn

from django.contrib.auth.models import User
from tastypie.http import HttpBadRequest, HttpUnauthorized, HttpAccepted
from tastypie.exceptions import ImmediateHttpResponse, Unauthorized
import json


def generate_filtering(mdl):
    """Utility function to add all model fields to filtering whitelist.
    See: http://django-tastypie.readthedocs.org/en/latest/resources.html#basic-filtering
    """
    filtering = {}
    for field in mdl._meta.fields:
        filtering.update({field.name: ALL_WITH_RELATIONS})
    return filtering


def generate_meta(klass):
    return type('Meta', (object,), {
        'queryset': klass.objects.all(),
        'resource_name': klass._meta.model_name,
        'filtering': generate_filtering(klass),
        'authorization': Authorization(),
        'always_return_data': True
    })


class APIResource(ModelResource):
    class Meta:
        #pass
        object_class=None

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>{})/fields/(?P<field_name>[\w\d_.-]+)/$".format(self._meta.resource_name),
                self.wrap_view('field_values'), name="api_field_values"),
        ]

    def field_values(self, request, **kwargs):
        # Get a list of unique values for the field passed in kwargs.
        try:
            qs = self._meta.queryset.values_list(kwargs['field_name'], flat=True).distinct()
        except FieldError as e:
            return self.create_response(request, data={'error': str(e)}, response_class=HttpBadRequest)
        # Prepare return the HttpResponse.
        return self.create_response(request, data=list(qs))


class PrescribedBurnResource(APIResource):
    class Meta:
        authorization= ReadOnlyAuthorization()
        object_class=None

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>{})/$".format(self._meta.resource_name),
                self.wrap_view('field_values'), name="api_field_values"),
        ]

    def field_values(self, request, **kwargs):
        try:
            #import ipdb; ipdb.set_trace() 
            qs = PrescribedBurn.objects.filter(date__year=current_finyear(), fire_id__isnull=False)
            if request.GET.get('fire_id'):
                qs = qs.filter(fire_id=request.GET.get('fire_id'))
            if request.GET.get('fire_id__in'):
                fire_id_list = [i.strip() for i in request.GET.get('fire_id__in').strip('[').strip(']').split(',')]
                qs = qs.filter(fire_id__in=fire_id_list)
            qs = qs.values('fire_id', 'region').annotate(area=Sum('area'))
        except FieldError as e:
            return self.create_response(request, data={'error': str(e)}, response_class=HttpBadRequest)
        return self.create_response(request, data=list(qs))



