from __future__ import (division, print_function, unicode_literals,
                        absolute_import)
import logging
logger = logging.getLogger("log." + __name__)

from swingers.models.auth import Audit
from swingers import models
#from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import F
from django.db.models.signals import post_save, post_delete
from django.db.models.query import QuerySet
from django.dispatch import receiver
from django.template.defaultfilters import truncatewords
# from django.utils.encoding import python_2_unicode_compatible
# from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_lazy as _
from unidecode import unidecode


SMEAC_SITUATION = 1
SMEAC_MISSION = 2
SMEAC_EXECUTION = 3
SMEAC_ADMINISTRATION = 4
SMEAC_COMMAND = 5
SMEAC_SAFETY = 6

SMEAC_CHOICES = (
    (SMEAC_SITUATION, "Situation"),
    (SMEAC_MISSION, "Mission"),
    (SMEAC_EXECUTION, "Execution"),
    (SMEAC_ADMINISTRATION, "Administration & Logistics"),
    (SMEAC_COMMAND, "Command & Communications"),
    (SMEAC_SAFETY, "Safety"),
)


class RiskCategoryManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class RiskCategory(models.Model):
    name = models.CharField(
        verbose_name="Potential Source of Risk Category", max_length=200)
    objects = RiskCategoryManager()

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    class Meta:
        ordering = ['name']
        verbose_name = 'Potential Source of Risk Category'
        verbose_name_plural = "Potential Source of Risk Categories"



