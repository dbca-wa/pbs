from __future__ import (division, print_function, unicode_literals,
                        absolute_import)
import logging
logger = logging.getLogger("log." + __name__)

from swingers.models.auth import Audit

from django.db import models
from django.utils import timezone

from pbs.prescription.models import Prescription



class CriticalStakeholder(Audit):
    prescription = models.ForeignKey(Prescription, on_delete=models.PROTECT)
    name = models.CharField(max_length=320)
    organisation = models.CharField(max_length=320)
    interest = models.TextField()

    _required_fields = ('name', 'organisation', 'interest')

    class Meta:
        verbose_name = "Critical Stakeholder"
        verbose_name_plural = "Critical Stakeholders"
        ordering = ['id']

    def __str__(self):
        return self.name


class PublicContact(Audit):
    prescription = models.ForeignKey(Prescription, on_delete=models.PROTECT)
    name = models.CharField(max_length=320)
    organisation = models.TextField()
    person = models.TextField(verbose_name="DPaW Person")
    comments = models.TextField()

    class Meta:
        verbose_name = "Public Contact"
        verbose_name_plural = "Public Contacts"



class Notification(Audit):
    ORG_BEEKEEPERS = 1
    ORG_NEIGHBOURS = 2
    ORG_FLORA_PICKERS = 3
    ORG_COMMERCIAL_OPS = 4
    ORG_RADIO_STATIONS = 5
    ORG_SIGNIFICANT_STAKEHOLDERS = 6
    ORG_OTHER = 7

    ORG_CHOICES = (
        (ORG_BEEKEEPERS, 'Beekeepers'),
        (ORG_NEIGHBOURS, 'Neighbours'),
        (ORG_FLORA_PICKERS, 'Flora Pickers'),
        (ORG_COMMERCIAL_OPS, 'Commercial Operators'),
        (ORG_RADIO_STATIONS, 'Radio Stations'),
        (ORG_SIGNIFICANT_STAKEHOLDERS, 'Significant Stakeholders'),
        (ORG_OTHER, 'Other')
    )

    prescription = models.ForeignKey(Prescription, on_delete=models.PROTECT)
    notified = models.DateField(verbose_name="Date of Notification")
    contacted = models.TextField(verbose_name="Person Contacted")
    organisation = models.PositiveSmallIntegerField(
        verbose_name="Organisation Type", choices=ORG_CHOICES)
    address = models.TextField()
    phone = models.CharField(max_length=320)

    def __str__(self):
        return "%s - %s" % (self.prescription.burn_id, self.organisation)

import reversion
reversion.register(CriticalStakeholder)