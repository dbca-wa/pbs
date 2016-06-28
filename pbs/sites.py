from __future__ import (unicode_literals, absolute_import)

from functools import update_wrapper

from django.conf import settings
from django.contrib.admin import ModelAdmin
from django.contrib.admin.validation import ImproperlyConfigured
from django.contrib.auth import REDIRECT_FIELD_NAME, login
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin, GroupAdmin
from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import resolve_url
from django.template import add_to_builtins
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters

from pbs.document.admin import DocumentAdmin
from pbs.document.models import Document
from pbs.forms import (UserForm, ProfileForm, PbsAdminAuthenticationForm,
    EndorseAuthoriseSummaryForm, BurnStateSummaryForm)
from pbs.implementation.admin import (BurningPrescriptionAdmin,
                                      EdgingPlanAdmin, LightingSequenceAdmin,
                                      ExclusionAreaAdmin, RoadSegmentAdmin,
                                      TrailSegmentAdmin, SignInspectionAdmin,
                                      OperationalOverviewAdmin)
from pbs.implementation.models import (RoadSegment, TrailSegment,
                                       SignInspection, TrafficControlDiagram,
                                       BurningPrescription, EdgingPlan,
                                       LightingSequence, ExclusionArea,
                                       OperationalOverview)
from pbs.models import Profile
from pbs.prescription.admin import (PrescriptionAdmin, ObjectiveAdmin,
                                    RegionalObjectiveAdmin,
                                    SuccessCriteriaAdmin,
                                    PriorityJustificationAdmin,
                                    BriefingChecklistAdmin)
from pbs.prescription.models import (Prescription, RegionalObjective,
                                     Objective, PriorityJustification,
                                     SuccessCriteria, BriefingChecklist)
from pbs.report.admin import (AreaAchievementAdmin, ProposedActionAdmin,
                              EvaluationAdmin, PostBurnChecklistAdmin)
from pbs.report.models import (AreaAchievement, Evaluation, ProposedAction,
                               PostBurnChecklist)
from pbs.risk.admin import (RegisterAdmin, ContextAdmin, ComplexityAdmin,
                            ContingencyAdmin, ActionAdmin, TreatmentAdmin,
                            RiskAdmin, ContextRelevantActionAdmin,
                            ContingencyActionAdmin, ContingencyNotificationAdmin)
from pbs.risk.models import (Risk, RiskCategory, Context, Action,
                             Register, Treatment, Contingency, Complexity,
                             ContextRelevantAction, ContingencyAction,
                             ContingencyNotification)
from pbs.stakeholder.admin import (CriticalStakeholderAdmin,
                                   PublicContactAdmin, NotificationAdmin)
from pbs.stakeholder.models import (CriticalStakeholder, PublicContact,
                                    Notification)
from pbs.review.models import (BurnState, PrescribedBurn)
from pbs.review.admin import (BurnStateAdmin, PrescribedBurnAdmin, FireAdmin)

from swingers.sauth.sites import AuditSite

import logging
import unicodecsv
import datetime
from dateutil import tz
import re
import itertools


log = logging.getLogger(__name__)

# Hard coded regions for CVS reporting
forest_regions = ['Swan', 'South West', 'Warren']


