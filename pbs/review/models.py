#from django.db import models
from swingers import models
from datetime import datetime, date, timedelta
from django.contrib.auth.models import User
from pbs.prescription.models import (Prescription, Region, District, Tenure)
from smart_selects.db_fields import ChainedForeignKey
from swingers.models.auth import Audit
from dateutil import tz
from django.utils.encoding import python_2_unicode_compatible

from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms import ValidationError


class BurnState(models.Model):
    prescription = models.ForeignKey(Prescription, related_name='burnstate')
    user = models.ForeignKey(User, help_text="User")
    review_type = models.CharField(max_length=64)
    review_date = models.DateTimeField(auto_now_add=True)

    fmt = "%d/%m/%Y %H:%M:%S"

    @property
    def record(self):
        username = '{} {}'.format(self.user.first_name[0], self.user.last_name)
        return "{} {}".format(
            username, self.review_date.astimezone(tz.tzlocal()).strftime(self.fmt)
        )

    def __str__(self):
        return "{} - {} - {}".format(
            self.prescription, self.review_type, self.record)


#@python_2_unicode_compatible
#class ApprovingRole(models.Model):
#    name = models.CharField(max_length=320)
#
#    def __str__(self):
#        return self.name
#
#    class Meta:
#        ordering = ['name']


@python_2_unicode_compatible
class ExternalAssist(models.Model):
    name = models.CharField(max_length=12)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Fire2(Audit):
    FIRE_ACTIVE = 1
    FIRE_INACTIVE = 2

    APPROVAL_DRAFT = 1
    APPROVAL_SUBMITTED = 2
    APPROVAL_ENDORSED = 3
    APPROVAL_APPROVED = 4
    APPROVAL_CHOICES = (
        (APPROVAL_DRAFT, 'Draft'),
        (APPROVAL_SUBMITTED, 'Submitted'),
        (APPROVAL_ENDORSED, 'Endorsed'),
        (APPROVAL_APPROVED, 'Approved'),
    )

    fire_id = models.CharField(verbose_name="Fire ID?", max_length=10, null=True, blank=True)
    name = models.TextField(verbose_name="Fire Description/Details?", null=True, blank=True)
    region = models.PositiveSmallIntegerField(verbose_name="Fire Region", choices=[(r.id, r.name) for r in Region.objects.all()], null=True, blank=True)
    district = ChainedForeignKey(
        District, chained_field="region", chained_model_field="region",
        show_all=False, auto_choose=True, blank=True, null=True)

    #user = models.ForeignKey(User, help_text="User")
    date = models.DateField(auto_now_add=False)
    active = models.NullBooleanField(verbose_name="Fire Active?", null=True, blank=True)
    #external_assist = models.BooleanField(verbose_name="External Assistance?", blank=True)
    external_assist = models.ManyToManyField(ExternalAssist, blank=True)
    area = models.DecimalField(
        verbose_name="Fire Area (ha)", max_digits=12, decimal_places=1,
        validators=[MinValueValidator(0)], null=True, blank=True)
    tenures = models.ManyToManyField(Tenure, blank=True)
    location= models.TextField(verbose_name="Location", null=True, blank=True)

    submitted_by = models.ForeignKey(User, verbose_name="Submitting User", blank=True, null=True, related_name='fire_submitted_by')
    endorsed_by = models.ForeignKey(User, verbose_name="Endorsing Officer", blank=True, null=True, related_name='fire_endorsed_by')
    approved_by = models.ForeignKey(User, verbose_name="Approving Officer", blank=True, null=True, related_name='fire_approved_by')

    approval_status = models.PositiveSmallIntegerField(
        verbose_name="Approval Status", choices=APPROVAL_CHOICES,
        default=APPROVAL_DRAFT)
    approval_status_modified = models.DateTimeField(
        verbose_name="Approval Status Modified", editable=False, null=True)
    rolled = models.BooleanField(verbose_name="Fire Rolled from yesterday", default=False)


    @property
    def tenures_str(self):
        return ', '.join([t.name for t in self.tenures.all()])

    @property
    def had_external_assist(self):
        if self.external_assist.all().count() > 0:
            return True
        return False

    @property
    def external_assist_str(self):
        return ', '.join([i.name for i in self.external_assist.all()])

    @property
    def status(self):
        if self.active:
            return self.FIRE_ACTIVE
        return self.FIRE_INACTIVE

