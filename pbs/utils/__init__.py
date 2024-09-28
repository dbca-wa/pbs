from django.contrib.admin.utils import NestedObjects
from django.contrib.auth.models import Group
from django.utils.text import capfirst
from django.utils.encoding import force_str

from guardian.shortcuts import remove_perm

from pbs.admin import get_permission_codename
from django.core.mail import EmailMessage
from django.conf import settings
import os

from .pdf import pdflatex,download_pdf

def get_deleted_objects(objs, opts, user, admin_site, using):
    """
    Find all objects related to ``objs`` that should also be deleted. ``objs``
    must be a homogenous iterable of objects (e.g. a QuerySet).

    Returns a nested list of strings suitable for display in the
    template with the ``unordered_list`` filter.

    """
    collector = NestedObjects(using=using)
    collector.collect(objs)
    perms_needed = set()

    def format_callback(obj):
        opts = obj._meta

        return '%s: %s' % (capfirst(opts.verbose_name),
                           force_str(obj))

    to_delete = collector.nested(format_callback)

    protected = [format_callback(obj) for obj in collector.protected]

    return to_delete, perms_needed, protected


def update_permissions(prescription, admin_site, state, action=remove_perm):
    """
    Update a prescription's object permissions based on the state of the
    ePFP.
    """
    # Loop over each model admin and check when it should be disabled,
    # adding/removing permissions as necessary.
    from pbs.prescription.admin import SavePrescriptionMixin
    group = Group.objects.get(name="Users")
    for model, model_admin in admin_site._registry.items():
        if isinstance(model_admin, SavePrescriptionMixin):
            if model_admin.can_delete and model_admin.lock_after == state:
                opts = model_admin.opts
                perm = get_permission_codename("delete", opts)
                if hasattr(model_admin, "prescription_filter_field"):
                    options = {
                        model_admin.prescription_filter_field: prescription
                    }
                else:
                    options = {"prescription": prescription}
                for obj in model.objects.filter(**options):
                    action("%s.%s" % (opts.app_label, perm), group, obj)


def create_permissions():
    """
    Create the can_carry_over and can_admin permissions.
    """
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from pbs.prescription.models import Prescription

    ct = ContentType.objects.get_for_model(Prescription)

    try:
        can_carry_over = Permission.objects.create(
            codename='can_carry_over', name='Can carry over prescriptions', content_type=ct)
    except:
        can_carry_over = Permission.objects.get(codename='can_carry_over')
    try:
        can_admin = Permission.objects.create(
            codename='can_admin', name='Can admin prescriptions', content_type=ct)
    except:
        can_admin = Permission.objects.get(codename='can_admin')
    data_coord = Group.objects.get(name__icontains='Coordinator')
    data_coord.permissions.add(can_carry_over)
    data_coord.permissions.add(can_admin)
    data_coord = Group.objects.get(name__icontains='Coordinator')
    # Regional Fire Coordinator can carry over burns too.
    obj_cust = Group.objects.get(name__icontains='objective custodians')
    obj_cust.permissions.add(can_carry_over)


def support_email(subject, msg, exception=None, msg_type='Warning'):
    if not settings.SUPPORT_EMAIL:
       return

    try:
        env = os.getcwd().split('/')[-1].split('.')[0].split('-')[1].upper() # PROD/UAT/DEV etc
    except:
        env = ''

    subject = 'PBS {}: {} ({})'.format(msg_type, subject, env)
    body = '<p>Subject: {}</p><br><br>{}<br><br>{}'.format(subject, msg, exception)

    message = EmailMessage(subject=subject, body=body, from_email=settings.FROM_EMAIL, to=settings.SUPPORT_EMAIL)
    message.content_subtype = 'html'
    message.send()