class UserAdmin(AuthUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_active')
    actions = None
    form = UserForm
    fieldsets = (
        (None, {'fields': ('username', 'email', ('first_name', 'last_name'),
                           'is_active', 'groups')}),
    )
    list_filter = ("is_active", "groups")


class PrescriptionSite(AuditSite):
    def has_permission(self, request):
        return request.user.is_active

    def get_urls(self):
        """
        Add a view to clear the current prescription from the session
        """
        from django.conf.urls import patterns, url

        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        urlpatterns = patterns(
            '',
            url(r'^administration/$',
                wrap(self.site_admin),
                name='site_admin'),
            url(r'^profile/$',
                wrap(self.profile),
                name='profile'),
            url(r'^endorse-authorise/$',
                wrap(self.endorse_authorise_summary),
                name='endorse_authorise_summary'),
#            url(r'^daily-burn-program/$',
#                wrap(self.daily_burn_program),
#                name='daily_burn_program'),
#            url(r'^daily-burn-program/add$',
#                wrap(self.daily_burn_program_add),
#                name='daily_burn_program_add'),

            url(r'^endorse-authorise/export_csv/$',
                wrap(self.export_to_csv),
                name='endorse_authorise_exportcsv'),
        )

        return urlpatterns + super(PrescriptionSite, self).get_urls()

    def index(self, request):
        try:
            profile = request.user.profile
        except:
            profile = None

        url = reverse('admin:prescription_prescription_changelist')
        if profile is not None and profile.region:
            url += '?region__id__exact=%s' % profile.region.id
        return HttpResponseRedirect(url)

    def password_change(self, request):
        if request.user.profile.is_fpc_user():
            return super(PrescriptionSite, self).password_change(request)
        else:
            return HttpResponseForbidden("You are not an FPC user. Only FPC "
                                         "users can change their password "
                                         "via this interface.")

    def register(self, model, admin_class=None, **options):
        try:
            super(PrescriptionSite, self).register(
                model, admin_class, **options)
        except ImproperlyConfigured:
            self._registry[model] = admin_class(model, self)

    @method_decorator(sensitive_post_parameters())
    @never_cache
    def login(self, request, redirect_field_name=REDIRECT_FIELD_NAME,
              authentication_form=PbsAdminAuthenticationForm,
              extra_context=None):
        """
        Displays the login form and handles the login action.
        """
        redirect_to = request.REQUEST.get(redirect_field_name, '')

        if request.method == 'POST':
            form = authentication_form(request, data=request.POST)
            if form.is_valid():

                # Ensure the user-originating redirection url is safe.
                if not is_safe_url(url=redirect_to, host=request.get_host()):
                    redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

                # If this is the user's first login, redirect them to
                # edit their profile.
                user = form.get_user()
                if user.last_login == user.date_joined:
                    request.session['first_login'] = True
                    redirect_to = reverse('admin:profile')

                # Okay, security check complete. Log the user in.
                login(request, user)

                return HttpResponseRedirect(redirect_to)
        else:
            form = authentication_form(request)

        current_site = get_current_site(request)

        # We won't need this in Django 1.6
        request.session.set_test_cookie()

        context = {
            'title': _('Log in'),
            'app_path': request.get_full_path(),
            'form': form,
            redirect_field_name: request.get_full_path(),
            'site': current_site,
            'site_name': current_site.name,
        }
        if extra_context is not None:
            context.update(extra_context)
        return TemplateResponse(request,
                                self.login_template or 'admin/login.html',
                                context, current_app=self.name)

    @never_cache
    def logout(self, request, extra_context=None):
        from django.contrib.auth.views import logout
        return logout(request, reverse('admin:index', current_app=self.name))

    def site_admin(self, request, extra_context=None):
        context = {}
        context.update(extra_context or {})
        return TemplateResponse(request, "admin/site_admin.html", context,
                                current_app=self.name)

    def profile(self, request):
        profile = request.user.get_profile()
        if request.method == 'POST':
            form = ProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('admin:index',
                                                    current_app=self.name))
        else:
            form = ProfileForm(instance=profile)
        context = {
            'title': _('Edit profile'),
            'form': form
        }
        return TemplateResponse(request, "admin/profile.html", context,
                                current_app=self.name)

    def endorse_authorise_summary(self, request, extra_context=None):
        """
        Display summaries of prescriptions, approvals and ignitions.

        DEV:

        """
        form = EndorseAuthoriseSummaryForm(request.GET)

        report_set = {'summary', 'approvals', 'ignitions'}
        report = request.GET.get('report', 'summary')
        if report not in report_set:
            report = 'summary'

        export_csv = True if request.GET.get('Export_CSV') == 'export_csv' else False

        if request.GET.get('fromDate'):
            fromDate = request.GET.get('fromDate')
            fromDate = datetime.datetime.strptime(fromDate, '%d-%m-%Y').date()
        else:
            # default - beginning of financial year
            yr = datetime.date.today().year
            fromDate = datetime.date(yr, 7, 1)

        if request.GET.get('toDate'):
            toDate = request.GET.get('toDate')
            toDate = datetime.datetime.strptime(toDate, '%d-%m-%Y').date()
        else:
            toDate = datetime.date.today()

        burns = []
        if report == 'summary':
            title = _("Endorsements summary")
            queryset = Prescription.objects.filter(
                endorsement_status=Prescription.ENDORSEMENT_SUBMITTED)
        elif report == 'approvals':
            title = _("Approvals summary")
            queryset = Prescription.objects.filter(
                approval_status=Prescription.APPROVAL_SUBMITTED)
        elif report == 'ignitions':
            title = _("Ignitions summary")
            queryset = None
            burns = self.get_burns(fromDate, toDate)
        else:
            raise ValueError("Report {} must be in {}".format(report, report_set))

        if export_csv:
            return self.export_to_csv(request, fromDate, toDate, burns)
        if queryset:
            queryset.prefetch_related('endorsing_roles')

        if form.is_valid():
            region = form.cleaned_data.get('region', None)
            district = form.cleaned_data.get('district', None)

            if region:
                queryset = queryset.filter(region=region)

            if district:
                queryset = queryset.filter(district=district)

        context = {
            'title': title,
            'prescriptions': queryset,
            'form': form,
            'report': report,
            'burns': burns,
            'fromDate': fromDate,
            'toDate': toDate,
        }
        context.update(extra_context or {})
        return TemplateResponse(request, "admin/endorse_authorise_summary.html", context,
                                current_app=self.name)

    def get_burns(self, fromDate, toDate):

          query_list = []

          for p in Prescription.objects.all():
              for a in p.areaachievement_set.all():
                  region_type = 'Forest' if str(p.region) in forest_regions else 'Non-forest'
                  if a.ignition >= fromDate and a.ignition <= toDate and p.ignition_status != p.IGNITION_COMPLETE:
                      query_list.append([int(p.id), str(p.burn_id), str(p.region), str(p.district),
                                         'commenced', str(a.ignition), float(a.area_treated), region_type])

                  elif a.ignition >= fromDate and a.ignition <= toDate and p.ignition_status == p.IGNITION_COMPLETE:
                      query_list.append([int(p.id), str(p.burn_id), str(p.region), str(p.district),
                                        'completed', str(a.ignition), float(a.area_treated), region_type])

          result = []
          # collate the results
          sub_results = self.collate_results(query_list, 'Forest')
          result += sub_results

          sub_results = self.collate_results(query_list, 'Non-forest')
          result += sub_results
          # don't double count Sub-Totals in Total, and ignore blank rows
          total_completed = sum([ll[1] for ll in result if len(ll)>0 and re.search('Total', ll[0]) ])
          total_commenced = sum([ll[2] for ll in result if len(ll)>0 and re.search('Total', ll[0]) ])
          total_area      = sum([ll[3] for ll in result if len(ll)>0 and re.search('Total', ll[0]) ])
          result.append(['Total', total_completed, total_commenced, total_area])

          return result

    def collate_results(self, query_list, region_type):
        results = []
        regions = set([ll[2] for ll in query_list if region_type in ll]) # unique list of region's
        for region in regions:
            # count of completed/commenced burns and sum(area) for given region
            completed_burns = len(set([ll[1] for ll in query_list if (region in ll and 'completed' in ll)]))
            commenced_burns = len(set([ll[1] for ll in query_list if (region in ll and 'commenced' in ll)]))
            area = sum([ll[6] for ll in query_list if (region in ll)])

            results.append([region, completed_burns, commenced_burns, area])

        total_completed = sum([ll[1] for ll in results ])
        total_commenced = sum([ll[2] for ll in results ])
        total_area      = sum([ll[3] for ll in results ])
        results.append(['{} Sub-Total'.format(region_type), total_completed, total_commenced, total_area])
        results.append([]*4)

        return results

    def export_to_csv(self, request, fromDate, toDate, burns=None):
        local_zone = tz.tzlocal()
        query_list = []
        id_list = []

        for p in Prescription.objects.all():
            for a in p.areaachievement_set.all():

                if a.ignition >= fromDate and a.ignition <= toDate:

                    p_id = p.id
                    p_count = 0 if p_id in id_list else 1 # get a unique count of prescription
                    id_list.append(p_id)
                    region = str(p.region)
                    region_type = 'Forest' if region in forest_regions else 'Non-forest'
                    district = str(p.district)
                    burn_name = str(p.name)
                    burn_id = str(p.burn_id)
                    date_updated = str(p.modified.astimezone(local_zone).strftime('%d/%m/%Y %H:%M:%S'))
                    ignition_status = p.get_ignition_status_display()
                    burn_closed = "Yes" if p.status == p.STATUS_CLOSED else "No"
                    burn_complexity = p.maximum_complexity
                    burn_priority = p.get_priority_display()
                    burn_risk = p.maximum_risk
                    contentious = "Yes" if p.contentious else "No"
                    year = p.planned_year
                    season = p.financial_year
                    actual_ignitions = ('"%s"' % ",".join(
                      ",".join('{0}:{1}'.format(x.ignition.strftime('%d/%m/%Y'),
                                                ignition_type)
                              for ignition_type
                              in (x.ignition_types.all() or ("Unset",))
                              )
                      for x in p.areaachievement_set.order_by('ignition'))
                    )
                    planned_burn_area = p.area
                    total_treatment_area = p.total_treatment_area
                    burnt_area_estimate = p.total_burnt_area_estimate
                    length_of_edging = p.total_edging_length
                    depth_of_edging = p.total_edging_depth
                    shires = '"%s"' % ",".join(x.name for x in p.shires.all())
                    purposes = '"%s"' % ",".join(x.name for x in p.purposes.all())
                    allocations = p.allocations
                    tenures = '"%s"' % ",".join(x.name for x in p.tenures.all())
                    #escape_dates = ", ".join([datetime.strftime(x.date_escaped, '%d/%m/%Y') for x in a.filter(date_escaped__isnull=False).order_by('ignition')])
                    #dpaw_fire_nums = '"%s"' % ",".join(x.dpaw_fire_no for x in a.exclude(dpaw_fire_no__isnull=True).exclude(dpaw_fire_no__exact='').order_by('ignition'))
                    #dfes_fire_nums = '"%s"' % ",".join(x.dfes_fire_no for x in a.exclude(dfes_fire_no__isnull=True).exclude(dfes_fire_no__exact='').order_by('ignition'))
                    success_criterias = '"%s"' % ",".join(x.criteria for x in p.successcriteria_set.all().order_by('id'))

                    if p.ignition_status != p.IGNITION_COMPLETE:

                        query_list.append([p_id, p_count, burn_id, burn_name, region, district,
                            'commenced', str(a.ignition), float(a.area_treated), region_type,
                            date_updated, ignition_status, burn_closed,
                            burn_complexity, burn_priority, burn_risk, contentious,
                            year, season, actual_ignitions, planned_burn_area,
                            total_treatment_area, burnt_area_estimate,
                            length_of_edging, depth_of_edging, shires, purposes,
                            allocations, tenures,
                            #escape_dates, dpaw_fire_nums, dfes_fire_nums,.
                            success_criterias])

                    elif p.ignition_status == p.IGNITION_COMPLETE:

                        query_list.append([p_id, p_count, burn_id, burn_name, region, district,
                            'completed', str(a.ignition), float(a.area_treated), region_type,
                            date_updated, ignition_status, burn_closed,
                            burn_complexity, burn_priority, burn_risk, contentious,
                            year, season, actual_ignitions, planned_burn_area,
                            total_treatment_area, burnt_area_estimate,
                            length_of_edging, depth_of_edging, shires, purposes,
                            allocations, tenures,
                            #escape_dates, dpaw_fire_nums, dfes_fire_nums,.
                            success_criterias])

        filename = 'export_burn_{0}-{1}.csv'.format(fromDate.strftime('%d%b%Y'), toDate.strftime('%d%b%Y'))
        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
        writer = unicodecsv.writer(response, quoting=unicodecsv.QUOTE_ALL)

        writer.writerow(['Prescription_ID', 'Prescription Count', 'Burn ID', 'Name of Burn', 'Region', 'District',
            'Status', 'Ignition Date', 'Burn area (ha)', 'Region Type',
            'Date Updated', 'Ignition Status', 'Burn Closed', 'Burn Complexity',
            'Burn Priority', 'Burn Risk', 'Contentious', 'Year', 'Season',
            'Actual Ignition Type', 'Planned Burn Area', 'Total Area Where Treatment Is Complete',
            'Total Treatment Activity', 'Length of Edging/Perimeter', 'Depth of Edging',
            'Shire', 'Burn Purpose/s', 'Program Allocations', 'Land Tenure', 'Success Criteria'])

        for burn in query_list:
            writer.writerow([unicode(s).encode("utf-8") for s in burn])

        return response
    export_to_csv.short_description = ugettext_lazy("Export to CSV")