#    def save(self, **kwargs):
#        super(Fire, self).save(**kwargs)
#        tenures = ', '.join([t.name for t in self.prescription.tenures.all()])
#        if not self.location:
#            self.location = self.prescription.location
#        if not self.tenures and tenures:
#            self.tenures = tenures
#        super(PrescribedBurn, self).save()

    @property
    def can_endorse(self):
        """
        Return true if this fire can be submitted for endorsement.
        """
        return (self.status == self.APPROVAL_SUBMITTED)

    @property
    def can_approve(self):
        """
        Return true if this fire can be submitted for Approval.
        """
        return (self.status == self.APPROVAL_ENDORSED)

    def __str__(self):
        return self.fire_id

    class Meta:
        unique_together = ('fire_id', 'date',)
        verbose_name = 'Fire'
        verbose_name_plural = 'Fires'
        permissions = (
            ("can_endorse", "Can endorse fire actions"),
            ("can_approve", "Can approve fire actions"),
        )

#class Fire(models.Model):
#    fire_id = models.CharField(verbose_name="Fire ID?", max_length=10, null=True, blank=True)
#    name = models.TextField(verbose_name="Fire Description/Details?", null=True, blank=True)
#    region = models.PositiveSmallIntegerField(verbose_name="Fire Region", choices=[(r.id, r.name) for r in Region.objects.all()], null=True, blank=True)
#    district = ChainedForeignKey(
#        District, chained_field="region", chained_model_field="region",
#        show_all=False, auto_choose=True, blank=True, null=True)


@python_2_unicode_compatible
class PrescribedBurn(Audit):
    BURN_ACTIVE = 1
    BURN_INACTIVE = 2
    BURN_COMPLETED = 3
    BURN_CHOICES = (
        (BURN_ACTIVE, 'Active'),
        (BURN_INACTIVE, 'Inactive'),
        (BURN_COMPLETED, 'Completed')
    )

    APPROVAL_DRAFT = 1
    APPROVAL_SUBMITTED = 2
    APPROVAL_ENDORSED = 3
    APPROVAL_APPROVED = 4
    APPROVAL_CHOICES = (
        (APPROVAL_DRAFT, 'Draft'),
        (APPROVAL_SUBMITTED, 'Submitted'),
        (APPROVAL_ENDORSED, 'Endorsed'),
        (APPROVAL_APPROVED, 'Approved'),
    )

    FORM_268A = 1
    FORM_268B = 2
    FORM_NAME_CHOICES = (
        (FORM_268A, 'Form 268a'),
        (FORM_268B, 'Form 268b'),
    )

    fmt = "%Y-%m-%d %H:%M"

    prescription = models.ForeignKey(Prescription, related_name='prescribed_burn', null=True, blank=True)
    #fire = models.ForeignKey(Fire, null=True, blank=True)

    # Required for Fire records
    fire_id = models.CharField(verbose_name="ID", max_length=10, null=True, blank=True)
    fire_name = models.TextField(verbose_name="Name", null=True, blank=True)
    region = models.PositiveSmallIntegerField(choices=[(r.id, r.name) for r in Region.objects.all()], null=True, blank=True)
    district = ChainedForeignKey(
        District, chained_field="region", chained_model_field="region",
        show_all=False, auto_choose=True, blank=True, null=True)

    date = models.DateField(auto_now_add=False)
    form_name = models.PositiveSmallIntegerField(verbose_name="Form Name (268a / 268b)", choices=FORM_NAME_CHOICES, editable=True)

    status = models.PositiveSmallIntegerField(verbose_name="Fire Status", choices=BURN_CHOICES, null=True, blank=True)
#    active = models.NullBooleanField(verbose_name="Burn Active?", null=True, blank=True)

    further_ignitions = models.NullBooleanField(verbose_name="Further ignitions required?")
