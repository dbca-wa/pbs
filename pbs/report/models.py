from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.validators import MinValueValidator

from swingers.models.auth import Audit
from swingers import models

from pbs.prescription.models import Prescription, SuccessCriteria
from pbs.risk.models import Complexity, Context, ContextRelevantAction, Action
from pbs.implementation.models import IgnitionType, RoadSegment, TrailSegment
# from pbs.report._models.day_of_burn import DayOfBurnReadEvent, DayOfBurnReviewedEvent

import logging

log = logging.getLogger(__name__)


class AbstractState(Audit):
    """
    Add some helper functions to our state models to track progress.
    """
    def __init__(self, *args, **kwargs):
        self._total_steps = None
        self._complete_steps = None
        super(AbstractState, self).__init__(*args, **kwargs)

    def _get_fields(self):
        return filter(lambda x: isinstance(x, models.NullBooleanField) or
                      isinstance(x, models.BooleanField), self._meta.fields)

    def _total(self):
        """
        Return the total number of steps.
        """
        if self._total_steps is None:
            total = 0
            for field in self._get_fields():
                if getattr(self, field.name) is None:
                    continue
                total += 1
            self._total_steps = total
        return self._total_steps
    total = property(_total)

    def _complete(self):
        """
        Return the total number of complete steps.
        """
        if self._complete_steps is None:
            complete = 0
            for field in self._get_fields():
                if getattr(self, field.name):
                    complete += 1
            self._complete_steps = complete
        return self._complete_steps
    complete = property(_complete)

    def _progress(self):
        """
        Calculate the progress in percent of this part of the ePFP.
        """
        return int(self.complete / self.total * 100)
    progress = property(_progress)

    def _finished(self):
        return self.total == self.complete
    finished = property(_finished)

    class Meta:
        abstract = True


BOOL_CHOICES = (
    (False, 'Incomplete'),
    (True, 'Complete')
)

NULL_CHOICES = (
    (None, 'Not applicable'),
    (False, 'Incomplete'),
    (True, 'Complete'),
)