class Risk(Audit):
    """
    Standard set of risks to be created on every prescription.
    """
    RISK_UNASSESSED = 1
    RISK_UNCERTAINTY = 2
    RISK_ASSUMPTION = 3
    RISK_NOT_APPLICABLE = 4
    RISK_CHOICES = (
        (RISK_UNASSESSED, "Unassessed"),
        (RISK_UNCERTAINTY, "Uncertainty"),
        (RISK_ASSUMPTION, "Assumption"),
        (RISK_NOT_APPLICABLE, "Not Applicable"),
    )

    prescription = models.ForeignKey(
        'prescription.Prescription',
        help_text="Prescription this issue belongs to.",
        blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(
        max_length=100, verbose_name="Potential Source of Risk")
    category = models.ForeignKey(RiskCategory, on_delete=models.PROTECT)
    risk = models.PositiveSmallIntegerField(
        choices=RISK_CHOICES, default=RISK_UNASSESSED)
    custom = models.BooleanField(
        default=True, verbose_name="Non standard source of risk",
        help_text="Is this a non standard source of risk?")

    def __str__(self):
        return unidecode(self.name)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Potential Source of Risk'
        verbose_name = "Potential Sources of Risk"


class Context(Audit):
    prescription = models.ForeignKey(
        'prescription.Prescription',
        help_text="Prescription this issue belongs to.", on_delete=models.PROTECT)
    statement = models.TextField(verbose_name="Context Statement", blank=True)

    _required_fields = ('statement', )

    def __str__(self):
        return self.statement

    class Meta:
        verbose_name = "Context Statement Item"
        verbose_name_plural = "Context Statement Items"
        ordering = ['pk']



class Action(Audit):
    RESOLUTION_NO = "No"
    RESOLUTION_YES = "Yes"
    RESOLUTION_EXPLANATION = "Explanation"
    RESOLUTION_CHOICES = (
        (RESOLUTION_NO, "No"),
        (RESOLUTION_YES, "Yes, as planned"),
        (RESOLUTION_EXPLANATION, "Yes, with explanation"),
    )

    RESPONSIBLE_IC = "IC"
    RESPONSIBLE_OPS = "OPS"
    RESPONSIBLE_CHOICES = (
        (RESPONSIBLE_IC, "IC"),
        (RESPONSIBLE_OPS, "OPS"),
    )

    SMEAC_MAP = (
        ('day_of_burn_situation', 'Situation'),
        ('day_of_burn_mission', 'Mission'),
        ('day_of_burn_execution', 'Execution'),
        ('day_of_burn_administration', 'Administration and Logistics'),
        ('day_of_burn_command', 'Command and Communications'),
        ('day_of_burn_safety', 'Safety'),
    )

    risk = models.ForeignKey(Risk, verbose_name='Potential Source of Risk', on_delete=models.PROTECT)
    relevant = models.BooleanField(
        verbose_name="Action Relevant?",
        default=True, help_text="Include in Action List")
    pre_burn = models.BooleanField(default=False)
    details = models.TextField(
        verbose_name="Action Details", blank=True)
    pre_burn_resolved = models.CharField(
        choices=RESOLUTION_CHOICES, default=RESOLUTION_NO,
        verbose_name="Issue Resolved", max_length=200, blank=True)
    pre_burn_completer = models.TextField(
        verbose_name="Actioned By Whom", null=True, blank=True)
    pre_burn_completed = models.DateTimeField(
        verbose_name="Date Actioned", null=True, blank=True, default=None)
    pre_burn_explanation = models.TextField(
        verbose_name="Explanation", blank=True)
    day_of_burn = models.BooleanField(default=False)
    day_of_burn_responsible = models.CharField(_("Responsible"),
        max_length=200, choices=RESPONSIBLE_CHOICES, default=RESPONSIBLE_IC)
    day_of_burn_completer = models.TextField(
        verbose_name="Actioned By Whom", null=True, blank=True)
    day_of_burn_completed = models.DateTimeField(
        verbose_name="Date Actioned",
        null=True, blank=True, default=None)
    day_of_burn_include = models.BooleanField(
        verbose_name="Include in Briefing?", default=False)
    day_of_burn_situation = models.BooleanField(
        verbose_name='S', default=False)
    day_of_burn_mission = models.BooleanField(
        verbose_name='M', default=False)
    day_of_burn_execution = models.BooleanField(
        verbose_name='E', default=False)
    day_of_burn_administration = models.BooleanField(
        verbose_name='A', default=False)
    day_of_burn_command = models.BooleanField(
        verbose_name='C', default=False)
    day_of_burn_safety = models.BooleanField(
        verbose_name='S', default=False)
    post_burn = models.BooleanField(default=False)
    post_burn_completer = models.TextField(
        verbose_name="Actioned By Whom", null=True, blank=True)
    post_burn_completed = models.DateTimeField(
        verbose_name="Date Actioned", null=True, blank=True, default=None)
    context_statement = models.BooleanField(
        verbose_name="Relevant to Context Statement?", default=False)
    index = models.PositiveSmallIntegerField(
        default=1, editable=False, verbose_name="Index of this action",
        help_text="Index of this action in the set of actions for this risk")
    total = models.PositiveSmallIntegerField(
        default=1, editable=False,
        verbose_name="Total number of actions for this risk")

    _required_fields = ('details', 'pre_burn_resolved',
                        'pre_burn_explanation', 'pre_burn_completed',
                        'pre_burn_completer', 'day_of_burn_include',
                        'day_of_burn_completer', 'day_of_burn_completed',
                        'post_burn_completer', 'post_burn_completed')

    class Meta:
        ordering = ['risk__category', '-relevant', 'risk__name', 'pk']

    @property
    def prescription(self):
        return self.risk.prescription

    def __str__(self):
        if self.total == 1:
            return self.risk.name
        else:
            return "%s (%s of %s)" % (self.risk.name, self.index, self.total)

    @property
    def smeac(self):
        output = ["S", "M", "E", "A", "C", "S"]
        for index, val in enumerate([
            self.day_of_burn_situation,
            self.day_of_burn_mission,
            self.day_of_burn_execution,
            self.day_of_burn_administration,
            self.day_of_burn_command,
            self.day_of_burn_safety
        ]):
            if not val:
                output[index] = "-"
        return " ".join(output)

    def clean_day_of_burn_include(self):
        if ((self.day_of_burn_include and
             not any([self.day_of_burn_situation, self.day_of_burn_mission,
                      self.day_of_burn_execution,
                      self.day_of_burn_administration,
                      self.day_of_burn_command, self.day_of_burn_safety]))):
            raise ValidationError('Please select at least one SMEACS location.')

    def _clean_burn_completed(self, completed, completer):
        prescription = self.risk.prescription
        if ((completed and (
             # just for the shell_plus hackers :)
             not prescription.approval_status_modified or
             prescription.approval_status != prescription.APPROVAL_APPROVED or
             completed < prescription.approval_status_modified)
             )):
            raise ValidationError('The action cannot be actioned before the ' +
                                  'approval of this ePFP.')

        if (completer and not completed):
            raise ValidationError('Please set when this action was actioned.')

    def clean_day_of_burn_completed(self):
        self._clean_burn_completed(self.day_of_burn_completed,
                                   self.day_of_burn_completer)

    def clean_post_burn_completed(self):
        self._clean_burn_completed(self.post_burn_completed,
                                   self.post_burn_completer)

    def clean_pre_burn_completed(self):
        #self._clean_burn_completed(self.pre_burn_completed,
        #                           self.pre_burn_completer)
        """
        Pre burn can be actionned at any time - PBS-1567
        """
        pass

    def _clean_completer(self, completed, completer):
        if (completed and not completer):
            raise ValidationError('Please set whom this action was ' +
                                  'actioned by.')

    def clean_day_of_burn_completer(self):
        self._clean_completer(self.day_of_burn_completed,
                              self.day_of_burn_completer)

    def clean_post_burn_completer(self):
        self._clean_completer(self.post_burn_completed,
                              self.post_burn_completer)

    def clean_pre_burn_completer(self):
        self._clean_completer(self.pre_burn_completed,
                              self.pre_burn_completer)


class ContextRelevantAction(Audit):
    action = models.OneToOneField(
        Action, related_name="context_considered",
        verbose_name=("Action relevant for context statement"), on_delete=models.PROTECT)
    considered = models.BooleanField(
        default=False, verbose_name="Considered?",
        help_text=("Has this action been considered as part of writing the "
                   "context statement?"))

    @property
    def prescription(self):
        return self.action.prescription



class Register(Audit):
    CONSEQUENCE_LOW = 1
    CONSEQUENCE_HIGH = 2
    CONSEQUENCE_VERY_HIGH = 3
    CONSEQUENCE_SEVERE = 4
    CONSEQUENCE_EXTREME = 5
    CONSEQUENCE_CATASTROPHIC = 6
    CONSEQUENCE_CHOICES = (
        (CONSEQUENCE_LOW, '1'),
        (CONSEQUENCE_HIGH, '2'),
        (CONSEQUENCE_VERY_HIGH, '3'),
        (CONSEQUENCE_SEVERE, '4'),
        (CONSEQUENCE_EXTREME, '5'),
        (CONSEQUENCE_CATASTROPHIC, '6'),
    )
    LIKELIHOOD_RARE = 1
    LIKELIHOOD_UNLIKELY = 2
    LIKELIHOOD_POSSIBLE = 3
    LIKELIHOOD_LIKELY = 4
    LIKELIHOOD_CERTAIN = 5
    LIKELIHOOD_CHOICES = (
        (LIKELIHOOD_RARE, 'Rare'),
        (LIKELIHOOD_UNLIKELY, 'Unlikely'),
        (LIKELIHOOD_POSSIBLE, 'Possible'),
        (LIKELIHOOD_LIKELY, 'Likely'),
        (LIKELIHOOD_CERTAIN, 'Almost Certain'),
    )

    LEVEL_VERY_LOW = 1
    LEVEL_LOW = 2
    LEVEL_MEDIUM = 3
    LEVEL_HIGH = 4
    LEVEL_VERY_HIGH = 5
    LEVEL_CHOICES = (
        (LEVEL_VERY_LOW, 'Very Low'),
        (LEVEL_LOW, 'Low'),
        (LEVEL_MEDIUM, 'Medium'),
        (LEVEL_HIGH, 'High'),
        (LEVEL_VERY_HIGH, 'Very High'),
    )

    # we can't simply multiply the levels as the matrix doesn't quite work
    # like that.
    RISK_MATRIX = [
        [LEVEL_VERY_LOW, LEVEL_VERY_LOW, LEVEL_LOW, LEVEL_LOW, LEVEL_MEDIUM,
         LEVEL_MEDIUM],
        [LEVEL_VERY_LOW, LEVEL_LOW, LEVEL_LOW, LEVEL_MEDIUM, LEVEL_MEDIUM,
         LEVEL_HIGH],
        [LEVEL_LOW, LEVEL_LOW, LEVEL_MEDIUM, LEVEL_MEDIUM, LEVEL_HIGH,
         LEVEL_HIGH],
        [LEVEL_LOW, LEVEL_MEDIUM, LEVEL_MEDIUM, LEVEL_HIGH, LEVEL_HIGH,
         LEVEL_VERY_HIGH],
        [LEVEL_MEDIUM, LEVEL_MEDIUM, LEVEL_HIGH, LEVEL_HIGH, LEVEL_VERY_HIGH,
         LEVEL_VERY_HIGH],
    ]

    prescription = models.ForeignKey(
        'prescription.Prescription',
        help_text="Prescription this risk register item belongs to.", on_delete=models.PROTECT)
    description = models.TextField(
        verbose_name="Risk Description", blank=True)
    draft_consequence = models.PositiveSmallIntegerField(
        choices=CONSEQUENCE_CHOICES, default=CONSEQUENCE_CATASTROPHIC,
        verbose_name="Consequence", blank=True)
    draft_likelihood = models.PositiveSmallIntegerField(
        choices=LIKELIHOOD_CHOICES, default=LIKELIHOOD_CERTAIN,
        verbose_name="Likelihood", blank=True)
    draft_risk_level = models.PositiveSmallIntegerField(
        choices=LEVEL_CHOICES, editable=False,
        default=LEVEL_VERY_HIGH, verbose_name="Draft ePFP Risk Level")
    alarp = models.BooleanField(
        default=False, verbose_name="As Low As Reasonably Practicable?")
    final_consequence = models.PositiveSmallIntegerField(
        choices=CONSEQUENCE_CHOICES, default=CONSEQUENCE_VERY_HIGH,
        verbose_name="Revised Consequence", blank=True)
    final_likelihood = models.PositiveSmallIntegerField(
        choices=LIKELIHOOD_CHOICES, default=LIKELIHOOD_CERTAIN,
        verbose_name="Revised Likelihood", blank=True)
    final_risk_level = models.PositiveSmallIntegerField(
        choices=LEVEL_CHOICES, editable=False,
        default=LEVEL_VERY_HIGH, verbose_name="Final ePFP Risk Level")

    _required_fields = ('description', 'draft_consequence',
                        'draft_likelihood', 'treatments',
                        'final_consequence', 'final_likelihood')

    def save(self, **kwargs):
        """
        Update the draft risk level and the final risk level based on each of
        the likelihoods and consequences.
        """
        # we have to do this as we want to store the levels as 1-indexed,
        # but we are referencing the risk matrix array that is 0-indexed.
        if not self.draft_likelihood:
            self.draft_likelihood = self.LIKELIHOOD_CERTAIN
        if not self.draft_consequence:
            self.draft_consequence = self.CONSEQUENCE_VERY_HIGH

        draft_likelihood = self.draft_likelihood - 1
        draft_consequence = self.draft_consequence - 1
        self.draft_risk_level = self.RISK_MATRIX[draft_likelihood][draft_consequence]

        # If the risk level is ALARP or saved from DRAFT page,
        # copy the draft attributes across to the final attributes.
        if ((self.alarp or self.pk is None or
             (self.final_likelihood == self._initial['final_likelihood'] and
              self.final_consequence == self._initial['final_consequence']))):
            self.final_likelihood = self.draft_likelihood
            self.final_consequence = self.draft_consequence
            self.final_risk_level = self.draft_risk_level
        else:
            if not self.final_likelihood:
                self.final_likelihood = self.LIKELIHOOD_CERTAIN
            if not self.final_consequence:
                self.final_consequence = self.CONSEQUENCE_VERY_HIGH
            final_likelihood = self.final_likelihood - 1
            final_consequence = self.final_consequence - 1
            self.final_risk_level = self.RISK_MATRIX[final_likelihood][final_consequence]

        if self.alarp and self.treatment_set.count() > 0:
            self.treatment_set.all().delete()

        super(Register, self).save(**kwargs)

    def __str__(self):
        return '{0} - {1}'.format(self.pk, truncatewords(self.description, 7))

    class Meta:
        ordering = ('pk', )
        verbose_name = 'Risk Register Item'
        verbose_name_plural = 'Risk Register Items'


class TreatmentLocationManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)



