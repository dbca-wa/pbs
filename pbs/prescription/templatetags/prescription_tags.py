from django import template
from django.db.models import Max
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter

from pbs.implementation.models import (Way, RoadSegment, TrailSegment,
                                       SignInspection, TrafficControlDiagram)
from pbs.risk.models import Action, Register
from pbs.prescription.models import Endorsement, EndorsingRole
import os

register = template.Library()


@register.simple_tag
def risk_display(register, draft=False):
    """
    Display as HTML span.
    """
    if draft:
        level = register.draft_risk_level
        name = register.get_draft_risk_level_display()
        id_ = "id_max_draft_risk_" + str(register.id)
    else:
        level = register.final_risk_level
        name = register.get_final_risk_level_display()
        id_ = "id_max_final_risk_" + str(register.id)

    if level == Register.LEVEL_VERY_LOW:
        label = 'label-very-low'
    elif level == Register.LEVEL_LOW:
        label = 'label-low'
    elif level == Register.LEVEL_MEDIUM:
        label = 'label-medium'
    elif level == Register.LEVEL_HIGH:
        label = 'label-high'
    else:
        label = 'label-very-high'

    return mark_safe(
        '<span id="%s" class="label %s">%s</span>' % (id_, label, name))


@register.simple_tag(takes_context=True)
def pfp_status(context):
    """
    Renders the PDF output's header line.
    """
    current = context['prescription']
    return "{0}, {1}, {2}, {3}, {4}".format(
        current.get_planning_status_display(),
        current.get_endorsement_status_display(),
        current.get_approval_status_display(),
        current.get_ignition_status_display(),
        current.get_status_display()
    )


@register.simple_tag(takes_context=True)
def all_actions(context):
    """
    All actions on the current prescription.
    """
    current = context['current']
    qs = Action.objects.filter(risk__prescription=current, relevant=True)
    qs.modified = qs.aggregate(Max('modified'))["modified_max"]
    pre_burn = qs.filter(pre_burn=True)
    pre_burn.modified = pre_burn.aggregate(Max('modified'))["modified_max"]
    day_burn = qs.filter(day_of_burn=True)
    day_burn.modified = day_burn.aggregate(Max('modified'))["modified_max"]
    post_burn = qs.filter(post_burn=True)
    post_burn.modified = post_burn.aggregate(Max('modified'))["modified_max"]

    return {
        "pre_burn": pre_burn,
        "day_of_burn": day_burn,
        "post_burn": post_burn,
        "all": qs,
    }


@register.simple_tag(takes_context=True)
def all_ways(context):
    """
    All of the roads, tracks, and trails for a particular ePFP.
    """
    current = context['current']

    roads = RoadSegment.objects.filter(prescription=current)
    trails = TrailSegment.objects.filter(prescription=current)
    ways = Way.objects.filter(prescription=current)
    inspections = SignInspection.objects.filter(way__prescription=current)
    traffic_diagrams = TrafficControlDiagram.objects.filter(
        roadsegment__prescription=current).exclude(name="custom").distinct()

    for qs in [roads, trails, ways, inspections]:
        qs.modified = qs.aggregate(Max('modified'))["modified__max"]

    return {
        "roads": roads,
        "trails": trails,
        "ways": ways,
        "standard_traffic_diagrams": traffic_diagrams,
        "inspections": inspections,
        "modified": max([modified for modified in
                         [roads.modified, trails.modified,
                         ways.modified, inspections.modified,
                         current.created]
                         if modified is not None])
    }


@register.filter
@stringfilter
def latex_criteria(value):
    """
    Priority justification criteria in A4 latex PDF
    """
    value = value.replace('    ', '\hspace*{0.5cm}').replace('\n', '\\newline')
    return value


@register.simple_tag
def get_required_role(prescription):
    risk, label, role = prescription._max_risk(prescription.maximum_risk)
    return role


@register.simple_tag
def role_required(prescription, role):
    """
    Check if the endorsing role is required, and if it has been performed.
    Includes span display:none enumerator hack to make table sortable.
    """
    endorsing_role = EndorsingRole.objects.get(name=role)
    if endorsing_role in prescription.endorsing_roles.all():
        if Endorsement.objects.filter(prescription=prescription,
                                      role=endorsing_role).exists():
            output = '<span style="display:none">2</span><i class="icon-ok text-success"></i>'
        else:
            output = '<span style="display:none">1</span><i class="icon-warning-sign text-error"></i>'
    else:
        output = '<span style="display:none">0</span>'
    return output

@register.simple_tag(takes_context=True)
def base_dir(context):
    """ Hack for getting the base_dir for uWSGI config. settings.BASE_DIR returns '' in latex templates when using uWSGI """
    return '{}'.format(os.getcwd())

@register.simple_tag
#@register.simple_tag
def _has_unique_district(objects):
    #import ipdb; ipdb.set_trace()
    objs_distinct = [obj.fire_idd for obj in objects.distinct('district')]
    #return [] if objs_distinct==1 else objs_distinct
    return True if len(objs_distinct)<=1 else False

@register.simple_tag(takes_context=True)
def __has_unique_district(context):
    #import ipdb; ipdb.set_trace()
    planned_burns = context['qs_burn']
    objs_distinct = [obj.fire_idd for obj in planned_burns.distinct('district')]
    #return [] if objs_distinct==1 else objs_distinct
    return True if len(objs_distinct)<=1 else False

@register.filter(takes_context=True)
def has_unique_district(objects):
    print(objects)
    #objs_distinct = [obj.fire_idd for obj in objects.distinct('district')]
    #return [] if objs_distinct==1 else objs_distinct
   # return True if len(objs_distinct)<=1 else False
    return True