class SummaryCompletionState(AbstractState):
    """
    Stores state related to Part A (Summary & Approval) section of an
    electronic Prescribed Fire Plan. These flags are to indicate if each
    section has been fully completed.
    """
    prescription = models.OneToOneField(
        Prescription, related_name='pre_state', on_delete=models.PROTECT)
    summary = models.BooleanField(choices=BOOL_CHOICES, default=False)
    context_statement = models.BooleanField(
        choices=BOOL_CHOICES, default=False)
    context_map = models.BooleanField(choices=BOOL_CHOICES, default=False)
    objectives = models.BooleanField(choices=BOOL_CHOICES, default=False)
    success_criteria = models.BooleanField(choices=BOOL_CHOICES, default=False)
    priority_justification = models.BooleanField(
        choices=BOOL_CHOICES, default=False)
    complexity_analysis = models.BooleanField(
        choices=BOOL_CHOICES, default=False)
    risk_register = models.BooleanField(choices=BOOL_CHOICES, default=False)

    @property
    def complete_except_risk(self):
        """
        Return True if all sections of part A are marked complete except for
        risk_register.
        """
        return (self.summary and self.context_statement and self.context_map
                and self.objectives and self.success_criteria and
                self.priority_justification and self.complexity_analysis)

    def clean_context_map(self):
        """
        BR-16: For the Part A Stage of Completion Table, the Context map can
        not be marked as "Complete" unless a context map is uploaded.
        """
        documents = self.prescription.document_set
        count = documents.tag_names("Context Map").count()
        if self.context_map and count < 1:
            self.context_map = False
            self.save()
            raise ValidationError("To mark the context map as complete you "
                                  "first need to upload a context map")

    def clean_priority_justification(self):
        if self.priority_justification:
            justifications = self.prescription.priorityjustification_set
            justifications = justifications.filter(relevant=True)
            blankrationale = justifications.filter(rationale='').count()
            unratedpriority = justifications.filter(priority=0).count()
            if blankrationale > 0 or unratedpriority > 0:
                raise ValidationError("To mark the priority justification "
                                      "as complete you need to set the "
                                      "priority and enter a rationale for "
                                      "each relevant burn purpose.")
            if ((self.prescription.priority == 0 or
                 self.prescription.rationale == '')):
                raise ValidationError("To mark the priority justification "
                                      "as complete you need to set the "
                                      "overall priority and rationale for "
                                      "the burn.")

    def clean_summary(self):
        if self.summary:
            if (self.prescription.priority < 1 or self.prescription.rationale == ''):
                raise ValidationError("To mark the summary and approval as "
                                      "complete you must set the overall priority "
                                      "and enter a rationale.")
            if not self.prescription.fuel_types.exists():
                raise ValidationError("To mark the summary and approval as "
                                      "complete you must set the fuel type(s).")
            if not self.prescription.tenures.exists():
                raise ValidationError("To mark the summary and approval as "
                                      "complete you must set the burn tenures(s).")
            if not self.prescription.forecast_areas.exists():
                raise ValidationError("To mark the summary and approval as "
                                      "complete you must set the forecast area(s).")
            if not self.prescription.shires.exists():
                raise ValidationError("To mark the summary and approval as "
                                      "complete you must set the Shire(s).")
            if not self.prescription.prohibited_period:
                raise ValidationError("To mark the summary and approval as "
                                      "complete you must input the Prohibited Period.")
            if not self.prescription.short_code:
                raise ValidationError("To mark the summary and approval as "
                                      "complete you must input the Short Code.")

    def clean_objectives(self):
        objectives = self.prescription.objective_set.count()
        if self.objectives and objectives < 1:
            self.objectives = False
            self.save()
            raise ValidationError("To mark the burn objectives as complete "
                                  "you need to specify at least one burn "
                                  "objective.")

    def clean_complexity_analysis(self):
        not_rated = Complexity.objects.filter(
            prescription=self.prescription,
            rating=Complexity.RATING_UNRATED).exists()

        no_rationale = Complexity.objects.filter(
            prescription=self.prescription,
            rationale='').exists()

        if self.complexity_analysis and (not_rated or no_rationale):
            self.complexity_analysis = False
            self.save()
            raise ValidationError("To mark the complexity analysis as "
                                  "complete you need to rate all complexities "
                                  "and provide a rationale for your rating.")

    def clean_success_criteria(self):
        success_criterias = self.prescription.successcriteria_set.count()
        if self.success_criteria and success_criterias < 1:
            self.success_criteria = False
            self.save()
            raise ValidationError("To mark the success criterias as complete "
                                  "you need to specify at least one success "
                                  "criteria.")

    def clean_risk_register(self):
        if self.risk_register and self.prescription.register_set.count() < 1:
            self.risk_register = False
            self.save()
            raise ValidationError("To mark the risk register as complete "
                                  "you need to have at least one register "
                                  "item.")

    def clean_context_statement(self):
        contexts = Context.objects.filter(prescription=self.prescription)
        context = all(bool(c.statement) for c in contexts)
        actions = ContextRelevantAction.objects.filter(
            action__risk__prescription=self.prescription)
        complete = all(a.considered for a in actions)
        if self.context_statement and not (context and complete):
            self.context_statement = False
            self.save()
            raise ValidationError("To mark risk management context statement "
                                  "as complete, there must be at least one "
                                  "context statement and all relevant actions "
                                  "need to be considered.")