#    external_assist = models.BooleanField(verbose_name="External Assistance?", blank=True)
    external_assist = models.ManyToManyField(ExternalAssist, blank=True)
    planned_area = models.DecimalField(
        verbose_name="Planned Burn Area (ha)", max_digits=12, decimal_places=1,
        validators=[MinValueValidator(0.0)], null=True, blank=True)
    area = models.DecimalField(
        verbose_name="Area Burnt Yesterday (ha)", max_digits=12, decimal_places=1,
        validators=[MinValueValidator(0.0)], null=True, blank=True)
    tenures= models.TextField(verbose_name="Tenure")
    location= models.TextField(verbose_name="Location", null=True, blank=True)

    est_start = models.TimeField('Estimated Start Time', null=True, blank=True)
    conditions = models.TextField(verbose_name='Special Conditions', null=True, blank=True)

    submitted_by = models.ForeignKey(User, verbose_name="Submitting User", editable=False, blank=True, null=True, related_name='submitted_by')
    submitted_date = models.DateTimeField(editable=False, null=True)
    endorsed_by = models.ForeignKey(User, verbose_name="Endorsing Officer", editable=False, blank=True, null=True, related_name='endorsed_by')
    endorsed_date = models.DateTimeField(editable=False, null=True)
    approved_by = models.ForeignKey(User, verbose_name="Approving Officer", editable=False, blank=True, null=True, related_name='approved_by')
    approved_date = models.DateTimeField(editable=False, null=True)

    approval_status = models.PositiveSmallIntegerField(
        verbose_name="Approval Status", choices=APPROVAL_CHOICES,
        default=APPROVAL_DRAFT)
    approval_status_modified = models.DateTimeField(
        verbose_name="Approval Status Modified", editable=False, null=True)
    rolled = models.BooleanField(verbose_name="Fire Rolled from yesterday", editable=False, default=False)

    def clean_fire_id(self):
        if not self.fire_id or str(self.fire_id)[0] in ('-', '+') or not str(self.fire_id).isdigit():
            raise ValidationError("You must enter numeric digit with 3 characters (001 - 999).")

        if int(self.fire_id)<1 or int(self.fire_id)>999:
            raise ValidationError("Value must be in range (001 - 999).")
#        import ipdb; ipdb.set_trace()

        fire_id = "%s_%s" % (self.district.code, self.fire_id)
        if PrescribedBurn.objects.filter(fire_id=fire_id, date=self.date).count() > 0:
            raise ValidationError("{} already exists for date {}".format(fire_id, self.date))

        self.fire_id = fire_id



        try:
                num=int(self.fir_id)
                print "S contains only digits"
        except:
                print "S doesn't contain digits ONLY"

    def clean_date(self):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        if not self.pk and (self.date < today or self.date > tomorrow):
            raise ValidationError("You must enter burn plans for today or tommorow's date only.")

    def clean_sdo_approve(self):
        """
        Check that status 'Active' and 'Area burnt yesterday' are not Null.
        Cannot approve if data is missing from 268b records
        """
        #TODO - 1254
        pass

    @property
    def fire_type(self):
        return "Burn" if self.prescription else "Fire"

    @property
    def submitted(self):
        return True if self.submitted_by else False

    @property
    def endorsed(self):
        return True if self.endorsed_by else False

    @property
    def approved(self):
        return True if self.approved_by else False

    @property
    def submitted_date_str(self):
        return self.submitted_date.strftime('%Y-%m-%d %H:%M')

    @property
    def endorsed_date_str(self):
        return self.endorsed_date.strftime('%Y-%m-%d %H:%M')

    @property
    def approved_date_str(self):
        return self.approved_date.strftime('%Y-%m-%d %H:%M')

    @property
    def fire_idd(self):
        return self.prescription.burn_id

    @property
    def active(self):
        if self.status==self.BURN_ACTIVE:
            return True
        elif self.status==self.BURN_INACTIVE:
            return False
        return None

    @property
    def completed(self):
        if self.status==self.BURN_COMPLETED:
            return True
        return False

    @property
    def has_conditions(self):
        if self.conditions:
            return True
        return False

    @property
    def tenures_str(self):
        return self.tenures #', '.join([t.name for t in self.tenures.all()])

    @property
    def had_external_assist(self):
        if self.external_assist.all().count() > 0:
            return True
        return False

    @property
    def external_assist_str(self):
        return ', '.join([i.name for i in self.external_assist.all()])

    @property
    def name(self):
        return self.prescription.name

    @property
    def get_region(self):
        return self.prescription.region if self.prescription else self.region

    @property
    def get_district(self):
        return self.prescription.district if self.prescription else self.district

    @property
    def can_endorse(self):
        return (self.status == self.APPROVAL_SUBMITTED)

    @property
    def can_approve(self):
        return (self.status == self.APPROVAL_ENDORSED)

#    def save(self, **kwargs):
#        super(PrescribedBurn, self).save(**kwargs)
#        tenures = self.tenures_str
#        if not self.location:
#            if len(self.prescription.location.split('|')) > 1:
#                tokens = self.prescription.location.split('|')
#                self.location = tokens[1] + 'km ' + tokens[2] + ' of ' + tokens[3]
#            else:
#                self.location = self.prescription.location
#        if not self.tenures and tenures:
#            self.tenures = tenures
#        super(PrescribedBurn, self).save()

    def __str__(self):
        return self.prescription.burn_id if self.prescription else self.fire_id

    class Meta:
        unique_together = ('prescription', 'date', 'form_name',)
        verbose_name = 'Prescribed Burn'
        verbose_name_plural = 'Prescribed Burns'
        permissions = (
            ("can_endorse", "Can endorse burns"),
            ("can_approve", "Can approve burns"),
        )



