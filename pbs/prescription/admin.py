from __future__ import unicode_literals, absolute_import

import logging
import os
import subprocess
import json
import time
import unicodecsv
import humanize

from functools import update_wrapper, partial
from dateutil import tz
from datetime import datetime

from swingers.admin import DetailAdmin

from guardian.shortcuts import assign_perm

from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.utils import quote, unquote, flatten_fieldsets
from django.contrib.auth.models import Group
from django.core.exceptions import (FieldError, ValidationError,
                                    PermissionDenied)
from django.urls import reverse
from django.db import transaction, router
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.forms.models import modelform_factory
from django.template import RequestContext
from django.template.defaultfilters import date
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.decorators.csrf import csrf_protect

from pbs.admin import BaseAdmin, get_permission_codename
from pbs.prescription.actions import (
    delete_selected, delete_approval_endorsement, carry_over_burns, bulk_corporate_approve)
from pbs.prescription.forms import (
    PrescriptionCreateForm, EndorsingRoleForm,
    AddEndorsementForm, AddApprovalForm, PrescriptionEditForm,
    PrescriptionPriorityForm, BriefingChecklistForm,
    FundingAllocationInlineFormSet)
from pbs.prescription.models import (
    Season, Prescription, RegionalObjective, Region, FundingAllocation, EndorsingRole)
from django.forms.models import inlineformset_factory

from pbs.report.models import Evaluation
from pbs.report.forms import (
    SummaryCompletionStateForm, BurnImplementationStateForm, BurnClosureStateForm)

from pbs.templatetags.pbs_markdown import markdownify
from pbs.utils import get_deleted_objects, update_permissions, support_email,download_pdf
from pbs.utils.widgets import CheckboxSelectMultiple

from pbs import mutex, SemaphoreException
from pbs.filters import BooleanFieldListFilter,CrossTenureApprovedListFilter,IntChoicesFieldListFilter,RelatedFieldListFilter,StringValuesFieldListFilter
from django.core.mail import send_mail

from pbs.prescription import fund_allocation


csrf_protect_m = method_decorator(csrf_protect)
logger = logging.getLogger('pbs')


class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'code')