class BurnImplementationState(AbstractState):
    """
    Stores state related to Part B (Implementation plan) of an electronic
    Prescribed Fire Plan. These flags are to indicate if each section has
    been fully completed.
    """
    prescription = models.OneToOneField(
        Prescription, related_name='day_state', on_delete=models.PROTECT)
    overview = models.BooleanField(choices=BOOL_CHOICES, default=False)
    # pre_actions = models.NullBooleanField(choices=NULL_CHOICES, default=False)
    # actions = models.NullBooleanField(choices=NULL_CHOICES, default=False)
    # roads = models.NullBooleanField(choices=NULL_CHOICES, default=False)
    # traffic = models.NullBooleanField(choices=NULL_CHOICES, default=False)
    # tracks = models.NullBooleanField(choices=NULL_CHOICES, default=False)
    pre_actions = models.BooleanField(choices=NULL_CHOICES, default=False, null=True)
    actions = models.BooleanField(choices=NULL_CHOICES, default=False, null=True)
    roads = models.BooleanField(choices=NULL_CHOICES, default=False, null=True)
    traffic = models.BooleanField(choices=NULL_CHOICES, default=False, null=True)
    tracks = models.BooleanField(choices=NULL_CHOICES, default=False, null=True)
    burning_prescription = models.BooleanField(
        choices=BOOL_CHOICES, default=False)
    # fuel_assessment = models.NullBooleanField(
    #     choices=NULL_CHOICES, default=False)
    # edging_plan = models.NullBooleanField(choices=NULL_CHOICES, default=False)
    fuel_assessment = models.BooleanField(
        choices=NULL_CHOICES, default=False, null=True)
    edging_plan = models.BooleanField(choices=NULL_CHOICES, default=False, null=True)
    contingency_plan = models.BooleanField(choices=BOOL_CHOICES, default=False)
    lighting_sequence = models.BooleanField(
        choices=BOOL_CHOICES, default=False)
    # exclusion_areas = models.NullBooleanField(
    #     choices=NULL_CHOICES, default=False)
    exclusion_areas = models.BooleanField(
        choices=NULL_CHOICES, default=False, null=True)
    organisational_structure = models.BooleanField(
        choices=BOOL_CHOICES, default=False)
    briefing = models.BooleanField(choices=BOOL_CHOICES, default=False)
    operation_maps = models.BooleanField(choices=BOOL_CHOICES, default=False)
    # aerial_maps = models.NullBooleanField(choices=NULL_CHOICES, default=False)
    aerial_maps = models.BooleanField(choices=NULL_CHOICES, default=False, null=True)

    def clean_overview(self):
        overviews = self.prescription.operationaloverview_set.all()
        if self.overview and not all([x.overview for x in overviews]):
            self.overview = False
            self.save()
            raise ValidationError("Operational overview cannot be marked as "
                                  "complete unless the overview has been "
                                  "filled out and completed.")

    def clean_pre_actions(self):
        """
        There must be at least one pre burn action to complete this.
        The action details must also be complete.
        If there are no pre burn actions, user should select N/A.
        Should not allow user to mark N/A if pre burn action exists.
        """
        pre_burn_actions = Action.objects.filter(
            risk__prescription=self.prescription,
            relevant=True, pre_burn=True)
        incomplete_pre_burn_actions = 0

        for action in pre_burn_actions:
            if not action.details:
                incomplete_pre_burn_actions += 1

        if (self.pre_actions and pre_burn_actions.count() == 0):
            self.pre_actions = False
            self.save()
            raise ValidationError("Pre-burn actions cannot be marked as "
                                  "complete unless there is at least one "
                                  "pre-burn action associated with the burn.")
        if ((self.pre_actions and pre_burn_actions.count() > 0 and
             incomplete_pre_burn_actions > 0)):
            self.pre_actions = False
            self.save()
            raise ValidationError("Pre-burn actions cannot be marked as "
                                  "complete unless all pre-burn actions have "
                                  "details.")
        if (self.pre_actions is None and pre_burn_actions.count() > 0):
            self.pre_actions = False
            self.save()
            raise ValidationError("Pre-burn actions cannot be marked as Not "
                                  "Applicable if there are pre-burn actions "
                                  "associated with the burn.")

    def clean_actions(self):
        """
        There must be at least one day of burn action to complete this.
        The action details must also be complete.
        If there are no day of burn actions, user should select N/A.
        Should not allow user to mark N/A if day of burn action exists.
        """
        dob_actions = Action.objects.filter(
            risk__prescription=self.prescription,
            relevant=True, day_of_burn=True)
        incomplete_dob_actions = 0
        for action in dob_actions:
            if (not action.details or
                (action.day_of_burn_include and
                 not any([action.day_of_burn_situation,
                          action.day_of_burn_mission,
                          action.day_of_burn_execution,
                          action.day_of_burn_administration,
                          action.day_of_burn_command,
                          action.day_of_burn_safety]))):
                incomplete_dob_actions += 1
        if (self.actions and dob_actions.count() == 0):
            self.actions = False
            self.save()
            raise ValidationError("Day of burn actions cannot be marked as "
                                  "complete unless there is at least one day "
                                  "of burn action associated with the burn.")
        if ((self.actions and dob_actions.count() > 0 and
             incomplete_dob_actions > 0)):
            self.actions = False
            self.save()
            raise ValidationError("Day of burn actions cannot be marked as "
                                  "complete unless all day of burn actions "
                                  "have details and all day of burn actions " +
                                  "that are to be included in briefing have " +
                                  "SMEAC locations(s) selected.")
        if (self.actions is None and dob_actions.count() > 0):
            self.actions = False
            self.save()
            raise ValidationError("Day of burn actions cannot be marked as "
                                  "Not Applicable if there are day of burn "
                                  "actions associated with the burn.")

    def clean_lighting_sequence(self):
        """
        There must be at least one lighting sequence
        """
        lightingsequences = self.prescription.lightingsequence_set.count()
        if self.lighting_sequence and lightingsequences < 1:
            self.lighting_sequence = False
            self.save()
            raise ValidationError("Lighting sequence cannot be "
                                  "marked as complete unless there is at "
                                  "least one lighting sequence.")

    def clean_contingency_plan(self):
        """
        BR-33: There must be at least one contingency plan.
        """
        contingencies = self.prescription.contingency_set.count()
        if self.contingency_plan and contingencies < 1:
            self.contingency_plan = False
            self.save()
            raise ValidationError("Contingency plan cannot be "
                                  "marked as complete unless there is at "
                                  "least one contingency plan.")

    def clean_exclusion_areas(self):
        """
        There must be at least one exclusion area to complete this.
        If there are no exclusion areas, user should select N/A.
        Should not allow user to mark N/A if exclusion area exists.
        """
        count = self.prescription.exclusionarea_set.all().count()
        if self.exclusion_areas and count < 1:
            self.exclusion_areas = False
            self.save()
            raise ValidationError("Exclusion areas cannot be marked as "
                                  "complete unless there is at least one "
                                  "exclusion area associated with the burn.")
        if self.exclusion_areas is None and count > 0:
            self.exclusion_areas = False
            self.save()
            raise ValidationError("Exclusion areas cannot be marked as Not "
                                  "Applicable if there are exclusion areas "
                                  "associated with the burn.")

    def clean_edging_plan(self):
        """
        BR-32: If there is an edging plan there must be at least one edge in
        the plan.
        """
        if self.edging_plan and self.prescription.edgingplan_set.count() < 1:
            self.edging_plan = False
            self.save()
            raise ValidationError("Edging plan cannot be marked as complete "
                                  "unless there is at least one edge in the "
                                  "plan.")

    def clean_briefing(self):
        """
        Briefing checklist cannot be marked as "Complete"
        unless either a briefing checklist document is uploaded
        or at least one item in the checklist has been entered into"
        """
        count = self.prescription.document_set.tag_names(
            "Briefing Checklist").count()
        bc_count = self.prescription.briefingchecklist_set.exclude(
            notes__isnull=True).exclude(notes__exact='').count()
        if (self.briefing and (count < 1 and bc_count < 1)):
            self.briefing = False
            self.save()
            raise ValidationError("Briefing checklist cannot be marked as "
                                  "complete unless either at least one item "
                                  "in the checklist has been entered or "
                                  "a briefing checklist document has been "
                                  "uploaded.")

    def clean_organisational_structure(self):
        """
        Organisational structure cannot be marked as "Complete"
        unless an organisational structure document is uploaded
        """
        count = self.prescription.document_set.tag_names(
            "Prescribed Burning Organisational Structure "
            "and Communications Plan").count()
        if self.organisational_structure and count < 1:
            self.organisational_structure = False
            self.save()
            raise ValidationError("Organisational structure and "
                                  "communications plan cannot be marked as "
                                  "complete unless an organisational "
                                  "structure and communications plan document "
                                  "has been uploaded.")

    def clean_aerial_maps(self):
        """
        BR-25: For the Part B Stage of Completion Table, the Aerial map can
        not be marked as "Complete" unless an aerial map is uploaded or it has
        been marked as "Not Applicable".
        """
        if self.aerial_maps and not self.prescription.aircraft_burn:
            self.aerial_maps = False
            self.save()
            raise ValidationError("Aerial burning map cannot be marked "
                                  "as complete unless the burn has been "
                                  "marked as an aircraft burn and an "
                                  "aerial burning map has been uploaded.")

        documents = self.prescription.document_set
        count = documents.tag_names("Aerial Burn Map").count()
        if ((self.aerial_maps and self.prescription.aircraft_burn and
             count < 1)):
            self.aerial_maps = False
            self.save()
            raise ValidationError("Aerial burning map cannot be marked as "
                                  "complete unless an aerial map has been "
                                  "uploaded.")

        if self.prescription.aircraft_burn and self.aerial_maps is None:
            self.aerial_maps = False
            self.save()
            raise ValidationError("Aerial burning map cannot marked as not "
                                  "applicable when the burn has been marked "
                                  "as an aircraft burn.")

    def clean_operation_maps(self):
        """
        BR-24: For the Part B Stage of Completion Table, the Operations map
        can not be marked as "Complete" unless an operations map is uploaded.
        The Operations Map can not be marked as "Not applicable".
        """
        documents = self.prescription.document_set
        count = documents.tag_names("Operations Map").count()
        if self.operation_maps and count < 1:
            self.operation_maps = False
            self.save()
            raise ValidationError("Operations map cannot be marked as "
                                  "complete unless an operations map has been "
                                  "uploaded.")

    def clean_burning_prescription(self):
        """
        BR-29: In the Contents section Part B - Burning Prescription can not
        be marked as complete unless there has been a document uploaded
        against it in Part D.
        There needs to be at least one burning prescription.
        """
        count = self.prescription.burningprescription_set.all().count()

        if self.burning_prescription and count < 1:
            self.burning_prescription = False
            self.save()
            raise ValidationError("Burning prescription cannot be marked as "
                                  "complete unless at least one burning "
                                  "prescription has been added to the burn.")

    def clean_fuel_assessment(self):
        count = self.prescription.document_set.tag_names(
                    "Fuel Assessment Summary_FIRE 872").count()

        if self.fuel_assessment and count < 1:
            self.fuel_assessment = False
            self.save()
            raise ValidationError("Fuel Assessment cannot be marked as "
                                  "complete unless a fuel assessment "
                                 "summary has been uploaded against it.")

        if self.fuel_assessment is None and count > 0:
            self.fuel_assessment = False
            self.save()
            raise ValidationError("Fuel Assessment cannot be marked as not applicable "
                                  "if there are Fuel Assessments associated with the "
                                  "burn.")

    def clean_roads(self):
        road_count = RoadSegment.objects.filter(
            way_ptr__prescription=self.prescription).count()
        incomplete_roads_count = RoadSegment.objects.filter(
            Q(road_type='') | Q(road_type=None) | Q(name='') | Q(name=None),
            way_ptr__prescription=self.prescription).count()

        if self.roads and road_count < 1:
            self.roads = False
            self.save()
            raise ValidationError("Roads cannot be marked as complete unless "
                                  "at least one road is associated with the "
                                  "burn.")

        if self.roads and road_count > 0 and incomplete_roads_count > 0:
            self.roads = False
            self.save()
            raise ValidationError("Roads cannot be marked as complete unless "
                                  "all roads associated with the burn have at "
                                  "least a road name and type.")

        if self.roads is None and road_count > 0:
            self.roads = False
            self.save()
            raise ValidationError("Roads cannot be marked as not applicable "
                                  "if there are roads associated with the "
                                  "burn.")

    def clean_traffic(self):
        """
        BR-23: For the Part B Stage of Completion Table, the Traffic Control
        Diagrams can not be marked as "Complete" unless a traffic control
        diagram is selected from the library or a custom map is uploaded or it
        has been marked as "Not Applicable".
        """
        documents = self.prescription.document_set
        traffic_diagrams = self.prescription.way_set.filter(
            roadsegment__traffic_diagram__isnull=False).count()
        count = (documents.filter(tag__name="Traffic Diagrams").count() +
                 traffic_diagrams)
        road_count = RoadSegment.objects.filter(
            way_ptr__prescription=self.prescription).count()

        if self.traffic and count < 1:
            self.traffic = False
            self.save()
            raise ValidationError("Traffic control diagrams cannot be "
                                  "marked as complete unless "
                                  "a traffic control diagram has been "
                                  "selected or a custom one uploaded.")

        if self.traffic and road_count < 1:
            self.traffic = False
            self.save()
            raise ValidationError("Traffic control diagrams cannot be "
                                  "marked as complete unless "
                                  "there is at least one road uploaded "
                                  "to the burn.")

        if self.traffic is None and count > 0:
            self.traffic = False
            self.save()
            raise ValidationError("Traffic control diagrams cannot be "
                                  "marked as not applicable "
                                  "if there are traffic control diagrams "
                                  "associated with the burn.")

    def clean_tracks(self):
        """
        BR-26: For the Part B Stage of Completion Table, the Tracks and Trails
        Maps can not be marked as "Complete" unless a diversion map
        uploaded or it has been marked as "Not Applicable". This only applies
        if there is a tracks/trails record stating that a diversion map
        exists.
        """
        documents = self.prescription.document_set
        ways = self.prescription.way_set
        doc_count = documents.filter(
            tag__name="Track Trail Diversion Map").count()
        count_trails_with_divmap = ways.filter(
            trailsegment__diversion=True).count()
        track_count = TrailSegment.objects.filter(
            way_ptr__prescription=self.prescription).count()

        if self.tracks and track_count < 1:
            self.tracks = False
            self.save()
            raise ValidationError("Tracks and trails cannot be "
                                  "marked as complete if there are no "
                                  "tracks and trails records associated with "
                                  "the burn.")

        if self.tracks and doc_count < 1 and count_trails_with_divmap > 0:
            self.tracks = False
            self.save()
            raise ValidationError("A user has indiciated that a diversion map "
                                  "is required for this burn. Tracks and "
                                  "trails cannot be marked as "
                                  "complete unless a diversion map has been "
                                  "uploaded.")

        if self.tracks and doc_count > 0 and count_trails_with_divmap < 1:
            self.tracks = False
            self.save()
            raise ValidationError("A diversion map has been uploaded "
                                  "but no tracks or trails requiring a "
                                  "diversion map have been "
                                  "associated with the burn. Tracks and "
                                  "trails cannot be marked as "
                                  "complete unless at least one track or "
                                  "trail requiring a diversion map is "
                                  "associated with the burn.")

        if self.tracks is None and track_count > 0:
            self.tracks = False
            self.save()
            raise ValidationError("Tracks and trails cannot be "
                                  "marked as not applicable as there are "
                                  "tracks and trails records associated with "
                                  "the burn.")

        if self.tracks is None and doc_count > 0:
            self.tracks = False
            self.save()
            raise ValidationError("Tracks and trails cannot be "
                                  "marked as not applicable as there are "
                                  "diversion maps uploaded to "
                                  "the burn.")


