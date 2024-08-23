from django import template
from django.contrib.admin.utils import quote
from django.urls import reverse

from pbs.risk.models import Treatment

register = template.Library()


@register.inclusion_tag('admin/risk/treatments.html', takes_context=True)
def show_treatments(context, location):
    current = context['current']
    treatments = Treatment.objects.filter(
        register__prescription=current, location__name=location)
    url = reverse('admin:risk_treatment_complete',
                  args=(quote(current.pk),))
    return {
        'current': current,
        'treatments': treatments,
        'url': url
    }
