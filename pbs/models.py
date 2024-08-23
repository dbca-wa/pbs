from django.contrib.auth.models import User, Group
from django.conf import settings
from django.db import models
from django.db import connection
from django.db.models.signals import post_save

from pbs.prescription.models import Region, District
from smart_selects.db_fields import ChainedForeignKey

import logging
logger = logging.getLogger("log." + __name__)


class Profile(models.Model):
    DEFAULT_GROUP = "Users"

    user = models.OneToOneField(User, on_delete=models.PROTECT)
    region = models.ForeignKey(Region, blank=True, null=True, on_delete=models.PROTECT)
    district = ChainedForeignKey(District,
        chained_field="region", chained_model_field="region",
        show_all=False, auto_choose=True, blank=True, null=True,
        on_delete=models.PROTECT)

    def is_fpc_user(self):
        return self.user.email.lower().endswith(settings.FPC_EMAIL_EXT)


def user_post_save(sender, instance, created, **kwargs):
    """Create a user profile when a new user account is created"""
    if (created and
            Profile._meta.db_table in connection.introspection.table_names()):
        p = Profile()
        p.user = instance
        p.save()

        # add the default user group (fail_silently=True)
        try:
            group = Group.objects.get(name__iexact=p.DEFAULT_GROUP)
        except Group.DoesNotExist:
            logger.warning("Failed to assign group `%s' to user `%s', "
                           "group `%s' does not exist.", p.DEFAULT_GROUP,
                           p.user.username, p.DEFAULT_GROUP)
        else:
            p.user.groups.add(group)

post_save.connect(user_post_save, sender=User)


def prescription_modified(sender, instance, created, **kwargs):
    if hasattr(instance, 'prescription'):
        prescription = instance.prescription
        if prescription is not None:
            prescription.save()     # update the modified and modifier fields

post_save.connect(prescription_modified)