site = PrescriptionSite()

site.register(User, UserAdmin)
site.register(Group, GroupAdmin)

site.register(Prescription, PrescriptionAdmin)
site.register(RegionalObjective, RegionalObjectiveAdmin)
site.register(Objective, ObjectiveAdmin)
site.register(SuccessCriteria, SuccessCriteriaAdmin)
site.register(PriorityJustification, PriorityJustificationAdmin)

site.register(RiskCategory, ModelAdmin)
site.register(Register, RegisterAdmin)
site.register(Risk, RiskAdmin)
site.register(Treatment, TreatmentAdmin)
site.register(Context, ContextAdmin)
site.register(ContextRelevantAction, ContextRelevantActionAdmin)
site.register(CriticalStakeholder, CriticalStakeholderAdmin)
site.register(PublicContact, PublicContactAdmin)
site.register(Notification, NotificationAdmin)
site.register(Complexity, ComplexityAdmin)
site.register(Contingency, ContingencyAdmin)
site.register(ContingencyAction, ContingencyActionAdmin)
site.register(ContingencyNotification, ContingencyNotificationAdmin)
site.register(Profile, ModelAdmin)
site.register(Action, ActionAdmin)
site.register(AreaAchievement, AreaAchievementAdmin)

site.register(RoadSegment, RoadSegmentAdmin)
site.register(TrailSegment, TrailSegmentAdmin)
site.register(SignInspection, SignInspectionAdmin)
site.register(BurningPrescription, BurningPrescriptionAdmin)
site.register(EdgingPlan, EdgingPlanAdmin)
site.register(LightingSequence, LightingSequenceAdmin)
site.register(BriefingChecklist, BriefingChecklistAdmin)
site.register(ExclusionArea, ExclusionAreaAdmin)
site.register(Document, DocumentAdmin)
site.register(TrafficControlDiagram, ModelAdmin)
site.register(ProposedAction, ProposedActionAdmin)
site.register(Evaluation, EvaluationAdmin)
site.register(PostBurnChecklist, PostBurnChecklistAdmin)
site.register(OperationalOverview, OperationalOverviewAdmin)

site.register(BurnState, BurnStateAdmin)
site.register(PrescribedBurn, PrescribedBurnAdmin)

# add our own texify filter to the builtins here.
add_to_builtins('pbs.prescription.templatetags.texify')
