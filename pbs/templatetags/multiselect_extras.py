#! /us/bin/env python2.7
"""
Module: multiselect.py
Package: pbs.templatetags
Description: Create select html for a multiple select boxes

This function crafts the context dictionary that will be passed to the template
and thus to the the multiselect template tag.

The spec and choices are a part of the changelist object that the ModelAdmin returns.
We use the title, display and query_string attrs of that object to set useful and
unique attributes on the select elements, which will be turned into multiselects
by the bootstrap js library.
"""
from __future__ import print_function, division, unicode_literals, absolute_import
# Imports
from django import template
from urllib.parse import parse_qs
register = template.Library()
# Constants

# Classes

# Functions
@register.inclusion_tag("admin/prescription/prescription/multiselect.html",
                        takes_context=True)
def multiselect_form(context):
    changelist = context['cl']
    specs = list(changelist.filter_specs)
    selected = context.get('selected', set())
    selects = []
    for spec in specs:
        field_name = None
        choices = []
        # Ignore the first provided choice "All"
        for choice in list(spec.choices(changelist))[1:]:
            q = parse_qs(choice['query_string'].lstrip('?'))
            # If any key doesn't start with the field name, pop it out of the dict.
            # We should end up with a single key:value.
            for k in q.keys():
                if not k.startswith(spec.field.name):
                    del q[k]
            # for k, v in q.iteritems():
            for k, v in q.items():
                val = None
                # For each key:value, only use those that end in '__exact'
                # or equal 'financial_year'
                # WHY DOESN'T financial_year BEHAVE LIKE ALL THE OTHER FIELDS?
                if k.endswith('__exact') or k == 'financial_year':
                    if k == 'financial_year':
                        field_name = 'financial_year'
                    else:
                        field_name = k.replace('__exact', '')
                    val = v[0]
                    choices.append({
                        'value': val,
                        #'value': choice['query_string'],
                        # 'name': unicode(choice['display']),
                        'name': choice['display'],
                        'selected': choice['query_string'] in selected,
                    })

        selects.append({
            'field': field_name,
            #'field': spec.field.name,
            'title': spec.title.title(),
            'choices': choices,
        })
    return {'selects': selects}