class TreatmentLocation(models.Model):
    name = models.CharField(max_length=200)
    objects = TreatmentLocationManager()

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    class Meta:
        ordering = ['name']


# Haha, this kind of makes having TreatmentLocation in the database a bit
# redundant. Could always refactor it out of the database later.
LOCATION_MAPPING = {
    'excluded_areas': 'Areas To Be Excluded',
    'contingency_plan': 'Contingency Plan',
    'dob_action': 'Day of Burn Action',
    'dob_briefing': 'Day of Burn Briefing',
    'edging_plan': 'Edging Plan',
    'fuel_schedule': 'Burning Prescription',
    'lighting_plan': 'Lighting Sequence',
    'post_action': 'Post Burn Action',
    'pre_action': 'Pre-Burn Action',
    'traffic_plan': 'Traffic Management Plan'
}


class TreatmentQuerySet(QuerySet):
    def __getattr__(self, name):
        if name in LOCATION_MAPPING.keys():
            return self.filter(location__name=LOCATION_MAPPING[name])
        elif hasattr(self, name):
            return getattr(self, name)
        else:
            raise AttributeError


class TreatmentManager(models.Manager):
    #use_for_related_fields = True

    def get_queryset(self):
        return TreatmentQuerySet(self.model, using=self._db)

    #This function was getting Recursion error so modifying it
    # def __getattr__(self, name):
    #     if name in LOCATION_MAPPING.keys():
    #         return getattr(self.get_query_set(), name)
    #     elif hasattr(self, name):
    #         return getattr(self, name)
    #     else:
    #         raise AttributeError

    def __getattr__(self, name):
        if name in LOCATION_MAPPING.keys():
            return getattr(self.get_query_set(), name)
        try:
            return  super().__getattr__(name)
        except:
            raise AttributeError