class PrescriptionAdmin(DetailAdmin, BaseAdmin):
    """
    An admin class to manage prescriptions.
    Caution: self.fieldsets and self.form are both declared as the fieldsets
    and form for the *add* form. The functions `get_form` and `get_fieldsets`
    have been overridden to return a different form and fieldsets based on the
    selected prescription's status.
    """
    objectives_template = 'admin/prescription/prescription/add_objectives.html'
    summary_template = 'admin/prescription/prescription/summary.html'
    pre_summary_template = 'admin/prescription/prescription/pre_summary.html'
    day_summary_template = 'admin/prescription/prescription/day_summary.html'
    post_summary_template = 'admin/prescription/prescription/post_summary.html'
    corporate_approval_template = 'admin/prescription/prescription/cbas.html'
    pdf_summary_template = 'admin/prescription/prescription/pdf_summary.html'

    remove_selected_confirmation_template = (
        'admin/prescription/prescription/remove_selected_confirmation.html')

    changelist_link_detail = True
    list_filter = (("region",RelatedFieldListFilter), ("district",RelatedFieldListFilter), ("financial_year",StringValuesFieldListFilter),
                   ("contentious",BooleanFieldListFilter), ("aircraft_burn",BooleanFieldListFilter),
                   ("priority",IntChoicesFieldListFilter), ("planning_status",IntChoicesFieldListFilter), ("endorsement_status",IntChoicesFieldListFilter),
                   ("approval_status",IntChoicesFieldListFilter), ("ignition_status",IntChoicesFieldListFilter), ("status",IntChoicesFieldListFilter),
                   ("contingencies_migrated",BooleanFieldListFilter),("non_calm_tenure",BooleanFieldListFilter),("non_calm_tenure_approved",CrossTenureApprovedListFilter))
    list_display = ("burn_id", "name", "region", "district",
                    "financial_year", "contentious", "aircraft_burn",
                    "priority", "remote_sensing_priority",
                    "planning_status", "endorsement_status", "approval_status",
                    "approval_expiry", "ignition_status", "status",
                    "prescribing_officer_name", "date_modified_local", "contingencies_migrated","_non_calm_tenure","_non_calm_tenure_approved")

    actions = [delete_selected, 'export_to_csv', 'burn_summary_to_csv',
               delete_approval_endorsement, carry_over_burns, bulk_corporate_approve]

    form = PrescriptionCreateForm
    edit_form = PrescriptionEditForm

    fieldsets = (
        (None, {
            "fields": (
                'name',
                'description',
                'financial_year',
                ('last_season', 'last_year'),
                ('last_year_unknown', 'last_season_unknown'),
                ('region', 'district'), 'location', 'forest_blocks',
                ('contentious', 'contentious_rationale'),
                ('aircraft_burn', 'remote_sensing_priority'),
                ('priority', 'rationale'),
                'purposes', 'treatment_percentage',
                'area', 'perimeter'
            )
        }),
    )
    search_fields = ('name', 'burn_id', 'location')
    filter_fields = (
        ('district', {'filter_on': 'region'}),
        ('shire', {'filter_on': 'district'}),
    )
    filter_horizontal = ('tenures', 'fuel_types', 'shires',
                         'forecast_areas', 'endorsing_roles')

    def _non_calm_tenure(self,obj):
        if obj.non_calm_tenure:
            return "Yes"
        elif obj.non_calm_tenure is None:
            return "------"
        else:
            return "No"
    _non_calm_tenure.admin_order_field = 'non_calm_tenure'
    _non_calm_tenure.short_description = 'Non CALM-Act Tenure'

    def _non_calm_tenure_approved(self,obj):
        if obj.non_calm_tenure:
            if obj.non_calm_tenure_approved:
                return "<i class='icon-ok text-success'></i>"
            elif obj.non_calm_tenure_approved == False:
                return "<i class='icon-minus text-warning'></i>"
            else:
                return ""
        else:
            return ""
    _non_calm_tenure_approved.admin_order_field = 'non_calm_tenure_approved'
    _non_calm_tenure_approved.short_description = 'Cross Tenure Approved?'



    def queryset(self, request):
        """
        Prefetch the approvals, so that we don't do a query per-prescription
        on the regional summary page.
        """
        qs = super(PrescriptionAdmin, self).queryset(request)
        qs.prefetch_related('approval_set')

        return qs

    def prescribing_officer_name(self, obj):
        if obj.prescribing_officer is not None:
            return obj.prescribing_officer.get_full_name()
        else:
            return "No prescribing officer"
    prescribing_officer_name.admin_order_field = 'prescribing_officer'
    prescribing_officer_name.short_description = 'Prescribing Officer'

    def date_modified_local(self, obj):
        return obj.date_modified_local()
    date_modified_local.admin_order_field = 'modified'
    date_modified_local.short_description = 'Date Modified'

    def approval_expiry(self, obj):
        if obj.is_approved:
            return date(obj.current_approval.valid_to)
        else:
            return "Not applicable"
    approval_expiry.short_description = "Approved Until"

    def get_urls(self):
        """
        Add some extra views for handling the prescription summaries and a page
        to handle selecting Regional Fire Coordinator objectives for a burn.
        """
        # from django.conf.urls import url
        from django.urls import re_path

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            # '',
           re_path(r'^(\d+)/add/objectives/$',
                wrap(self.add_objectives),
                name='%s_%s_objectives' % info),
           re_path(r'^(\d+)/regional_objective/(\d+)/delete$',
                wrap(self.delete_regional_objective),
                name='%s_%s_delete_regional_objective' % info),
           re_path(r'^(\d+)/summary/$',
                wrap(self.summary),
                name='%s_%s_summary' % info),
           re_path(r'^(\d+)/summary/pre/$',
                wrap(self.pre_summary),
                name='%s_%s_pre_summary' % info),
           re_path(r'^(\d+)/summary/day/$',
                wrap(self.day_summary),
                name='%s_%s_day_summary' % info),
           re_path(r'^(\d+)/summary/post/$',
                wrap(self.post_summary),
                name='%s_%s_post_summary' % info),
           re_path(r'^(\d+)/summary/pdf/$',
                wrap(self.pdf_summary),
                name='%s_%s_pdf_summary' % info),
           re_path(r'^(\d+)/download/$',
                wrap(self.pdflatex),
                name='%s_%s_download' % info),
           re_path(r'^(\d+)/export/$',
                wrap(self.pdflatex),
                name='%s_%s_export' % info),
           re_path(r'^(\d+)/cbas/$',
                wrap(self.corporate_approve),
                name='%s_%s_corporate_approve' % info),
           re_path(r'^(\d+)/endorsement/$',
                wrap(self.endorse),
                name='%s_%s_endorse' % info),
           re_path(r'^(\d+)/endorsement/(\d+)/delete$',
                wrap(self.delete_endorsement),
                name='%s_%s_delete_endorsement' % info),
           re_path(r'^(\d+)/endorsement/officers$',
                wrap(self.endorsing_roles),
                name='%s_%s_endorsing_roles' % info),
           re_path(r'^(\d+)/approval/$',
                wrap(self.approve),
                name='%s_%s_approve' % info),
           re_path(r'^(\d+)/closure/$',
                wrap(self.close),
                name='%s_%s_close' % info),
           re_path(r'^(\d+)/sitemap/$',
                wrap(self.sitemap),
                name='%s_%s_sitemap' % info),
        ]

        return urlpatterns + super(PrescriptionAdmin, self).get_urls()
        #return urlpatterns + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        # figure out how to auto-select current user's region from
        # request.user.profile
        context = {
            'regions': Region.objects.all(),
            'seasons': Season.SEASON_CHOICES
        }
        #set the baseurl if it is not configured, 
        #this is the home page and also is the most used url, so this is the best place to set the baseurl
        if not settings.BASE_URL:
            settings.BASE_URL = request.build_absolute_uri("/")[:-1]

        context.update(extra_context or {})
        response = super(PrescriptionAdmin, self).changelist_view(
            request, extra_context=context)
        return response

    def get_actions(self, request):
        actions = super(PrescriptionAdmin, self).get_actions(request)

        if not request.user.has_perm('prescription.delete_prescription') and actions["delete_selected"]:
            del actions['delete_selected']
        if not request.user.has_perm('prescription.can_delete_approval') and actions["delete_approval_endorsement"]:
            del actions['delete_approval_endorsement']
        if not request.user.has_perm('prescription.can_carry_over') and actions["carry_over_burns"]:
            del actions['carry_over_burns']
        if not request.user.has_perm('prescription.can_corporate_approve') and actions["bulk_corporate_approve"]:
            del actions['bulk_corporate_approve']

        return actions

    def burn_summary_to_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = "attachment; filename=burn_summary.csv"

        writer = unicodecsv.writer(response, quoting=unicodecsv.QUOTE_ALL)
        writer.writerow([
            'Burn ID', 'Name of Burn', 'Area (ha)', 'Area to be treated (%)',
            'Priority', 'If Priority 1, explanatory comment*'])

        for item in queryset.order_by('priority', 'burn_id'):
            writer.writerow([
                item.burn_id, item.name, "%0.1f" % item.area, item.treatment_percentage,
                item.get_priority_display(), item.rationale if item.priority == 1 else ""
            ])

        return response
    burn_summary_to_csv.short_description = ugettext_lazy("Export Burn Summary to CSV")

    def export_to_csv(self, request, queryset):
        # TODO: fix up the date/time formatting to use the default template
        # filters.
        local_zone = tz.tzlocal()
        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = "attachment; filename=export.csv"

        writer = unicodecsv.writer(response, quoting=unicodecsv.QUOTE_ALL)
        writer.writerow([
            'Region', 'District', 'Name of Burn', 'Burn ID', 'Date Updated',
            'Planning Status', 'Endorsement Status', 'Approval Status',
            'Ignition Status', 'Burn Closed', 'Burn Complexity',
            'Burn Priority', 'Burn Risk', 'Contentious',
            'Contentious Rationale', 'Location of Burn',
            'Prescribing Officer', 'Year',
            'Proposed Ignition Type', 'Actual Ignition Type',
            'Fire Weather Forecast Area/s', 'Treatment %', 'Planned Burn Area',
            'Planned Burn Perimeter', 'Total Area Where Treatment Is Complete',
            'Total Treatment Activity', 'Newest treatment date',
            'Length of Edging/Perimeter',
            'Depth of Edging', 'Shire', 'Bushfire Act Zone',
            'Prohibited Period', 'Burn Purpose/s', 'Burn Objective/s',
            'Ignition Date', 'Program Allocations', 'Fuel Types',
            'Fuel Description', 'Land Tenure', 'Year Last Burnt', 'Season Last Burnt',
            'Date(s) Escaped', 'DPaW Fire Number', 'DFES Fire Number',
            'Shortcode', 'Remote Sensing Priority', 'Aircraft Burn',
            'Success Criteria', 'Success Criteria Achieved',
            'Observations Identified', 'Proposed Action',
            'Endorsement Name/s', 'Endorsement Date',
            'Approval Name/s', 'Approval Date', 'Approved Until','Overall Rationale',
            'Non-CALM Act Tenure?','Non-CALM Act Tenure Included','Public Value in Burn','Complete Without Other Tenures?','Risks If Exclude Other Tenures'])

        for item in queryset:
            if item.last_season is not None:
                last_season_burnt = item.last_season
            else:
                last_season_burnt = "Unknown"
            if item.last_year is not None:
                last_year_burnt = item.last_year
            else:
                last_year_burnt = "Unknown"

            if item.is_approved:
                try:
                    approved_until = date(item.current_approval.valid_to)
                except:
                    approved_until = ""
            else:
                approved_until = ""

            proposed_ignitions = ('"%s"' % ", ".join(
                ",".join('{0}:{1}'.format(x.seqno, ignition_type)
                         for ignition_type
                         in (x.ignition_types.all() or ("Unset",))
                         )
                for x in item.lightingsequence_set.order_by('seqno'))
            )
            actual_ignitions = ('"%s"' % ",".join(
                ",".join('{0}:{1}'.format(x.ignition.strftime('%d/%m/%Y'),
                                          ignition_type)
                         for ignition_type
                         in (x.ignition_types.all() or ("Unset",))
                         )
                for x in item.areaachievement_set.order_by('ignition'))
            )
            forecast_areas = '"%s"' % ",".join(x.name for x
                                               in item.forecast_areas.all())
            treatment_area = item.total_treatment_area
            burnt_area_estimate = item.total_burnt_area_estimate
            burnt_area_estimate_modified = item.total_burnt_area_estimate_modified
            length_of_edging = item.total_edging_length
            depth_of_edging = item.total_edging_depth
            objectives = '"%s"' % ",".join(x.objectives for x in item.objective_set.all())
            shires = '"%s"' % ",".join(x.name for x in item.shires.all())
            purposes = '"%s"' % ",".join(x.name for x in item.purposes.all())
            fuel_types = '"%s"' % ",".join(x.name for x in item.fuel_types.all())
            fuel_descriptions = '"%s"' % ",".join(
                x.fuel_description for x in item.lightingsequence_set.all())
            tenures = '"%s"' % ",".join(x.name for x in item.tenures.all())
            escape_dates = ", ".join([
                datetime.strftime(x.date_escaped, '%d/%m/%Y')
                for x in item.areaachievement_set.filter(date_escaped__isnull=False).order_by('ignition')
            ])
            dpaw_fire_nums = '"%s"' % ",".join(
                x.dpaw_fire_no for x in item.areaachievement_set
                .exclude(dpaw_fire_no__isnull=True)
                .exclude(dpaw_fire_no__exact='')
                .order_by('ignition'))
            dfes_fire_nums = '"%s"' % ",".join(
                x.dfes_fire_no for x in item.areaachievement_set
                .exclude(dfes_fire_no__isnull=True)
                .exclude(dfes_fire_no__exact='')
                .order_by('ignition'))
            success_criterias = '"%s"' % ",".join(
                x.criteria for x in item.successcriteria_set.all().order_by('id'))
            success_criteria_outcomes = '"%s"' % ",".join(
                x.criteria.criteria + ':' + x.get_achieved_display() + ':' + x.summary
                for x in Evaluation.objects
                .filter(criteria__in=item.successcriteria_set.all().order_by('id'))
                .exclude(achieved__isnull=True)
                .exclude(summary__isnull=True))
            observations = '"%s"' % ",".join(
                (x.observations or "No observation") + ':' + (x.action or "No action")
                for x in item.proposedaction_set.all().order_by('id'))
            proposed_actions = '"%s"' % ",".join(
                (x.observations or "No observation") + ':' + (x.action or "No action")
                for x in item.proposedaction_set.all().order_by('id'))
            endorsements = '"%s"' % ",".join(
                x.role.name + ':' + x.get_endorsed_display()
                for x in item.endorsement_set.all())
            approvals = '"%s"' % ",".join(
                x.creator.get_full_name() + ':' + x.valid_to.strftime('%d/%m/%Y') + '(%s)' %
                x.extension_count for x in item.approval_set.all())

            writer.writerow([
                item.region, item.district, item.name, item.burn_id,
                item.modified.astimezone(local_zone).strftime('%d/%m/%Y %H:%M:%S'),
                item.get_planning_status_display(),
                item.get_endorsement_status_display(),
                item.get_approval_status_display(),
                item.get_ignition_status_display(),
                "Yes" if item.status == item.STATUS_CLOSED else "No",
                item.maximum_complexity,
                item.get_priority_display(), item.maximum_risk,
                "Yes" if item.contentious else "No",
                item.contentious_rationale, item.location,
                item.prescribing_officer, item.financial_year,
                proposed_ignitions, actual_ignitions, forecast_areas,
                item.treatment_percentage, item.area, item.perimeter,
                treatment_area, burnt_area_estimate, burnt_area_estimate_modified,
                length_of_edging, depth_of_edging,
                shires, item.bushfire_act_zone, item.prohibited_period,
                purposes, objectives,
                actual_ignitions,
                item.allocations,
                fuel_types, fuel_descriptions,
                tenures, last_year_burnt, last_season_burnt, escape_dates,
                dpaw_fire_nums, dfes_fire_nums, item.short_code,
                item.get_remote_sensing_priority_display(),
                "Yes" if item.aircraft_burn else "No", success_criterias,
                success_criteria_outcomes, observations, proposed_actions,
                endorsements,
                item.endorsement_status_modified.astimezone(
                    local_zone).strftime('%d/%m/%Y %H:%M:%S') if item.endorsement_status_modified else "",
                approvals,
                item.approval_status_modified.astimezone(
                    local_zone).strftime('%d/%m/%Y %H:%M:%S') if item.approval_status_modified else "",
                approved_until,
                item.rationale,
                "Yes" if item.non_calm_tenure else ("--------" if item.non_calm_tenure is None else "No"),
                item.non_calm_tenure_included,item.non_calm_tenure_value,
                ("Yes" if item.non_calm_tenure_complete == 1  else ( "No" if item.non_calm_tenure_complete == 2 else "Yes & No")) if item.non_calm_tenure else "",
                item.non_calm_tenure_risks
            ])

        return response
    export_to_csv.short_description = ugettext_lazy("Export to CSV")

    def response_post_save_add(self, request, obj):
        """
        Override the redirect url after successful save of a new burn plan.
        """

        # a simple hack to set the default prescribing officer
        if obj is not None and obj.prescribing_officer is None:
            obj.prescribing_officer = request.user
            obj.save()

        if obj is not None and obj.creator_id == 1:
            obj.creator = request.user
            obj.save()

        url = reverse('admin:prescription_prescription_detail',
                      args=[str(obj.id)])
        return HttpResponseRedirect(url)

    def response_post_save_change(self, request, obj):
        """
        Override the redirect url after successful save of an existing burn
        plan.
        """
        url = reverse('admin:prescription_prescription_detail',
                      args=[str(obj.id)])
        return HttpResponseRedirect(url)

    def get_fieldsets(self, request, obj=None):
        """
        Tweak fieldsets based on whether the user is creating a new
        prescription or editing an existing one.
        """
        if obj:
            return (('Corporate Burn Attribute Summary', {
                "fields": ('name', 'description', ('financial_year', 'planned_season'),
                           ('last_year', 'last_season',
                            'last_year_unknown', 'last_season_unknown'),
                           'region', 'district', 'location',
                           'forest_blocks',
                           ('priority', 'rationale'),
                           ('contentious', 'contentious_rationale'),
                           'aircraft_burn',
                           # TODO: PBS-1551 # 'allocation',
                           'remote_sensing_priority', 'purposes',
                           ('area', 'perimeter', 'treatment_percentage'),
                           ('non_calm_tenure','non_calm_tenure_approved','non_calm_tenure_included','non_calm_tenure_value','non_calm_tenure_complete','non_calm_tenure_risks')
                          )
            }), ('Other Attributes', {
                "fields": ('tenures', 'fuel_types', 'shires',
                           'bushfire_act_zone', 'prohibited_period',
                           'forecast_areas', 'prescribing_officer',
                           'short_code')
            }))
        else:
            return super(PrescriptionAdmin, self).get_fieldsets(request, obj)

    def get_readonly_fields(self, request, obj=None):
        # NOTE: Data Admins can edit all fields at any status.
        if request.user.has_perm('prescription.can_admin'):
            return (None,)
        elif obj and obj.planning_status != obj.PLANNING_DRAFT:
            return ('name', 'description', 'burn_id', 'financial_year', 'planned_season',
                    'last_year', 'last_season', 'last_season_unknown',
                    'last_year_unknown', 'priority', 'rationale',
                    'region', 'district', 'contentious',
                    'contentious_rationale')
        elif obj and not obj.is_draft:
            return (None,)
        else:
            return super(PrescriptionAdmin, self).get_readonly_fields(
                request, obj)

    def formfield_for_dbfield(self, db_field, **kwargs):
        # today = timezone.now().date()
        # if db_field.name == 'planned_year':
        #     kwargs['initial'] = today.year

        if db_field.name == 'planned_season':
            kwargs['initial'] = Season.SEASON_ANNUAL

        # This is commented out because there are two possible seasons
        # for each period. We need a dataset to relate the region to the
        # seasons they will use (tropical, temperate), otherwise we will
        # not be able to pre-populate this field.
        # season = Season.objects.get(start__lte=today, end__gte=today)
        # if db_field.name == 'planned_season':
        #     kwargs['initial'] = season.name

        return super(PrescriptionAdmin, self).formfield_for_dbfield(
            db_field, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Populate some of the foreign keys with initial data.
        """
        # profile = request.user.get_profile()
        profile = request.user.profile
        if db_field.name == 'region' and profile.region is not None:
            kwargs['initial'] = profile.region.pk
            return db_field.formfield(**kwargs)

        if db_field.name == 'district' and profile.district is not None:
            kwargs['initial'] = profile.district.pk
            return db_field.formfield(**kwargs)

        if db_field.name == 'prescribing_officer':
            kwargs['initial'] = request.user.pk
            field = db_field.formfield(**kwargs)
            return field

        return super(PrescriptionAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Replace the widget for the burn purposes with our own checkbox select.
        """
        if db_field.name == 'purposes':
            kwargs['widget'] = CheckboxSelectMultiple()

        return super(PrescriptionAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs)

    def get_form_class(self, request, obj=None):
        if obj:
            return self.edit_form
        else:
            return self.form

    def get_form(self, request, obj=None, **kwargs):
        """
        Returns a Form class for use in the admin add view. This is used by
        add_view and change_view.
        """
        # if self.declared_fieldsets:
        if hasattr(self, 'declared_fieldsets'):
            fields = flatten_fieldsets(self.get_fieldsets(request, obj))
        else:
            fields = None
        if self.exclude is None:
            exclude = []
        else:
            exclude = list(self.exclude)
        exclude.extend(self.get_readonly_fields(request, obj))

        form = self.get_form_class(request, obj)

        if self.exclude is None and (
            hasattr(form, '_meta') and form._meta.exclude
        ):
            # Take the custom ModelForm's Meta.exclude into account only if the
            # ModelAdmin doesn't define its own.
            exclude.extend(self.form._meta.exclude)
        # if exclude is an empty list we pass None to be consistent with the
        # default on modelform_factory
        exclude = exclude or None
        defaults = {
            "form": form,
            "fields": fields,
            "exclude": exclude,
            "widgets": form._meta.widgets if hasattr(form,"_meta") and hasattr(form._meta,"widgets") else None,
            "formfield_callback": partial(self.formfield_for_dbfield,
                                          request=request),
        }
        kwargs.pop('change', None)
        defaults.update(kwargs)

        try:
            return modelform_factory(self.model, **defaults)
        except FieldError as e:
            raise FieldError('%s. Check fields/fieldsets/exclude'
                             ' attributes of class %s.'
                             % (e, self.__class__.__name__))

    def detail_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, unquote(object_id))
        if not obj:
            raise Http404('Prescription with primary key {} does not exist'.format(object_id))

        # the epfp approval modal
        submit_for_epfp_approval_title = self._approve_title(obj)
        AdminAddApprovalForm = self._approve_approval_form(request)
        form = AdminAddApprovalForm(initial={'prescription': obj})
        submit_for_epfp_approval_form, media = self._approve_form(
            request, obj, form)

        context = {
            'current': obj,
            'submit_for_epfp_approval_form': submit_for_epfp_approval_form,
            'submit_for_epfp_approval_title': submit_for_epfp_approval_title,
            'media': media,
        }
        context.update(extra_context or {})

        return super(PrescriptionAdmin, self).detail_view(
            request, object_id, context)

    def corporate_approve(self, request, object_id, extra_context=None):
        """
        View to manage corporate approval of an ePFP.
        """
        obj = self.get_object(request, unquote(object_id))
        if request.method == 'POST':
            url = reverse('admin:prescription_prescription_detail',
                          args=[str(obj.id)])
            if request.POST.get('_cancel'):
                return HttpResponseRedirect(url)
            if request.POST.get('_save'):
                if (obj.planning_status == obj.PLANNING_DRAFT and obj.can_corporate_approve):
                    obj.planning_status = obj.PLANNING_SUBMITTED
                    obj.planning_status_modified = timezone.now()
                    obj.save()
                    self.message_user(
                        request, "Successfully submitted for corporate approval.")
                    return HttpResponseRedirect(url)
                if obj.planning_status == obj.PLANNING_SUBMITTED:
                    # Only ePFP Application Administrator can apply corporate approval
                    if ((not request.user.has_perm(
                         'prescription.can_corporate_approve'))):
                        raise PermissionDenied

                    obj.planning_status = obj.PLANNING_APPROVED
                    obj.planning_status_modified = timezone.now()
                    obj.save()
                    self.message_user(
                        request, "Corporate approval successful.")
                    return HttpResponseRedirect(url)
            elif request.POST.get('_delete'):
                if (obj.planning_status == obj.PLANNING_APPROVED and request.user.has_perm('prescription.can_admin')):
                    obj.planning_status = obj.PLANNING_DRAFT
                    obj.planning_status_modified = timezone.now()
                    obj.save()
                    self.message_user(
                        request, "Successfully deleted for corporate approval.")
                    return HttpResponseRedirect(url)

        context = {
            'current': obj,
        }
        return TemplateResponse(request, self.corporate_approval_template,
                                context, current_app=self.admin_site.name)

    def endorse(self, request, object_id, extra_context=None):
        """
        View to manage endorsement of an ePFP.
        """
        obj = self.get_object(request, unquote(object_id))

        title = "Endorse this ePFP"
        if obj.endorsement_status == obj.ENDORSEMENT_DRAFT:
            title = "Submit for endorsement"

        form = AddEndorsementForm(request.POST or None, request=request)

        if request.method == 'POST':
            url = reverse('admin:prescription_prescription_detail',
                          args=[str(obj.id)])
            if request.POST.get('_cancel'):
                return HttpResponseRedirect(url)
            if obj.endorsement_status == obj.ENDORSEMENT_DRAFT and obj.can_endorse:
                obj.endorsement_status = obj.ENDORSEMENT_SUBMITTED
                obj.endorsement_status_modified = timezone.now()
                obj.save()

                # Remove all object permissions for sections that can't be
                # modified after submitting for endorsement
                update_permissions(obj, self.admin_site, 'endorsement')

                # a simple hack to set the default prescribing officer
                if obj is not None and obj.prescribing_officer is None:
                    obj.prescribing_officer = request.user
                    obj.save()

                self.message_user(
                    request, "Successfully submitted for endorsement.")
                return HttpResponseRedirect(url)
            if obj.endorsement_status == obj.ENDORSEMENT_SUBMITTED or obj.endorsement_status == obj.ENDORSEMENT_APPROVED:
                # create an endorsement
                if form.is_valid():
                    endorsement = form.save(commit=False)
                    endorsement.prescription = obj
                    endorsement.endorsed = (
                        request.POST.get('_dont_endorse') is None)
                    endorsement.creator = request.user
                    endorsement.modifier = request.user
                    endorsement.save()
                    group = Group.objects.get(name='ePFP Application Administrator')
                    assign_perm('delete_endorsement', group, endorsement)

                # check that all needed endorsements are there
                if obj.all_reviewed:
                    if obj.all_endorsed:
                        obj.endorsement_status = obj.ENDORSEMENT_APPROVED
                        msg = (" All endorsements have been completed on "
                               "this ePFP.")
                        group = Group.objects.get(name='ePFP Application Administrator')
                    else:
                        logger.warning('Prescription {} - all endorsements input but "delete all" business logic triggered'.format(obj))
                        for i in obj.endorsement_set.all():
                            logger.info('Staff: {}, role: {}, endorsement: {}'.format(i.creator.get_full_name(), i.role, i.endorsed))
                        msg = (" All endorsements have been reviewed but some "
                               "of them have not been endorsed on this ePFP.")
                    obj.save()
                    self.message_user(
                        request, "Successfully added endorsement." +
                        msg)
                else:
                    self.message_user(
                        request, "Successfully added endorsement.")
                return HttpResponseRedirect(url)

        form.fields['role'].queryset = obj.not_endorsed_endorsing_roles

        group = Group.objects.get(name='ePFP Application Administrator')
        for endorsement in obj.endorsement_set.all():
            assign_perm('delete_endorsement', group, endorsement)

        context = {
            'title': title,
            'current': obj,
            'errors': None,
            'form': form,
            'endorsed_endorsing_roles': obj.endorsement_set.all(),
            'not_endorsed_endorsing_roles': obj.not_endorsed_endorsing_roles,
        }
        return TemplateResponse(request, "admin/prescription/prescription/"
                                "endorsement.html", context,
                                current_app=self.admin_site.name)

    def delete_endorsement(self, request, object_id, endorsement_id,
                           extra_context=None):
        obj = self.get_object(request, unquote(object_id))

        if obj is None:
            raise Http404(_('%(name)s object with primary key (%key)r'
                            ' does not exist.') %
                          {'name': force_text(self.opts.verbose_name),
                           'key': object_id})

        endorsement = obj.endorsement_set.get(pk=unquote(endorsement_id))

        if not request.user.has_perm('prescription.delete_endorsement'):
            raise PermissionDenied

        if request.method == 'POST':
            # The user has confirmed they wish to delete the endorsement
            endorsement.delete()
            msg = 'Delete Endorsement', 'Burn ID: {}, Role: {}, Endorsed by: {}, Deleted by: {}'. format(obj.burn_id, endorsement.role, endorsement.modifier.get_full_name(), request.user.get_full_name())
            logger.warning(msg)
            support_email('Delete Endorsement', msg)
            self.message_user(request, "Successfully deleted endorsement.")
            url = reverse('admin:prescription_prescription_endorse', args=(obj.id,))
            return HttpResponseRedirect(url)

        context = {
            'title': "Delete endorsement",
            'current': obj,
            'endorsement': endorsement
        }
        context.update(extra_context or {})

        return TemplateResponse(request, "admin/prescription/prescription/delete_endorsement.html", context, current_app=self.admin_site.name)

    def endorsing_roles(self, request, object_id, extra_context=None):
        """
        View to manage determining additional endorsement roles in an ePFP.
        """
        class AdminEndorsingRoleForm(EndorsingRoleForm):
            formfield_callback = partial(
                self.formfield_for_dbfield, request=request)

            def __init__(self, *args, **kwargs):
                super(AdminEndorsingRoleForm, self).__init__(*args, **kwargs)
                self.fields["endorsing_roles"].queryset = EndorsingRole.objects.filter(archived=False)

        obj = self.get_object(request, unquote(object_id))

        if obj is None:
            raise Http404(_('%(name)s object with primary key (%key)r'
                            ' does not exist.') %
                          {'name': force_text(self.opts.verbose_name),
                           'key': object_id})

        if request.method == 'POST':
            form = AdminEndorsingRoleForm(request.POST, instance=obj)
            url = reverse('admin:prescription_prescription_detail',
                          args=[str(obj.id)])
            if request.POST.get('_cancel'):
                return HttpResponseRedirect(url)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.endorsing_roles_determined = True
                obj.save()
                form.save_m2m()
                self.message_user(
                    request, "Successfully saved endorsing officers.")
                return HttpResponseRedirect(url)
        else:
            form = AdminEndorsingRoleForm(instance=obj)

        admin_form = helpers.AdminForm(
            form, [(None, {'fields': list(form.base_fields)})],
            self.get_prepopulated_fields(request, obj),
            self.get_readonly_fields(request, obj),
            model_admin=self)
        media = self.media + admin_form.media
        context = {
            'title': 'Determine endorsing roles',
            'form': admin_form,
            'media': media,
            'current': obj,
            'errors': None
        }
        return TemplateResponse(request, "admin/prescription/prescription/"
                                "endorsing_roles.html", context,
                                current_app=self.admin_site.name)

    def delete_regional_objective(self, request, object_id, objective_id, extra_context=None):
        obj = self.get_object(request, unquote(object_id))

        if obj is None:
            raise Http404(_('%(name)s object with primary key (%key)r'
                            ' does not exist.') %
                          {'name': force_text(self.opts.verbose_name),
                           'key': object_id})

        regional_objective = obj.regional_objectives.get(pk=unquote(objective_id))

        can_delete = request.user.has_perm('prescription.change_prescription') or request.user.is_superuser
        if not can_delete:
            raise PermissionDenied

        if request.method == 'POST':
            # The user has confirmed they wish to delete the regional objective from ePFP
            obj.regional_objectives.remove(regional_objective)
            self.message_user(request, "Successfully removed regional objective from ePFP({}).".format(obj.burn_id))
            url = reverse('admin:risk_context_changelist', args=(obj.id,))

            return HttpResponseRedirect(url)

        context = {
            'title': "Remove regional objective from ePFP",
            'current': obj,
            'regional_objective': regional_objective,
            'can_delete': can_delete
        }
        context.update(extra_context or {})

        return TemplateResponse(request, "admin/prescription/prescription/delete_regional_objective.html", context, current_app=self.admin_site.name)

    def _approve_title(self, obj):
        if obj.approval_status == obj.APPROVAL_DRAFT:
            title = "Submit for approval"
        elif obj.approval_status == obj.APPROVAL_SUBMITTED:
            title = "Approve ePFP {} ({})".format(obj.burn_id, obj.financial_year)
        elif obj.approval_status == obj.APPROVAL_APPROVED:
            title = "Approve extension of ePFP {} ({})".format(
                obj.burn_id, obj.financial_year)

        return title

    def _approve_form(self, request, obj, form):
        admin_form = helpers.AdminForm(
            form, [(None, {'fields': list(form.base_fields)})],
            self.get_prepopulated_fields(request, obj),
            self.get_readonly_fields(request, obj),
            model_admin=self)
        media = self.media + admin_form.media

        return admin_form, media

    def _approve_approval_form(self, request):
        class AdminAddApprovalForm(AddApprovalForm):
            formfield_callback = partial(
                self.formfield_for_dbfield, request=request)
        return AdminAddApprovalForm

    def approve(self, request, object_id, extra_context=None):
        """
        View to manage corporate approval of an ePFP.
        """
        obj = self.get_object(request, unquote(object_id))
        title = self._approve_title(obj)

        AdminAddApprovalForm = self._approve_approval_form(request)

        form = AdminAddApprovalForm(initial={'prescription': obj})
        if request.method == 'POST':
            url = reverse('admin:prescription_prescription_detail',
                          args=[str(obj.id)])
            if obj.approval_status == obj.APPROVAL_DRAFT and obj.can_approve:
                # create an approval
                obj.approval_status = obj.APPROVAL_SUBMITTED
                obj.approval_status_modified = timezone.now()
                obj.save()
                self.message_user(
                    request, "Successfully submitted for approval.")
                return HttpResponseRedirect(url)
            elif obj.approval_status == obj.APPROVAL_SUBMITTED:
                if request.POST.get('_cancel'):
                    obj.clear_approvals()
                    msg = 'Delete: Clearing Approvals/Endorsements', 'Burn ID: {}, Deleted by: {}'. format(obj.burn_id, request.user.get_full_name())
                    logger.warning(msg)
                    support_email('Delete: Clearing Approvals/Endorsements', msg)

                    self.message_user(
                        request, "Approval rejected. ePFP is now draft.")
                    return HttpResponseRedirect(url)

                form = AdminAddApprovalForm(request.POST,
                                            initial={'prescription': obj})
                if form.is_valid():
                    approval = form.save(commit=False)
                    approval.prescription = obj
                    approval.creator = request.user
                    approval.modifier = request.user
                    approval.save()
                    obj.approval_status = obj.APPROVAL_APPROVED
                    obj.approval_status_modified = timezone.now()
                    obj.save()
                    self.message_user(
                        request, "Successfully approved.")
                    return HttpResponseRedirect(url)
            elif obj.is_approved:
                if obj.is_closed:
                    self.message_user(
                        request, "You can't extend an approval after the "
                                 "prescribed fire plan has been closed.")
                    return HttpResponseRedirect(url)
                if request.POST.get('_cancel'):
                    self.message_user(
                        request, "Didn't extend approval.")
                    return HttpResponseRedirect(url)
                else:
                    approval = obj.current_approval
                    if approval and approval.extension_count < 3:
                        approval.extension_count = approval.extension_count + 1
                        approval.valid_to = approval.next_valid_to
                        approval.save()
                        self.message_user(
                            request, "Successfully extended approval.")
                    else:
                        self.message_user(request, "You can't extend an "
                                          "approval more than 3 times.")
                    return HttpResponseRedirect(url)

        admin_form, media = self._approve_form(request, obj, form)

        context = {
            'title': title,
            'current': obj,
            'form': admin_form,
            'media': media,
            'errors': None,
        }
        return TemplateResponse(request, "admin/prescription/prescription/"
                                "approval.html", context,
                                current_app=self.admin_site.name)

    def sitemap(self, request, object_id, extra_context=None):
        """
        View to manage closure of an ePFP.
        """
        obj = self.get_object(request, unquote(object_id))
        title = "Sitemap"

        context = {
            'title': title,
            'current': obj,
        }
        return TemplateResponse(request, "admin/prescription/prescription/"
                                "sitemap.html", context,
                                current_app=self.admin_site.name)

    def close(self, request, object_id, extra_context=None):
        """
        View to manage closure of an ePFP.
        """
        obj = self.get_object(request, unquote(object_id))
        title = "Close this ePFP"

        if request.method == 'POST':
            url = reverse('admin:prescription_prescription_detail',
                          args=[str(obj.id)])
            if request.POST.get('_cancel'):
                return HttpResponseRedirect(url)

            if obj.is_approved and obj.post_state.post_burn_checklist:
                # close the burn
                post_state = obj.post_state
                post_state.closure_declaration = True
                if not post_state.creator:
                    post_state.creator = request.user
                post_state.modifier = request.user
                post_state.save()
                obj.status = obj.STATUS_CLOSED
                obj.status_modified = timezone.now()
                obj.closure_officer = request.user
                obj.save()

                # Remove all object permissions for sections that can't be
                # modified after closure. (Pretty much everything.)
                update_permissions(obj, self.admin_site, 'closure')

                self.message_user(
                    request, "Burn closed successfully.")
                return HttpResponseRedirect(url)

        context = {
            'title': title,
            'current': obj,
        }
        return TemplateResponse(request, "admin/prescription/prescription/"
                                "closure.html", context,
                                current_app=self.admin_site.name)

    def add_objectives(self, request, object_id):
        """
        Custom view to allow the user to select which objectives from the
        prescription's region fit.
        """
        # TODO: make a form to handle this...
        obj = self.get_object(request, unquote(object_id))
        if request.method == "POST":
            selected = request.POST.getlist('objectives')
            added, removed = False, False
            for objective in RegionalObjective.objects.filter(
                pk__in=selected
            ).exclude(pk__in=obj.regional_objectives.all()):
                obj.regional_objectives.add(objective)
                added = True
            for objective in obj.regional_objectives.exclude(pk__in=selected):
                obj.regional_objectives.remove(objective)
                removed = True
            if added and removed:
                message = "added and removed successfully."
            elif added:
                message = "added successfully."
            elif removed:
                message = "removed successfully."
            else:
                message = "were not changed."
            self.message_user(request, "Regional objectives " + message)
            url = request.REQUEST.get('next', reverse(
                'admin:prescription_prescription_detail', args=[str(obj.id)]))
            return HttpResponseRedirect(url)

        objectives = RegionalObjective.objects.filter(
            region=obj.region).exclude(pk__in=obj.regional_objectives.all())
        context = {
            'current': obj,
            'objectives': objectives,
            'current_app': self.admin_site.name,
        }
        # return TemplateResponse(request, self.objectives_template,
        #                         context, current_app=self.admin_site.name)
        return TemplateResponse(request, self.objectives_template, context)

    def summary(self, request, object_id):
        """
        A custom view to display section A1 of an ePFP.
        """
        obj = self.get_object(request, unquote(object_id))

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r'
                            ' does not exist.') %
                          {'name': force_text(self.opts.verbose_name),
                           'key': object_id})

        if request.method == "POST":
            form = SummaryCompletionStateForm(request.POST,
                                              instance=obj.pre_state)
            if form.is_valid():
                form.save()
                if request.is_ajax():
                    message = "Summary updated."
                    return HttpResponse(json.dumps({'message': message}))
                else:
                    url = reverse('admin:index')
                    return HttpResponseRedirect(url)
            else:
                if request.is_ajax():
                    return HttpResponse(json.dumps({'errors': form.errors}))
        else:
            form = SummaryCompletionStateForm(instance=obj.pre_state)
        context = {
            'current': obj,
            'form': form,
            'current_app':self.admin_site.name,
        }
        # return TemplateResponse(request, self.summary_template,
        #                         context, current_app=self.admin_site.name)
        return TemplateResponse(request, self.summary_template,
                                context)

    def pre_summary(self, request, object_id):
        """
        A custom view to display section A1 of an ePFP.
        """
        obj = self.get_object(request, unquote(object_id))
        AdminPrescriptionSummaryForm = self.get_form(request, obj)
        print(AdminPrescriptionSummaryForm)

        funding_choices = FundingAllocation._meta.get_field('allocation').choices
        # I have not been able to pass this queryset in as a keyword param to FundingAllocationFormSet
        # so this queryset code is duplicated in the FundingAllocationInlineFormSet.__init__
        initial_queryset = FundingAllocation.objects.filter(prescription=obj)
        FundingAllocationFormSet = inlineformset_factory(
            parent_model=Prescription, model=FundingAllocation,
            formset=FundingAllocationInlineFormSet,
            fields='__all__',
            extra=len(funding_choices) - initial_queryset.count())
        # FundingAllocationFormSet = inlineformset_factory(
        #     parent_model=Prescription, model=FundingAllocation,
        #     formset=FundingAllocationInlineFormSet,
        #     extra=len(funding_choices) - initial_queryset.count(),
        #     form=AdminPrescriptionSummaryForm)
        # Top up initial data with missing allocations
        existing_allocations = {fa.id: (fa.allocation, fa.proportion) for fa in initial_queryset}
        initial_choices_dict = {k: 0 for k, v in funding_choices}
        # for i, (a, p) in existing_allocations.iteritems():
        for i, (a, p) in existing_allocations.items():
            if a in initial_choices_dict:
                initial_choices_dict.pop(a)
        # initial_choices_dict.update(existing_allocations)
        # initial_choices = [
        #     {'prescription': obj.pk, 'allocation': k, 'proportion': v} for k, v in initial_choices_dict.iteritems()]
        initial_choices = [
            {'prescription': obj.pk, 'allocation': k, 'proportion': v} for k, v in initial_choices_dict.items()]

        if request.method == "POST":
            data = request.POST
            form = AdminPrescriptionSummaryForm(data=data, instance=obj)
            formset_data = fund_allocation.harvest(data)
            formset = FundingAllocationFormSet(data=formset_data,
                                               prescription=obj,
                                               instance=obj)

            form_valid = form.is_valid()
            formset_valid = formset.is_valid()
            if form_valid and formset_valid:
                form.save()
                formset.save()
                if request.is_ajax():
                    message = obj.__str__() + ' summary updated successfully.'
                    return HttpResponse(json.dumps({'message': message, 'description': obj.description}))
                else:
                    return HttpResponseRedirect(obj.get_absolute_url())
            else:
                if request.is_ajax():
                    formset_errors = formset.errors
                    cross_form_errors = formset.non_form_errors()
                    # Apply cross form errors to whole form
                    formset_errors.append({'id': cross_form_errors})
                    errors = {
                        'errors': form.errors,
                        'formset_errors': formset_errors,
                    }
                    return HttpResponse(json.dumps(errors))
        else:
            form = AdminPrescriptionSummaryForm(instance=obj)
            formset = FundingAllocationFormSet(prescription=obj, instance=obj, initial=initial_choices)

        admin_form = helpers.AdminForm(
            form, [(None, {'fields': list(form.base_fields)})],
            self.get_prepopulated_fields(request, obj),
            self.get_readonly_fields(request, obj),
            model_admin=self)
        media = self.media + admin_form.media

        context = {
            'current': obj,
            'form': admin_form,
            'formset': formset,
            'media': media,
            'max_risk': obj.get_maximum_risk,
            'max_complexity': obj.get_maximum_complexity,
            'purposes': [p.name for p in obj.purposes.all()],
            'current_app': self.admin_site.name
        }
        # return TemplateResponse(request, self.pre_summary_template,
        #                         context, current_app=self.admin_site.name)
        return TemplateResponse(request, self.pre_summary_template,
                                context)

    def pdf_summary(self, request, object_id, extra_context=None):
        """
        View to manage PDF created.
        """
        obj = self.get_object(request, unquote(object_id))
        title = "PDFs"

        cmd = ['fexsend', '-l', '-v']
        run = subprocess.Popen(' '.join(cmd), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        fex_tokens = run.communicate()[0]

        token_str = self.__find_between(fex_tokens, '<pre>', '</pre>')
        tokens = [token for token in token_str.split('<--') if 'dkey' in token]

        fex_file_list = []
        for token in tokens:
            pdf = self.__find_between(token, '>', '<')
            dkey = self.__find_between(token, 'dkey=', '&')
            expiry = self.__find_between(token, '[', ']')
            size = self.__find_between(token, '   ', ' [').strip()
            size = '< 1 MB' if size == '0 MB' else size
            if not pdf.endswith("_pfp.pdf"):  # exclude non-pfp's
                continue

            try:
                timestamp = datetime.strptime(pdf.split('_')[-2], '%Y-%m-%dT%H%M')
            except ValueError:
                timestamp = datetime.strptime(pdf.split('_')[-2], '%Y-%m-%dT%H%M%S')

            fex_file_list.append([
                pdf,
                settings.FEX_SVR_HTTP + '/fop/' + dkey + '/' + pdf,
                size,
                expiry,
                timestamp,
            ])

        fex_file_list = sorted(fex_file_list, key=lambda x: x[4], reverse=True)

        context = {
            'title': title,
            'current': obj,
            'fex_file_list': fex_file_list,
        }
        return TemplateResponse(request, self.pdf_summary_template,
                                context, current_app=self.admin_site.name)

    def __find_between(self, s, first, last):
        """
        Find the substring between the first and last chars/strings
        """
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""

    def day_summary(self, request, object_id):
        """
        A custom view to display the summary of Part B of an ePFP.
        """
        obj = self.get_object(request, unquote(object_id))

        if obj is None:
            raise Http404(_('%(name)s object with primary key (%key)r'
                            ' does not exist.') % {
                                'name': force_text(self.opts.verbose_name),
                                'key': object_id})

        if request.method == "POST":
            form = BurnImplementationStateForm(request.POST,
                                               instance=obj.day_state)
            if form.is_valid():
                form.save()
                if request.is_ajax():
                    message = "Summary updated."
                    return HttpResponse(json.dumps({'message': message}))
                else:
                    url = reverse('admin:index')
                    return HttpResponseRedirect(url)
            else:
                if request.is_ajax():
                    return HttpResponse(json.dumps({'errors': form.errors}))
        else:
            form = BurnImplementationStateForm(instance=obj.day_state)

        context = {
            'current': obj,
            'form': form,
            'current_app':self.admin_site.name,
        }
        # return TemplateResponse(request, self.day_summary_template,
        #                         context, current_app=self.admin_site.name)
        return TemplateResponse(request, self.day_summary_template,
                                context)

    def post_summary(self, request, object_id):
        """
        A custom view to display the summary of Part C of an ePFP.
        """
        obj = self.get_object(request, unquote(object_id))

        if obj is None:
            raise Http404(_('%(name)s object with primary key (%key)r'
                            ' does not exist.') % {
                                'name': force_text(self.opts.verbose_name),
                                'key': object_id})

        if request.method == "POST":
            form = BurnClosureStateForm(request.POST, instance=obj.post_state)
            if form.is_valid():
                form.save()
                if request.is_ajax():
                    message = "Summary updated."
                    return HttpResponse(json.dumps({'message': message}))
                else:
                    url = reverse('admin:index')
                    return HttpResponseRedirect(url)
            else:
                if request.is_ajax():
                    return HttpResponse(json.dumps({'errors': form.errors}))
        else:
            form = BurnClosureStateForm(instance=obj.post_state)

        context = {
            'current': obj,
            'form': form,
        }
        return TemplateResponse(request, self.post_summary_template,
                                context, current_app=self.admin_site.name)

    def pdflatex(self, request, object_id):
        prescription = self.get_object(request, unquote(object_id))
        return download_pdf(request,prescription)

class PrescriptionMixin(object):
    prescription_filter_field = "prescription"

    def __init__(self, model, admin_site):
        self.prescription = None
        return super(PrescriptionMixin, self).__init__(model, admin_site)

    def get_urls(self):
        # from django.conf.urls import url
        from django.urls import re_path

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
           re_path(r'^prescription/(\d+)/$',
                wrap(self.changelist_view),
                name='%s_%s_changelist' % info),
           re_path(r'^add/prescription/(\d+)/$',
                wrap(self.add_view),
                name='%s_%s_add' % info),
           re_path(r'^(.+)/history/prescription/(\d+)/$',
                wrap(self.history_view),
                name='%s_%s_history' % info),
           re_path(r'^(.+)/delete/prescription/(\d+)/$',
                wrap(self.delete_view),
                name='%s_%s_delete' % info),
           re_path(r'^(.+)/prescription/(\d+)/$',
                wrap(self.change_view),
                name='%s_%s_change' % info)
        ]
        return urlpatterns

    def get_changelist(self, request, **kwargs):
        ChangeList = super(PrescriptionMixin, self).get_changelist(
            request, **kwargs)
        admin = self

        class PrescriptionChangeList(ChangeList):
            def get_query_set(self, request):
                qs = super(PrescriptionChangeList, self).get_query_set(request)
                if admin.prescription is not None:
                    fields = {
                        admin.prescription_filter_field: admin.prescription
                    }
                    return qs.filter(**fields)
                else:
                    return qs
                
            def get_filters(self, request):
                if self.list_filter is None:
                    self.list_filter = []
                return super().get_filters(request)
                
            def get_queryset(self, request):
                qs = super(PrescriptionChangeList, self).get_queryset(request)
                if admin.prescription is not None:
                    fields = {
                        admin.prescription_filter_field: admin.prescription,
                    }
                    return qs.filter(**fields)
                else:
                    return qs

            def url_for_result(self, result):
                pk = getattr(result, self.pk_attname)
                # return reverse('admin:%s_%s_change' % (self.opts.app_label,
                #                                        self.opts.module_name),
                #                args=(quote(pk), quote(admin.prescription.pk)),
                #                current_app=self.model_admin.admin_site.name)
                return reverse('admin:%s_%s_change' % (self.opts.app_label,
                                                       self.opts.model_name),
                               args=(quote(pk), quote(admin.prescription.pk)),
                               current_app=self.model_admin.admin_site.name)

        return PrescriptionChangeList

    def get_prescription(self, request, object_id):
        """
        Returns an instance matching the primary key provided. ``None`` is
        returned if no match is found (or the object_id failed validation
        against the primary key field).
        WARNING: be very careful here -- setting state on a thread-local
        object so we have to ensure that it changes "per-request" and the
        only reason we set the state is to access it in methods that don't
        include prescription_id. This feels just as hacky as request.session.
        """
        queryset = Prescription.objects
        model = Prescription

        try:
            object_id = model._meta.pk.to_python(object_id)
            self.prescription = queryset.get(pk=object_id)
        except (Prescription.DoesNotExist, ValidationError, ValueError):
            self.prescription = None
        return self.prescription

    def changelist_view(self, request, prescription_id, extra_context=None):
        prescription = self.get_prescription(request, unquote(prescription_id))

        if prescription is None:
            raise Http404(_('prescription object with primary key %(key)r '
                            'does not exist.') % {'key': prescription_id})

        editable = self.get_list_editable(request)
        if not editable or 'id' in editable and len(editable) == 1:
            editable = False
        else:
            editable = True

        context = {
            'current': prescription,
            'editable': editable,
        }
        context.update(extra_context or {})
        #import ipdb; ipdb.set_trace()
        return super(PrescriptionMixin, self).changelist_view(
            request, extra_context=context)

    def add_view(self, request, prescription_id, form_url='',
                 extra_context=None):
        prescription = self.get_prescription(request, unquote(prescription_id))

        if prescription is None:
            raise Http404(_('prescription object with primary key %(key)r '
                            'does not exist.') % {'key': prescription_id})

        context = {
            'current': prescription
        }
        context.update(extra_context or {})

        return super(PrescriptionMixin, self).add_view(
            request, extra_context=context)

    def change_view(self, request, object_id, prescription_id,
                    extra_context=None):
        print('in change view')
        prescription = self.get_prescription(request, unquote(prescription_id))

        if prescription is None:
            raise Http404(_('prescription object with primary key %(key)r '
                            'does not exist.') % {'key': prescription_id})

        if request.method == 'POST' and "_saveasnew" in request.POST:
            opts = self.model._meta
            return self.add_view(request, prescription_id=prescription.id,
                                 form_url=reverse(
                                     'admin:%s_%s_add' %
                                     (opts.app_label, opts.model_name),
                                     args=[prescription.id],
                                     current_app=self.admin_site.name))

        context = {
            'current': prescription
        }
        context.update(extra_context or {})

        return super(PrescriptionMixin, self).change_view(
            request, object_id, extra_context=context)

    def history_view(self, request, object_id, prescription_id,
                     extra_context=None):
        prescription = self.get_prescription(request, unquote(prescription_id))

        if prescription is None:
            raise Http404(_('prescription object with primary key %(key)r '
                            'does not exist.') % {'key': prescription_id})

        context = {
            'current': prescription
        }
        context.update(extra_context or {})

        return super(PrescriptionMixin, self).history_view(
            request, object_id, extra_context=context)

    @csrf_protect_m
    @transaction.atomic
    def delete_view(self, request, object_id, prescription_id,
                    extra_context=None):
        "The 'delete' admin view for this model."
        opts = self.model._meta
        app_label = opts.app_label

        obj = self.get_object(request, unquote(object_id))
        prescription = self.get_prescription(request, unquote(prescription_id))

        if not self.has_delete_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(
                _('%(name)s object with primary key %(key)r does '
                  'not exist.') % {'name': force_text(opts.verbose_name),
                                   'key': escape(object_id)})

        if prescription is None:
            raise Http404(
                _('prescription object with primary key %(key)r does not '
                  'exist.') % {'key': prescription_id})

        using = router.db_for_write(self.model)

        # Populate deleted_objects, a data structure of all related objects
        # that will also be deleted.
        (deleted_objects, perms_needed, protected) = get_deleted_objects(
            [obj], opts, request.user, self.admin_site, using)

        if request.POST:    # The user has already confirmed the deletion.
            if perms_needed:
                raise PermissionDenied
            obj_display = force_text(obj)
            self.log_deletion(request, obj, obj_display)
            self.delete_model(request, obj)

            self.message_user(request, _(
                'The %(name)s "%(obj)s" was deleted successfully.') % {
                    'name': force_text(opts.verbose_name),
                    'obj': force_text(obj_display)},
                messages.SUCCESS)

            if self.has_change_permission(request, None):
                if "next" in request.GET:
                    post_url = request.GET['next']
                else:
                    post_url = reverse(
                        'admin:%s_%s_changelist' % (opts.app_label,
                                                    opts.model_name),
                        args=(quote(self.prescription.pk),),
                        current_app=self.admin_site.name)
            else:
                post_url = reverse('admin:index',
                                   current_app=self.admin_site.name)
            return HttpResponseRedirect(post_url)

        object_name = force_text(opts.verbose_name)

        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": object_name}
        else:
            title = _("Are you sure?")

        context = {
            "title": title,
            "object_name": object_name,
            'current': prescription,
            "object": obj,
            "deleted_objects": deleted_objects,
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": opts,
            "app_label": app_label,
            "current_app": self.admin_site.name,
        }
        context.update(extra_context or {})

        return TemplateResponse(request, self.delete_confirmation_template or [
            "admin/%s/delete_confirmation.html" % app_label,
            "admin/delete_confirmation.html"
        ], context)

    def get_readonly_fields(self, request, obj=None):
        """
        For any of our ePFP related admins, do not allow editing if the ePFP
        has been submitted for endorsement, has been endorsed, or has been
        approved. If the user is part of the ePFP Application Administrator, allow
        editing even after the ePFP has been locked.
        """
        if request.user.has_perm('prescription.can_admin'):
                return super(PrescriptionMixin, self).get_readonly_fields(request, obj)

        current = self.prescription
        if current and not current.is_draft:
            return self.list_editable
        else:
            return super(PrescriptionMixin, self).get_readonly_fields(request, obj)

    def get_changelist_form(self, request, **kwargs):
        return self.get_form(request, **kwargs)

    def get_list_display(self, request):
        """
        Allow the use of the current request inside our remove function.
        This lets us check if the current user has permission to delete a
        particular object.
        """
        delete = partial(self.remove, request=request)
        delete.short_description = ""
        delete.allow_tags = True
        list_display = list(self.list_display)
        for index, field_name in enumerate(list_display):
            field = getattr(self.model, field_name, None)
            if hasattr(field, "related"):
                list_display.remove(field_name)
                list_display.insert(
                    index, self.display_add_link(request, field.related))
        list_display.append(delete)
        return list_display

    def remove(self, obj, **kwargs):
        """
        This will not work without a custom get_list_display like above in
        this class.
        """
        request = kwargs.pop('request')
        if self.has_delete_permission(request, obj):
            info = obj._meta.app_label, obj._meta.model_name
            delete_url = reverse('admin:%s_%s_delete' % info,
                                 args=(quote(obj.pk),
                                       quote(self.prescription.pk)))
            return ('<div><a href="%s" class="inline-deletelink"'
                    'title="Delete"></a></div>') % delete_url
        else:
            return ""

    def display_add_link(self, request, related):
        def inner(obj):
            opts = related.model._meta
            kwargs = {related.field.name: obj}
            count = related.model._default_manager.filter(**kwargs).count()
            context = {
                'related': related,
                'obj': obj,
                'opts': opts,
                'count': count
            }
            return render_to_string(
                'admin/change_list_links.html',
                RequestContext(request, context)
            )
        inner.allow_tags = True
        inner.short_description = related.opts.verbose_name_plural.title()
        return inner

    # def response_add(self, request, obj, post_url_continue=None):
    #     redirect = request.GET['next'] if "next" in request.GET else None
    #     if redirect is None:
    #         opts = obj._meta
    #         pk_value = obj._get_pk_val()            
    #         redirect = reverse('admin:%s_%s_change' %
    #                            (opts.app_label, opts.model_name),
    #                            args=(pk_value, self.prescription.pk),
    #                            current_app=self.admin_site.name)
    #     return super(PrescriptionMixin, self).response_add(
    #         request, obj, post_url_continue=redirect)

    def response_add(self, request, obj, post_url_continue=None):
        redirect = request.GET['next'] if "next" in request.GET else None
        if redirect:
            return HttpResponseRedirect(request.GET['next'])
        opts = obj._meta
        msg_dict = {'name': force_text(opts.verbose_name),
                    'obj': force_text(obj)}
        if redirect is None:
            # opts = obj._meta
            pk_value = obj._get_pk_val()            
            redirect = reverse('admin:%s_%s_change' %
                               (opts.app_label, opts.model_name),
                               args=(pk_value, self.prescription.pk),
                               current_app=self.admin_site.name)
        if '_save' in request.POST:
            msg = ('The %(name)s "%(obj)s" was added successfully.' % msg_dict)
            self.message_user(request, msg, messages.SUCCESS)
            return self.response_post_save_add(request, obj)
        return super(PrescriptionMixin, self).response_add(
            request, obj, post_url_continue=redirect)

    def response_change(self, request, obj):
        opts = self.model._meta
        pk_value = obj._get_pk_val()
        msg_dict = {'name': force_text(opts.verbose_name),
                    'obj': force_text(obj)}
        if "_saveasnew" in request.POST:
            msg = ('The %(name)s "%(obj)s" was added successfully. You may ' +
                   ' edit it again below.' % msg_dict)
            self.message_user(request, msg)
            return HttpResponseRedirect(reverse('admin:%s_%s_change' %
                                        (opts.app_label, opts.model_name),
                                        args=(pk_value, self.prescription.pk),
                                        current_app=self.admin_site.name))
        elif "_addanother" in request.POST:
            msg = ('The %(name)s "%(obj)s" was changed successfully. You may' +
                   ' add another %(name)s below.' % msg_dict)
            self.message_user(request, msg)
            return HttpResponseRedirect(reverse('admin:%s_%s_add' %
                                        (opts.app_label, opts.model_name),
                                        args=(self.prescription.pk,),
                                        current_app=self.admin_site.name))
        return super(PrescriptionMixin, self).response_change(request, obj)

    def response_post_save_add(self, request, obj):
        """
        Figure out where to redirect after the 'Save' button has been pressed
        when adding a new object.
        """
        opts = self.model._meta

        if "next" in request.GET:
            return HttpResponseRedirect(request.GET['next'])

        if self.has_change_permission(request, None):
            post_url = reverse('admin:%s_%s_changelist' %
                               (opts.app_label, opts.model_name),
                               args=(quote(self.prescription.pk),),
                               current_app=self.admin_site.name)
        else:
            post_url = reverse('admin:index',
                               current_app=self.admin_site.name)

        return HttpResponseRedirect(post_url)

    def response_post_save_change(self, request, obj):
        """
        Figure out where to redirect after the 'Save' button has been pressed
        when editing an existing object.
        """
        opts = self.model._meta

        if "next" in request.GET:
            return HttpResponseRedirect(request.GET['next'])

        if self.has_change_permission(request, None):
            post_url = reverse('admin:%s_%s_changelist' %
                               (opts.app_label, opts.model_name),
                               args=(quote(self.prescription.pk),),
                               current_app=self.admin_site.name)
        else:
            post_url = reverse('admin:index',
                               current_app=self.admin_site.name)

        return HttpResponseRedirect(post_url)


