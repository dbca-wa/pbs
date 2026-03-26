from django import template
from django.contrib.auth.models import Group
from django.db.models import Max, Q

from collections import OrderedDict

from pbs.document.models import DocumentTag, DocumentCategory

from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
def tag_id(name):
    """
    Returns a tag id for the given tag name, the lookup is case-insensitive.
    """
    try:
        return DocumentTag.objects.get(name__iexact=name).id
    except DocumentTag.DoesNotExist:
        pass


@register.simple_tag
def filter_by_tag_name(qs, name):
    """
    Filters the queryset by tag name, the lookup is case-insensitive.
    Ensure that only documents that can be included are included (no zipped
    documents). All image types are automatically converted to pdf, so checking
    for ".pdf" extension should be sufficient.
    """
    return filter(lambda x: x.filename.endswith('.pdf'), qs.tag_names(name))


@register.simple_tag
def document_names_by_category(prescription):
    """
    Return a dictionary of document names indexed by category.
    Used at the end of Part D to display every document.
    """
    names = OrderedDict()
    for category in DocumentCategory.objects.all().order_by('order'):
        items = []
        for item in prescription.document_set.filter(category=category):
            items.append(item.document.name.split("/")[-1])
        names[category.name] = items
    return names


@register.simple_tag
def attached_documents(prescription):
    """
    Return the set of all attached (printable) documents. Exclude those
    documents that can are printed in other sections.
    """
    qs = prescription.document_set.exclude(
        Q(tag__name__iexact="Traffic Diagrams") |
        Q(tag__name__iexact="Sign Inspection and Surveillance Form") |
        Q(tag__name__iexact="Prescribed Burning Organisational Structure and Communications Plan") |
        Q(tag__name__iexact="Context Map") |
        Q(tag__name__iexact="Prescribed Burning SMEAC Checklist"))
    qs.modified = qs.aggregate(Max('modified'))["modified__max"]
    return filter(lambda x: x.filename.endswith('.pdf'), qs)


@register.inclusion_tag('admin/document_list.html', takes_context=True)
def document_list(context):
    """
    Created for Action report on the CAR screens.
    """
    current = context.get('current')
    request = context.get('request')
    if 'pre_burn' in request.GET:
        document_set = current.document_set.tag_names('Pre Burn Actions List')
        document_type = 'Pre Burn Actions Lists'
    elif 'day_of_burn' in request.GET:
        document_set = current.document_set.tag_names(
            'Day of Burn Actions List')
        document_type = 'Day of Burn Actions Lists'
    elif 'post_burn' in request.GET:
        document_set = current.document_set.tag_names('Post Burn Actions List')
        document_type = 'Post Burn Actions Lists'
    else:
        document_set = current.document_set.all()
        document_type = 'All documents'

    return {
        "current": current,
        "request": request,
        "document_type": document_type,
        "document_set": document_set
    }

@register.filter
@stringfilter
def template_exists(value):
    try:
        template.loader.get_template(value)
        return True
    except template.TemplateDoesNotExist:
        return False


@register.filter(name='has_group')
def has_group(user, group_name):
    group = Group.objects.get(name=group_name)
    return True if group in user.groups.all() else False