class Treatment(Audit):
    register = models.ForeignKey(Register, on_delete=models.PROTECT)
    description = models.TextField()
    location = models.ForeignKey(TreatmentLocation, on_delete=models.PROTECT)
    complete = models.BooleanField(verbose_name="Dealt With?", default=False)
    objects = TreatmentManager()

    def __str__(self):
        return self.description

    @property
    def prescription(self):
        return self.register.prescription



class Contingency(Audit):
    '''This model is intended to replace the Contingency model, above.
    The Contingency model should be manually migrated by users to the new
    version.
    '''
    prescription = models.ForeignKey(
        'prescription.Prescription',
        help_text="Prescription this objective belongs to.", on_delete=models.PROTECT)
    description = models.TextField(
        help_text="Contingency Details", verbose_name="Contingency")
    trigger = models.TextField(help_text="Trigger")
    # The fields below here have been deprecated in favour of using
    # the ContingencyAction and ContingencyNotification models.
    # These field will be removed in a future release when all existing
    # objects have their data manually migrated to the new models.
    # The boolean fields are intended as filters to assist staff to
    # migrate the data.
    actions_migrated = models.BooleanField(default=True)
    action = models.TextField(help_text="List of Actions", blank=True, null=True)
    notifications_migrated = models.BooleanField(default=True)
    notify_name = models.TextField(
        verbose_name="Notify (Name)", blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    organisation = models.TextField(blank=True, null=True)
    contact_number = models.TextField(blank=True, null=True)


    _required_fields = ('description', 'trigger')

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['id']
        verbose_name = "Contingency"
        verbose_name_plural = "Contingencies"

    @property
    def subitems(self):
        subitems = []
        notify_name = self.notify_name or ""
        organisation = self.organisation or ""
        location = self.location or ""
        contact_number = self.contact_number or ""
        for key, value in {
            "notify_name": notify_name.split("\n"),
            "organisation": organisation.split("\n"),
            "location": location.split("\n"),
            "contact_number": contact_number.split("\n")
        }.iteritems():
            for index, item in enumerate(value):
                if index < len(subitems):
                    subitems[index].update({key: item})
                else:
                    subitems.append({key: item})
        return subitems



class ContingencyAction(Audit):
    contingency = models.ForeignKey(Contingency, related_name='actions', on_delete=models.PROTECT)
    action = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.action



class ContingencyNotification(Audit):
    contingency = models.ForeignKey(Contingency, related_name='notifications', on_delete=models.PROTECT)
    name = models.CharField(max_length=100, verbose_name='Notify (Name)',
        blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    organisation = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return '{0} ({1}) - {2}'.format(self.name, self.organisation,
            self.contact_number)

    class Meta:
        ordering = ['name']



class Complexity(Audit):
    RATING_UNRATED = 0
    RATING_LOW = 2
    RATING_MEDIUM = 3
    RATING_HIGH = 4
    RATING_CHOICES = (
        (RATING_UNRATED, 'Unrated'),
        (RATING_LOW, 'Low'),
        (RATING_MEDIUM, 'Medium'),
        (RATING_HIGH, 'High'),
    )

    prescription = models.ForeignKey(
        'prescription.Prescription',
        help_text="Prescription this Complexity belongs to.",
        blank=True, null=True, on_delete=models.PROTECT)
    factor = models.CharField(max_length=64)
    sub_factor = models.CharField(
        verbose_name="Sub-factor", max_length=64)
    order = models.PositiveSmallIntegerField(default=0)
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES, default=RATING_UNRATED,
        verbose_name="Complexity Rating")
    rationale = models.TextField(
        verbose_name="Complexity Rationale", blank=True)

    _required_fields = ('rating', 'rationale',)

    def __str__(self):
        return self.sub_factor

    def save(self, **kwargs):
        """
        Update the SummaryCompletionState object associated with the parent
        Prescription if the complexity rating is set as 'Unrated' or the
        rationale is blank.
        """
        if self.rating == self.RATING_UNRATED or not self.rationale:
            self.prescription.pre_state.complexity_analysis = False
            self.prescription.pre_state.save()
        super(Complexity, self).save(**kwargs)

    class Meta:
        ordering = ['order']
        verbose_name = "Complexity Analysis Item"
        verbose_name_plural = "Complexity Analysis Items"


@receiver(post_save, sender=Action)
def update_index_total_save(sender, instance, created, **kwargs):
    if created:
        logger.debug("Updating indexes for risk '%s'" % instance.risk)
        actions = Action.objects.filter(risk=instance.risk)
        total = actions.count()
        if total > 1:
            last_action = actions.order_by("-index")[0]
            instance.index = last_action.index + 1
            instance.total = total
            instance.save()
        num_updated = actions.update(total=total)
        logger.debug("%d actions updated." % num_updated)


@receiver(post_save, sender=Action)
def update_context_relevant_actions_save(sender, instance, created, **kwargs):
    if instance.context_statement:
        ContextRelevantAction.objects.get_or_create(action=instance)
        # If the context statement has already been marked as complete,
        # revert it back to incomplete as a new relevant action has been
        # identified.
        prescription = instance.risk.prescription
        if (prescription.pre_state.context_statement and
            prescription.endorsement_status == prescription.ENDORSEMENT_DRAFT):
            pre_state = prescription.pre_state
            pre_state.context_statement = False
            pre_state.save()
    else:
        ContextRelevantAction.objects.filter(action=instance).delete()


@receiver(post_delete, sender=Action)
def update_index_total_delete(sender, instance, **kwargs):
    actions = Action.objects.filter(risk=instance.risk_id).order_by("index")
    for index, action in enumerate(actions):
        action.index = index + 1
        action.total = F('total') - 1
        action.save()

import reversion
reversion.register(Risk)
reversion.register(Context)
reversion.register(Action)
reversion.register(Register)
reversion.register(Contingency)
reversion.register(Complexity)