class SavePrescriptionMixin(object):
    exclude = ('prescription',)
    can_delete = False
    lock_after = 'endorsement'

    def get_list_editable(self, request):
        """
        Restrict editing when the ePFP reaches certain stages of completion.
        If the user is part of the ePFP Application Administrator, allow them to edit
        anyway.
        """
        current = self.prescription
        if request.user.has_perm('prescription.can_admin') or self.lock_after == 'never':
            return self.list_editable

        if (self.lock_after == 'endorsement' and not current.is_draft) or (self.lock_after == 'closure' and current.is_closed):
            return ('id',)
        else:
            return self.list_editable

    def save_model(self, request, obj, form, change):
        """
        Save the model and assign delete permissions to particular objects.
        Also save user to object if an audit object
        """
        #import ipdb; ipdb.set_trace()
        try:
            obj.prescription = self.prescription
        except AttributeError:
            pass
        if not obj.pk:
            obj.creator = request.user
        obj.modifier = request.user

        obj.save()

        # If can_delete is set, allow the user to delete this object.
        if self.can_delete:
            opts = self.opts
            group = Group.objects.get(name='Users')
            perm = get_permission_codename('delete', opts)
            assign_perm("%s.%s" % (opts.app_label, perm), group, obj)


class ObjectiveAdmin(PrescriptionMixin, SavePrescriptionMixin,
                     BaseAdmin):
    list_display = ("objectives",)
    list_editable = ("objectives",)
    list_empty_form = True
    list_display_links = (None,)
    actions = None
    can_delete = True
    lock_after = "endorsement"