class PostBurnChecklist(Audit):
    prescription = models.ForeignKey(Prescription, blank=True, null=True, on_delete=models.PROTECT)
    action = models.CharField(max_length=320)
    relevant = models.BooleanField(default=False)
    completed_on = models.DateField(
        default=timezone.now, blank=True, null=True)
    completed_by = models.TextField(verbose_name="Action completed by (name)",
                                    blank=True, null=True)

    _required_fields = ('completed_on', 'completed_by')

    def __str__(self):
        return self.action

    def clean_completed_on(self):
        if self.completed_on is not None:
            # The following line was causing validation failure before 0800.
            # Jira ref: PBS-1454
            #if self.completed_on > timezone.now().date():
            if self.completed_on > datetime.now().date():
                raise ValidationError("This action could not be completed "
                                      "in the future.")
            if (self.prescription.approval_status_modified is None or
                    self.completed_on <
                    self.prescription.approval_status_modified.date()):
                raise ValidationError("This action could not be completed "
                                      "before its prescription was approved.")

    def clean(self, *args, **kwargs):
        super(PostBurnChecklist, self).clean(*args, **kwargs)

        if self.completed_on is not None and not self.completed_by:
            raise ValidationError("Please specify who completed this action.")

        if self.completed_by and self.completed_on is None:
            raise ValidationError("Please specify when was this action "
                                  "completed.")

    class Meta:
        ordering = ["pk"]
        verbose_name = "post burn checklist item"
        verbose_name_plural = "post burn checklist"