#class Fire2(Audit):
#
#    fire_id = models.CharField(verbose_name="Fire ID?", max_length=7)
#    name = models.TextField(verbose_name="Fire Description/Details?", null=True, blank=True)
#    region = models.PositiveSmallIntegerField(verbose_name="Fire Region", choices=[(r.id, r.name) for r in Region.objects.all()], null=True, blank=True)
#    district = ChainedForeignKey(
#        District, chained_field="region", chained_model_field="region",
#        show_all=False, auto_choose=True, blank=True, null=True)
#
#    tenures = models.ManyToManyField(Tenure, blank=True)
#    location = models.CharField(
#        help_text="Example: Nollajup Nature Reserve - 8.5 KM S of Boyup Brook",
#        max_length="320", blank=True, null=True)
#    ongoing = models.NullBooleanField(verbose_name="Fire Status (Ongoing/Closed)", default=True)
#
##    class Meta:
##        unique_together = ('fire_id', 'created',)
#
#
#class FireLoad(Audit):
#    FIRE_PLANNED = 0
#    FIRE_ACTIVE = 1
#    FIRE_INACTIVE = 2
#    FIRE_COMPLETED = 3
#    FIRE_CHOICES = (
#        (FIRE_PLANNED, 'Planned'),
#        (FIRE_ACTIVE, 'Active'),
#        (FIRE_INACTIVE, 'Inactive'),
#        (FIRE_COMPLETED, 'Completed')
#    )
#
#    APPROVAL_DRAFT = 1
#    APPROVAL_SUBMITTED = 2
#    APPROVAL_ENDORSED = 3
#    APPROVAL_APPROVED = 4
#    APPROVAL_CHOICES = (
#        (APPROVAL_DRAFT, 'Draft'),
#        (APPROVAL_SUBMITTED, 'Submitted'),
#        (APPROVAL_ENDORSED, 'Endorsed'),
#        (APPROVAL_APPROVED, 'Approved'),
#    )
#
#    prescription = models.ForeignKey(Prescription, related_name='fireload', null=True, blank=True)
#    fire = models.ForeignKey(Fire2, related_name='fire', null=True, blank=True)
#    date = models.DateField(auto_now_add=False)
#
#    status = models.PositiveSmallIntegerField(verbose_name="Fire Status", choices=FIRE_CHOICES, null=True, blank=True)
##    active = models.NullBooleanField(verbose_name="Burn Active?", null=True, blank=True)
#
#    further_ignitions = models.BooleanField(verbose_name="Further ignitions required?")
#    external_assist = models.ManyToManyField(ExternalAssist, blank=True)
#    area = models.DecimalField(
#        verbose_name="Area Achieved Yesterday (ha)", max_digits=12, decimal_places=1,
#        validators=[MinValueValidator(0.1)], null=True, blank=True)
#
#    est_start = models.TimeField('Estimated Start Time')
#    conditions = models.TextField(verbose_name='Special Conditions', null=True, blank=True)
#
#    submitted_by = models.ForeignKey(User, verbose_name="Submitting User", blank=True, null=True, related_name='burn_submitted_by')
#    endorsed_by = models.ForeignKey(User, verbose_name="Endorsing Officer", blank=True, null=True, related_name='burn_endorsed_by')
#    approved_by = models.ForeignKey(User, verbose_name="Approving Officer", blank=True, null=True, related_name='burn_approved_by')
#
#    approval_status = models.PositiveSmallIntegerField(
#        verbose_name="Approval Status", choices=APPROVAL_CHOICES,
#        default=APPROVAL_DRAFT)
#    approval_status_modified = models.DateTimeField(
#        verbose_name="Approval Status Modified", editable=False, null=True)
#
#    def __str__(self):
#        return self.prescription.burn_id
#
#    class Meta:
#        unique_together = ('prescription', 'date',)
#        verbose_name = 'Prescribed Burn'
#        verbose_name_plural = 'Prescribed Burns'
#        permissions = (
#            ("can_endorse", "Can endorse burns"),
#            ("can_approve", "Can approve burns"),
#        )
#