class RegionalObjectiveAdmin(admin.ModelAdmin):
    list_display = ("region", "impact", "fma_names", "objectives",)
    list_filter = ("region", "impact")
    actions = None

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Override to default the region to the user's profile region.
        """
        if db_field.name == 'region':
            if request.user.profile.region is not None:
                kwargs['initial'] = request.user.profile.region.pk
            return db_field.formfield(**kwargs)

        return super(RegionalObjectiveAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.creator = request.user
        obj.modifier = request.user
        obj.save()

class SuccessCriteriaAdmin(PrescriptionMixin, SavePrescriptionMixin,
                           BaseAdmin):
    list_display = ("criteria",)
    list_editable = ("criteria",)
    list_empty_form = True
    list_display_links = (None,)
    actions = None
    can_delete = True
    lock_after = 'endorsement'


class PriorityJustificationAdmin(PrescriptionMixin, SavePrescriptionMixin,
                                 BaseAdmin):
    list_display = ("purpose", "criteria_display", "rationale", "priority")
    list_editable = ("rationale", "priority")
    list_display_links = (None,)
    list_empty_form = False
    actions = None

    def criteria_display(self, obj):
        """
        Fix up the display of the criteria so that it looks a bit nicer.
        """
        return markdownify(obj.criteria)
    criteria_display.short_description = "Criteria"

    def queryset(self, request):
        qs = super(PriorityJustificationAdmin, self).queryset(request)
        return qs.filter(relevant=True)

    def changelist_view(self, request, prescription_id, extra_context=None):
        current = self.get_prescription(request, unquote(prescription_id))

        form = PrescriptionPriorityForm(request.POST or None, instance=current)

        if request.method == "POST" and current.is_draft:
            if form.is_valid() and form.has_changed():
                form.save()
                message = "Updated overall priority and rationale"
                self.message_user(request, message)

        context = {'priority_form': form}
        context.update(extra_context or {})

        return super(PriorityJustificationAdmin, self).changelist_view(
            request, prescription_id, extra_context=context)


class BriefingChecklistAdmin(PrescriptionMixin, SavePrescriptionMixin,
                             BaseAdmin):
    list_display = ("title_column", "notes")
    list_group_by = "smeac_category"
    list_editable = ("notes",)
    actions = None
    form = BriefingChecklistForm
    list_display_links = (None,)

    def get_action(self, obj):
        if obj.action:
            return obj.action.description
        else:
            return ""
    get_action.short_description = "Action"

    def smeac_category(self, obj):
        return obj.smeac.category

    def title_column(self, obj):
        return obj.title
    title_column.short_description = "Topic"

    def get_readonly_fields(self, request, obj=None):
        if self.prescription.is_closed:
            return self.list_editable
        else:
            return self.readonly_fields