class BurnClosureState(AbstractState):
    """
    Stores state related to Part C (Burn Closure and Evaluation) of an
    electronic Prescribed Fire Plan. These flags are to indicate if each
    section has been fully completed.
    """
    prescription = models.OneToOneField(
        Prescription, related_name='post_state', on_delete=models.PROTECT)
    # post_actions = models.NullBooleanField(choices=NULL_CHOICES, default=False)
    post_actions = models.BooleanField(choices=NULL_CHOICES, default=False, null=True)
    evaluation_summary = models.BooleanField(
        choices=BOOL_CHOICES, default=False)
    # evaluation = models.NullBooleanField(choices=NULL_CHOICES, default=False)
    evaluation = models.BooleanField(choices=NULL_CHOICES, default=False, null=True)
    # post_ignitions = models.NullBooleanField(
    #     choices=NULL_CHOICES, default=False)
    # aerial_intensity = models.NullBooleanField(
    #     choices=NULL_CHOICES, default=False)
    # satellite_intensity = models.NullBooleanField(
    #     choices=NULL_CHOICES, default=False)
    # other = models.NullBooleanField(choices=NULL_CHOICES, default=False)
    post_ignitions = models.BooleanField(
        choices=NULL_CHOICES, default=False, null=True)
    aerial_intensity = models.BooleanField(
        choices=NULL_CHOICES, default=False, null=True)
    satellite_intensity = models.BooleanField(
        choices=NULL_CHOICES, default=False, null=True)
    other = models.BooleanField(choices=NULL_CHOICES, default=False, null=True)
    post_burn_checklist = models.BooleanField(
        choices=BOOL_CHOICES, default=False)
    closure_declaration = models.BooleanField(
        choices=BOOL_CHOICES, default=False)
    # signage = models.NullBooleanField(choices=NULL_CHOICES, default=False)
    signage = models.BooleanField(choices=NULL_CHOICES, default=False, null=True)

    def clean_evaluation(self):
        evaluations = self.prescription.proposedaction_set.all().count()
        incomplete_evaluations = self.prescription.proposedaction_set.filter(
            Q(observations='') | Q(observations=None) | Q(action='') |
            Q(action=None)).count()
        if self.evaluation and evaluations > 0 and incomplete_evaluations > 0:
            self.evaluation = False
            self.save()
            raise ValidationError("To mark burn evaluation - lessons learned "
                                  "as complete you must fill in the details "
                                  "of all lessons learned.")
        if self.evaluation and evaluations < 1:
            self.evaluation = False
            self.save()
            raise ValidationError("To mark burn evaluation - lessons learned "
                                  "as complete you must detail at least one "
                                  "lesson learned.")

    def clean_evaluation_summary(self):
        incomplete_evaluation_summary = Evaluation.objects.filter(
            Q(achieved=None) | Q(summary='') | Q(summary=None),
            criteria__prescription=self.prescription).count()
        if self.evaluation_summary and incomplete_evaluation_summary > 0:
            self.evaluation_summary = False
            self.save()
            raise ValidationError("To mark burn evaluation summary as "
                                  "complete, you must state the level of "
                                  "achievement and the evaluation rationale "
                                  "for each success criteria.")

    def clean_post_actions(self):
        post_burn_actions = Action.objects.filter(
            risk__prescription=self.prescription, post_burn=True).count()
        incomplete = Action.objects.filter(
            Q(post_burn_completed=None) | Q(post_burn_completer='') |
            Q(post_burn_completer=None), risk__prescription=self.prescription,
            post_burn=True).count()
        if self.post_actions and post_burn_actions > 0 and incomplete > 0:
            self.post_actions = False
            self.save()
            raise ValidationError("To mark post-burn actions as complete, you "
                                  "must enter a date actioned and actioned by "
                                  "whom for all post-burn actions.")

        if self.post_actions is None and post_burn_actions > 0:
            self.post_actions = False
            self.save()
            raise ValidationError("You cannot mark post-burn actions as "
                                  "not applicable if there are any post-burn "
                                  "actions.")

    def clean_post_burn_checklist(self):
        checklists = PostBurnChecklist.objects.filter(
            prescription=self.prescription, relevant=True)
        complete = all(c.completed_on and c.completed_by
                       for c in checklists)
        if self.post_burn_checklist and not complete:
            self.post_burn_checklist = False
            self.save()
            raise ValidationError("To mark the post burn checklist as "
                                  "complete, you need to complete all "
                                  "relevant checklist items.")

    def clean_signage(self):
        documents = self.prescription.document_set
        doc_count = 0
        doc_count += self.prescription.way_set.filter(
            roadsegment__traffic_diagram__isnull=False).count()
        doc_count += documents.filter(tag__name="Traffic Diagrams").count()
        doc_count += documents.filter(tag__name="Diversion Map").count()
        sign_doc_count = documents.filter(
            tag__name="Sign Inspection and Surveillance Form").count()
        if self.signage is None and (doc_count > 0 or sign_doc_count > 0):
            raise ValidationError("Sign Inspection and Surveillance cannot "
                                  "be marked as incomplete if there are any "
                                  "traffic control diagrams, diversion maps "
                                  "or sign inspection and surveillance forms "
                                  "uploaded to the burn.")
        if self.signage and doc_count > 0 and sign_doc_count < 1:
            raise ValidationError("To mark Sign Inspection and "
                                  "Surveillance as complete there must "
                                  "be at least one traffic control "
                                  "diagram or diversion map "
                                  "AND a completed copy "
                                  "of the Sign Inspection and Surveillance "
                                  "Form uploaded to the burn.")
        if self.signage and doc_count < 1:
            raise ValidationError("Sign Inspection and Surveillance cannot "
                                  "be marked as complete if there are no "
                                  "traffic control diagrams or diversion maps "
                                  "uploaded to the burn.")

    def clean_closure_declaration(self):
        if self.closure_declaration and not self.prescription.can_close:
            raise ValidationError("Closure declaration cannot be marked as "
                                  "complete before the ePFP is ready to be "
                                  "closed.")



class AreaAchievement(Audit):
    prescription = models.ForeignKey(Prescription, on_delete=models.PROTECT)
    #Jira issue PBS-1407
    ignition = models.DateField(
        verbose_name="Ignition Date",)
        # default=lambda: timezone.now().date())
    ignition_types = models.ManyToManyField(IgnitionType)
    area_treated = models.DecimalField(
        verbose_name="Area where treatment is complete (ha)",
        validators=[MinValueValidator(0)], default=0,
        decimal_places=1, max_digits=12)
    area_estimate = models.DecimalField(
        verbose_name="Area treated today (ha)",
        validators=[MinValueValidator(0)], default=0,
        decimal_places=1, max_digits=12)
    edging_length = models.DecimalField(
        verbose_name="Length of Successful Edging (kms)",
        validators=[MinValueValidator(0)], default=0,
        decimal_places=1, max_digits=12)
    edging_depth_estimate = models.DecimalField(
        verbose_name="Estimated Depth of Edging (m)",
        validators=[MinValueValidator(0)], default=0,
        decimal_places=1, max_digits=12)
    dpaw_fire_no = models.CharField(
        verbose_name="DPaW Fire Number", max_length=64, blank=True)
    dfes_fire_no = models.CharField(
        verbose_name="DFES Fire Number", max_length=64, blank=True)
    date_escaped = models.DateField(
        verbose_name="Date of Escape", null=True, blank=True)

    _required_fields = ('ignition', 'ignition_types',
                        'area_treated', 'area_estimate')

    class Meta:
        ordering = ['-ignition']
        get_latest_by = 'ignition'
        verbose_name = "Day of Burn Achievement"
        verbose_name_plural = "Day of Burn Achievements"

    def __str__(self):
        return "%s %d ha %d kms" % (self.ignition, self.area_estimate,
                                    self.edging_length)

    def clean_ignition(self):
        if self.ignition and self.ignition > timezone.now().date():
            raise ValidationError("Ignition date cannot be in the future.")

    def clean_date_escaped(self):
        if self.date_escaped:
            if self.date_escaped > timezone.now().date():
                raise ValidationError("Date of escape cannot be in the "
                                      "future.")
            if not self.dpaw_fire_no and not self.dfes_fire_no:
                raise ValidationError("If there is a date of escape, there "
                                      "must also be a DPaW or DFES fire no.")

    def save(self, **kwargs):
        super(AreaAchievement, self).save(**kwargs)
        self.prescription.save()

    def delete(self, **kwargs):
        super(AreaAchievement, self).delete(**kwargs)
        obj = self.prescription
        if obj.areaachievement_set.all().count() == 0:
            obj.ignition_completed_date = None
            obj.save()


class Evaluation(Audit):
    ACHIEVED_NO = 1
    ACHIEVED_YES = 2
    ACHIEVED_PARTIAL = 3
    ACHIEVED_CHOICES = (
        (ACHIEVED_NO, "No"),
        (ACHIEVED_YES, "Yes"),
        (ACHIEVED_PARTIAL, "Partially"),
    )
    criteria = models.OneToOneField(
        SuccessCriteria, verbose_name="Success Criteria", on_delete=models.PROTECT)
    achieved = models.PositiveSmallIntegerField(
        choices=ACHIEVED_CHOICES, blank=True, null=True,
        verbose_name="Success Criteria Achieved?")
    summary = models.TextField(verbose_name="Evaluation Rationale", blank=True)

    _required_fields = ('achieved', 'summary')

    @property
    def prescription(self):
        return self.criteria.prescription

    def clean_achieved(self):
        if self.summary != '' and not self.achieved:
            raise ValidationError("You need to indicate whether or not "
                                  "this success criteria has been met.")

    def clean_summary(self):
        if self.achieved is not None and not self.summary:
            raise ValidationError("You need to provide a rationale for this "
                                  "achievement.")


class ProposedAction(Audit):
    prescription = models.ForeignKey(Prescription, on_delete=models.PROTECT)
    observations = models.TextField(
        blank=True, verbose_name='Observations Identified')
    action = models.TextField(
        blank=True, verbose_name='Proposed Action')

    _required_fields = ('observations', 'action')

    def __str__(self):
        return self.action

    class Meta:
        verbose_name = 'Lesson Learned'
        verbose_name_plural = "Lessons Learned"


class ClosureDeclaration(Audit):
    prescription = models.OneToOneField(Prescription, on_delete=models.PROTECT)
    closed = models.BooleanField(default=False)


@receiver(post_save, sender=Prescription)
def create_state(sender, instance, created, **kwargs):
    """
    For each new prescription, create new state objects to track their
    completion.
    """
    if created:
        for state in [SummaryCompletionState, BurnImplementationState,
                      BurnClosureState]:
            state.objects.create(prescription=instance)

        for item in PostBurnChecklist.objects.filter(prescription=None):
            item.pk = None
            item.prescription = instance
            item.save()


@receiver(post_save, sender=SuccessCriteria)
def create_evaluation(sender, instance, created, **kwargs):
    """
    When a new success criteria is created, create an instance of an
    evaluation for that criteria.
    """
    if created:
        Evaluation.objects.create(criteria=instance)

import reversion
reversion.register(PostBurnChecklist)
reversion.register(BurnClosureState)
reversion.register(AreaAchievement)
reversion.register(ProposedAction)
reversion.register(BurnImplementationState)