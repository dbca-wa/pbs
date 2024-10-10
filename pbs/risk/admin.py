from __future__ import unicode_literals
from functools import update_wrapper, partial
from guardian.shortcuts import assign_perm

from django.contrib.admin import SimpleListFilter
from django.contrib.admin.utils import unquote, quote
from django.contrib.auth.models import Group
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from pbs.admin import BaseAdmin, get_permission_codename
from pbs.prescription.models import Prescription
from pbs.prescription.admin import PrescriptionMixin, SavePrescriptionMixin
from pbs.prescription.templatetags.prescription_tags import risk_display
from pbs.risk.forms import RiskForm, TreatmentForm, TreatmentCompleteForm
from pbs.risk.models import (
    Action, ContextRelevantAction, Contingency, ContingencyAction,
    ContingencyNotification, Treatment, Register, Risk)

import json
import logging

log = logging.getLogger(__name__)


class RiskRegisterFilter(SimpleListFilter):
    """
    An annoying hack to get around not being able to pass custom GET
    variables around on a changelist. They get passed to filters and
    break the changelist if no filter classes are found to handle the
    variable.
    """
    title = _('section')
    parameter_name = 'section'

    def lookups(self, request, model_admin):
        return (
            ('draft', _('Initial risk assessment')),
            ('final', _('Treatments & final risk assessment')),
        )

    def queryset(self, request, queryset):
        return queryset


class RegisterAdmin(PrescriptionMixin, SavePrescriptionMixin,
                    BaseAdmin):
    prescription_filter_field = "prescription"
    list_display = ("description", "draft_consequence",
                     "draft_likelihood", "alarp", "final_consequence",
                     "final_likelihood")
    list_editable = ("description", "draft_consequence",
                     "draft_likelihood", "alarp", "final_consequence",
                     "final_likelihood")
    list_per_page = 150
    list_display_links = (None, )
    list_filter = (RiskRegisterFilter,)
    list_empty_form = True
    actions = None
    can_delete = True
    #lock_after = 'endorsement'
    lock_after = 'approval'

    def queryset(self, request):
        qs = super(RegisterAdmin, self).queryset(request)
        return qs.prefetch_related("treatment_set")

    def get_list_display(self, request):
        delete = partial(self.remove, request=request)
        delete.short_description = ""
        delete.allow_tags = True
        section = request.GET.get("section", "draft")
        if section == 'draft':
            return ("description",
                    "draft_consequence", "draft_likelihood",
                    "changelist_draft_risk_level", "alarp", delete)
        elif section == "final":
            return ("description", "all_treatments",
                    "final_consequence", "final_likelihood",
                    "changelist_final_risk_level", delete)

    def get_list_editable(self, request):
        """
        Only allow editing certain fields on the different pages.
        """
        section = request.GET.get("section", "draft")
        if section == 'draft':
            return ("description", "draft_consequence",
                    "draft_likelihood", "alarp")
        elif section == "final":
            return ("final_consequence", "final_likelihood")
        return super(RegisterAdmin, self).get_list_editable(request)

    def get_readonly_fields(self, request, obj):
        """
        If the ePFP has not had all part A (except risk register) complete, all
        of part B complete and post-burn actions of part C complete, do not
        allow the user to edit any risk register items.

        Similarly, if a PSoR has been marked ALARP, don't allow the user to
        edit the final likelihood or final consequences.
        """
        current = self.prescription
        if not current.can_corporate_approve:
            return self.list_editable
        else:
            return super(RegisterAdmin, self).get_readonly_fields(request, obj)

    def get_changelist_formset(self, request, **kwargs):
        FormSet = super(RegisterAdmin, self).get_changelist_formset(request)

        section = request.GET.get("section", "draft")
        if section == 'draft':
            class DraftFormSet(FormSet):
                def clean(self):
                    if any(self.errors):
                        return
            return DraftFormSet
        else:
            return FormSet

    def get_changelist_form(self, request, **kwargs):
        """
        If a PSoR has been marked ALARP, don't allow the user to
        edit the final likelihood or final consequences.
        """
        Form = super(RegisterAdmin, self).get_changelist_form(request,
                                                              **kwargs)
        section = request.GET.get("section", "draft")
        if section.lower() == "final":
            # custom processing for the ALARP-set fields -
            # lock the final_consequence and final_likelihood
            class FinalForm(Form):
                def __init__(self, *args, **kwargs):
                    super(FinalForm, self).__init__(*args, **kwargs)
                    if (kwargs.get('instance') is not None and
                            kwargs['instance'].alarp):
                        self.fields.pop('final_consequence', None)
                        self.fields.pop('final_likelihood', None)

            return FinalForm
        else:
            return Form

    def all_treatments(self, obj):
        if obj.treatment_set.count() > 0:
            output = '<ul>'
            for treatment in obj.treatment_set.all():
                if treatment.complete:
                    status_class = ' class="text-success"'
                    status_icon = '<i class="icon-ok"></i> '
                else:
                    status_class = ''
                    status_icon = ''

                treatment_url = reverse('admin:risk_treatment_change',
                                        args=(quote(treatment.pk),
                                              quote(self.prescription.pk)))
                output += '<li%s><a href="%s">%s%s (%s)</a></li>' % (
                    status_class, treatment_url, status_icon,
                    treatment.description, treatment.location)
            output += '</ul>'
        else:
            if obj.alarp:
                output = 'No treatments required'
            else:
                output = 'No treatments'

        if not obj.alarp and self.prescription.is_draft:
            url = reverse('admin:risk_treatment_add',
                          args=(quote(self.prescription.pk),),
                          current_app=self.admin_site.name)
            url += '?register=%d' % obj.pk
            output += (
                '<br><a id="add_treatment_%(pk)s" '
                'onclick="return showAddAnotherPopup(this);" '
                'class="add-another" href="%(url)s">'
                '<i class="icon-plus"></i> Add a treatment</a>'
            ) % {
                'pk': obj.pk,
                'url': url,
            }
        return output
    all_treatments.short_description = "Treatments"
    all_treatments.allow_tags = True

    def changelist_final_risk_level(self, obj):
        """
        Callable to display final_risk_level using colour based styling
        """
        return risk_display(obj)
    changelist_final_risk_level.short_description = 'Final ePFP Risk Level'
    changelist_final_risk_level.admin_order_field = 'final_risk_level'
    changelist_final_risk_level.required = True

    def changelist_draft_risk_level(self, obj):
        """
        Callable to display draft_risk_level using colour based styling
        """
        return risk_display(obj, draft=True)
    changelist_draft_risk_level.short_description = 'Draft ePFP Risk Level'
    changelist_draft_risk_level.admin_order_field = 'draft_risk_level'
    changelist_draft_risk_level.required = True


class ContextPestleFilter(SimpleListFilter):
    title = _('PESTLE')
    parameter_name = 'pestle'

    def lookups(self, request, model_admin):
        return (
            ('p', _('Political')),
            ('e', _('Economic')),
            ('s', _('Social')),
            ('t', _('Technical')),
            ('l', _('Legal')),
            ('en', _('Environmental')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'p':
            return queryset.filter(categories__name='Political')
        elif self.value() == 'e':
            return queryset.filter(categories__name='Economic')
        elif self.value() == 's':
            return queryset.filter(categories__name='Social')
        elif self.value() == 't':
            return queryset.filter(categories__name='Technical')
        elif self.value() == 'l':
            return queryset.filter(categories__name='Legal')
        elif self.value() == 'en':
            return queryset.filter(categories__name='Environmental')


class ContextAdmin(PrescriptionMixin, SavePrescriptionMixin,
                   BaseAdmin):
    list_display = ("statement",)
    list_display_links = (None,)
    list_editable = ("statement",)
    actions = None

    def get_readonly_fields(self, request, obj=None):
        """
        If the ePFP can not yet be submitted for corporate approval,
        do not allow the user to edit any contexts.
        """
        current = self.prescription
        if not (current.is_draft or current.can_corporate_approve):
            return self.list_editable
        return super(ContextAdmin, self).get_readonly_fields(request, obj)

    def changelist_view(self, request, prescription_id, extra_context=None):
        context = extra_context or {}
        context.update({
            'relevant_actions': ContextRelevantAction.objects.filter(action__risk__prescription__id=unquote(prescription_id)
                                                                     ).select_related('action', 'action__risk')})
        return super(ContextAdmin, self).changelist_view(request, prescription_id, context)


class ContextRelevantActionAdmin(PrescriptionMixin, SavePrescriptionMixin,
                                 BaseAdmin):
    def change_view(self, request, object_id, prescription_id,
                    extra_context=None):
        obj = self.get_object(request, unquote(object_id))

        if (obj is None or not self.has_change_permission(request, obj) or
                not request.is_ajax() or request.method != "POST"):
            return super(ContextRelevantActionAdmin, self).change_view(
                request, object_id)
        else:
            ModelForm = self.get_form(request, obj, exclude=('action',))
            form = ModelForm(request.POST, request.FILES, instance=obj)
            considered = obj.considered
            if form.is_valid():
                obj = self.save_form(request, form, change=True)
                self.save_model(request, obj, form, change=True)
            else:
                obj.considered = considered
            return HttpResponse(json.dumps({'considered': obj.considered}))


class ComplexityAdmin(PrescriptionMixin, SavePrescriptionMixin,
                      BaseAdmin):
    list_display = ("sub_factor", "rating", "rationale")
    list_display_links = ("sub_factor",)
    list_editable = ("rating", "rationale")
    list_filter = ("factor",)
    list_group_by = "factor"
    list_display_links = (None,)
    actions = None


class ContingencyActionAdmin(SavePrescriptionMixin, PrescriptionMixin, BaseAdmin):
    model = ContingencyAction
    fields = ("action",)
    actions = None

    def save_model(self, request, obj, form, change):
        """If a new object is being created, automatically associate
        it with the parent contigency.
        """
        if not change:
            object_id = unquote(request.GET.get('contingency'))

            try:
                obj.contingency = Contingency.objects.get(pk=object_id)
                #obj.contingency = Contingency.objects.get(pk=object_id)
                obj.creator = request.user
                obj.modifier = request.user
            except Contingency.DoesNotExist:
                return

        obj.save()

    def response_post_save_change(self, request, obj):
        """
        Override the redirect url after successful save of an existing
        ContingencyAction.
        """
        url = reverse('admin:risk_contingency_changelist',
                      args=[str(obj.contingency.prescription.pk)])
        return HttpResponseRedirect(url)


class ContingencyNotificationAdmin(SavePrescriptionMixin, PrescriptionMixin, BaseAdmin):
    model = ContingencyNotification
    fields = ('name', 'location', 'organisation', 'contact_number')
    actions = None

    def save_model(self, request, obj, form, change):
        """If a new object is being created, automatically associate
        it with the parent contigency.
        """
        if not change:
            object_id = unquote(request.GET.get('contingency'))

            try:
                obj.contingency = Contingency.objects.get(pk=object_id)
                #obj.prescription = self.prescription
                obj.creator = request.user
                obj.modifier = request.user
            except Contingency.DoesNotExist:
                return

        obj.save()

    def response_post_save_change(self, request, obj):
        """
        Override the redirect url after successful save of an existing
        ContingencyNotification.
        """
        url = reverse('admin:risk_contingency_changelist',
                      args=[str(obj.contingency.prescription.pk)])
        return HttpResponseRedirect(url)


class ContingencyAdmin(SavePrescriptionMixin, PrescriptionMixin, BaseAdmin):
    list_display = ("description", "trigger", "display_actions", "display_notifications")
    actions = None
    can_delete = True
    lock_after = 'endorsement'
    fields = ('description', 'trigger', 'actions_migrated', 'notifications_migrated')

    def changelist_view(self, request, prescription_id, extra_context=None):
        context = extra_context or {}
        current = Prescription.objects.get(pk=prescription_id)
        if not current.endorsement_status == current.ENDORSEMENT_DRAFT:
            context['hide_adminonly'] = 'hide adminonly'
        return super(ContingencyAdmin, self).changelist_view(request, prescription_id, context)

    def display_actions(self, obj):
        editable = obj.prescription.endorsement_status == obj.prescription.ENDORSEMENT_DRAFT
        output = ''
        # First, conditionally display old actions (only if actions_migrated
        # field is False).
        if not obj.actions_migrated and obj.action:
            output += '''<div class="alert alert-warning"><strong>Old actions list:</strong>
            <br>{}</div>'''.format(obj.action)
        # Then, display new actions.
        output += '<table><tbody>'
        for action in obj.actions.all():
            # For the delete link, we have to pass a 'next' parameter with the submit
            # in order to direct back to the contingency changlist.
            change_link = reverse('admin:risk_contingencyaction_change', args=(action.pk, self.prescription.pk), current_app=self.admin_site.name)
            delete_link = '<a href="{}?next={}" class="inline-deletelink" title="Delete"></a>'.format(
                reverse('admin:risk_contingencyaction_delete', args=(action.pk, self.prescription.pk), current_app=self.admin_site.name),
                reverse('admin:risk_contingency_changelist', args=[str(obj.prescription.pk)]))
            if editable:
                output += '<tr><td><a href="{}">{}</a></td><td>{}</td></tr>'.format(
                    change_link, action.action, delete_link)
            else:
                delete_link = delete_link.replace('class="', 'class="hide adminonly ')
                output += '<tr><td><a class="hide adminonly" href="{}">(Edit) </a>{}</td><td>{}</td></tr>'.format(
                    change_link, action.action, delete_link)
        output += "</tbody></table>"
        url = reverse('admin:risk_contingencyaction_add',
                      args=(obj.prescription.pk,),
                      current_app=self.admin_site.name)
        if editable:
            output += '''<a onclick="return showAddAnotherPopup(this);"
                class="add-another" href="{0}?contingency={1}">
                <i class="icon-plus"></i> Add an action</a>'''.format(url, obj.pk)
        # Include a distinctive class name in the "Add" link in order to conditionally
        # remove the stupid thing depending on the user's group membership.
        # We do this because we don't get access to the request object in this method.
        else:
            output += '''<a onclick="return showAddAnotherPopup(this);"
                class="add-another hide adminonly" href="{0}?contingency={1}">
                <i class="icon-plus"></i> Add an action</a>'''.format(url, obj.pk)
        return output
    display_actions.short_description = "Actions"
    display_actions.allow_tags = True

    def display_notifications(self, obj):
        """
        Return a table of notification contacts for this contingency.
        """
        editable = obj.prescription.endorsement_status == obj.prescription.ENDORSEMENT_DRAFT
        output = ''
        # First, conditionally display old notifications (only if notifications_migrated
        # field is False.
        if not obj.notifications_migrated and (obj.notify_name or obj.location or obj.organisation or obj.contact_number):
            output += '<div class="alert alert-warning"><strong>Old notifications list:</strong><br><table><tbody>'
            for item in obj.subitems:
                output += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
                    item.get("notify_name", ""), item.get("organisation", ""), item.get("location", ""), item.get("contact_number", ""))
            output += '</tbody></table></div>'
        # Then display new notifications.
        output += '<table><tbody>'
        for notification in obj.notifications.all():
            # For the delete link, we have to pass a 'next' parameter with the submit
            # in order to direct back to the contingency changlist.
            change_link = reverse('admin:risk_contingencynotification_change', args=(notification.pk, self.prescription.pk), current_app=self.admin_site.name)
            delete_link = '<a href="{}?next={}" class="inline-deletelink" title="Delete"></a>'.format(
                reverse('admin:risk_contingencynotification_delete', args=(notification.pk, self.prescription.pk), current_app=self.admin_site.name),
                reverse('admin:risk_contingency_changelist', args=[str(obj.prescription.pk)]))
            if editable:
                output += '<tr><td><a href="{}">{}</a></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
                    change_link, notification.name, notification.organisation,
                    notification.location, notification.contact_number,
                    delete_link)
            else:
                delete_link = delete_link.replace('class="', 'class="hide adminonly ')
                output += '<tr><td><a class="hide adminonly" href="{}">(Edit) </a>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
                    change_link, notification.name, notification.organisation,
                    notification.location, notification.contact_number,
                    delete_link)
        output += '</tbody></table>'
        url = reverse('admin:risk_contingencynotification_add',
                      args=(obj.prescription.pk,),
                      current_app=self.admin_site.name)
        if editable:
            output += '''<a onclick="return showAddAnotherPopup(this);"
                class="add-another" href="{0}?contingency={1}">
                <i class="icon-plus"></i> Add a notification</a>'''.format(url, obj.pk)
        # Include a distinctive class name in the "Add" link in order to conditionally
        # remove the stupid thing depending on the user's group membership.
        # We do this because we don't get access to the request object in this method.
        else:
            output += '''<a onclick="return showAddAnotherPopup(this);"
                class="add-another hide adminonly" href="{0}?contingency={1}">
                <i class="icon-plus"></i> Add a notification</a>'''.format(url, obj.pk)
        return output
    display_notifications.short_description = 'Notifications'
    display_notifications.allow_tags = True

    def save_model(self, request, obj, form, change=True):
        """First call save_model on this ContigencyAdmin object, then call
        save on the parent Prescription object.
        """
        super(ContingencyAdmin, self).save_model(request, obj, form, change)
        obj.prescription.save()

    def delete_model(self, request, obj):
        """First call delete_model on this ContigencyAdmin object, then call
        save on the parent Prescription object.
        """
        super(ContingencyAdmin, self).delete_model(request, obj)
        obj.prescription.save()


class ActionAdmin(SavePrescriptionMixin, PrescriptionMixin, BaseAdmin):
    """
    The action admin. Controls all aspects of prescription action planning
    including pre-burn, day of burn and post burn actions and the initial
    planning phase.
    """
    actions = None
    list_per_page = 150
    prescription_filter_field = "risk__prescription"
    list_group_by = 'risk_category'
    list_display_links = ('__str__',)
    list_display = ("relevant", "pre_burn", "day_of_burn", "post_burn",
                     "context_statement", "details",
                     "pre_burn_resolved", "pre_burn_explanation",
                     "pre_burn_completed", "pre_burn_completer",
                     "day_of_burn_situation", "day_of_burn_mission",
                     "day_of_burn_execution", "day_of_burn_administration",
                     "day_of_burn_command", "day_of_burn_safety",
                     "day_of_burn_completed", "day_of_burn_completer",
                     "post_burn_completed", "post_burn_completer",
                     "day_of_burn_include")
    # list_editable = ("relevant", "pre_burn", "day_of_burn", "post_burn",
    #                  "context_statement", "details", "pre_burn_responsible",
    #                  "pre_burn_resolved", "pre_burn_explanation",
    #                  "pre_burn_completed", "pre_burn_completer",
    #                  "day_of_burn_situation", "day_of_burn_mission",
    #                  "day_of_burn_execution", "day_of_burn_administration",
    #                  "day_of_burn_command", "day_of_burn_safety",
    #                  "day_of_burn_completed", "day_of_burn_completer",
    #                  "post_burn_completed", "post_burn_completer",
    #                  "day_of_burn_include")
    list_editable = ("relevant", "pre_burn", "day_of_burn", "post_burn",
                     "context_statement", "details",
                     "pre_burn_resolved", "pre_burn_explanation",
                     "pre_burn_completed", "pre_burn_completer",
                     "day_of_burn_situation", "day_of_burn_mission",
                     "day_of_burn_execution", "day_of_burn_administration",
                     "day_of_burn_command", "day_of_burn_safety",
                     "day_of_burn_completed", "day_of_burn_completer",
                     "post_burn_completed", "post_burn_completer",
                     "day_of_burn_include")

    fieldsets = (
        (None, {
            "fields": ('details', 'pre_burn', 'day_of_burn',
                       'post_burn', 'context_statement'),
        }),
    )

    can_delete = True
    lock_after = "closure"

    def queryset(self, request):
        qs = super(ActionAdmin, self).queryset(request)
        return qs.select_related("risk", "risk__category")

    def lookup_allowed(self, key, value):
        if key in ('relevant__exact', 'risk__category__id__exact'):
            return True
        return super(ActionAdmin, self).lookup_allowed(key, value)

    def get_list_display(self, request):
        """
        Return the changelist columns to display based on the request and the
        current prescription's status.
        """
        current = self.prescription

        delete = partial(self.remove, request=request)
        delete.short_description = ""
        delete.allow_tags = True

        if request.GET.get('pre_burn', False):
            # Pre-burn actions
            list_display = ("__str__", "details", "pre_burn_resolved",
                            "pre_burn_explanation")
            list_display += ("pre_burn_completed", "pre_burn_completer")
        elif request.GET.get('day_of_burn', False):
            # Day of burn actions
            list_display = ("__str__", "details", "day_of_burn_responsible",
                            "day_of_burn_include", "day_of_burn_situation",
                            "day_of_burn_mission", "day_of_burn_execution",
                            "day_of_burn_administration", "day_of_burn_command",
                            "day_of_burn_safety")
            if current.is_approved:
                list_display += ("day_of_burn_completed", "day_of_burn_completer")
        elif request.GET.get('post_burn', False):
            # Post burn actions
            list_display = ("__str__", "details")
            if current.is_approved:
                list_display += ("post_burn_completed", "post_burn_completer")
        else:
            # We are on the plan actions page if this falls through.
            list_display = ("relevant", "__str__", "details",
                            "pre_burn", "day_of_burn", "post_burn",
                            "context_statement", "add_action")
            #if current.is_draft:
                #list_display = ("relevant", "__str__", "details",
                                #"pre_burn", "day_of_burn", "post_burn",
                                #"context_statement", "add_action")
            #else:
                #list_display = ("relevant", "__str__", "details",
                                #"pre_burn", "day_of_burn", "post_burn",
                                #"context_statement")
        return list_display + (delete,)

    def get_list_editable(self, request):
        """
        Return the editable columns on the actions changelist based on the
        request and the current prescription's status.
        """
        current = self.prescription
        if current.is_closed:
            return ("id",)

        if request.GET.get('pre_burn', False):
            # Pre-burn actions
            list_editable = ("pre_burn_resolved", "pre_burn_explanation")
            list_editable += ("pre_burn_completed", "pre_burn_completer")
        elif request.GET.get('day_of_burn', False):
            # Day of burn actions
            list_editable = ("day_of_burn_include", "day_of_burn_situation",
                             "day_of_burn_mission", "day_of_burn_execution",
                             "day_of_burn_administration",
                             "day_of_burn_command", "day_of_burn_safety",
                             "day_of_burn_responsible")
            if current.is_approved:
                list_editable += ("day_of_burn_completed",
                                  "day_of_burn_completer")
        elif request.GET.get('post_burn', False):
            # Post burn actions
            list_editable = ()
            if current.is_approved:
                list_editable += ("post_burn_completed", "post_burn_completer")
        else:
            # Plan actions editable fields.
            list_editable = ("relevant", "details", "pre_burn", "day_of_burn",
                             "post_burn", "context_statement")
        return list_editable

    def get_readonly_fields(self, request, obj=None):
        actions = ['pre_burn', 'day_of_burn', 'post_burn']

        if self.prescription.is_closed:
            return self.list_editable

        if any([request.GET.get(action, False) for action in actions]):
            return ("details",)

        #return super(ActionAdmin, self).get_readonly_fields(request, obj)
        return super(PrescriptionMixin, self).get_readonly_fields(request, obj)

    def get_list_filter(self, request):
        """
        If we are on the plan actions page, allow filtering on relevance and
        risk category. Otherwise, disallow filtering.
        """
        actions = ['pre_burn', 'day_of_burn', 'post_burn']

        if not any([request.GET.get(action, False) for action in actions]):
            return ('relevant', 'risk__category')

    def risk_category(self, obj):
        return obj.risk.category

    def add_action(self, obj):
        if obj.index == 1:
            url = reverse('admin:risk_action_add',
                          args=(self.prescription.pk,),
                          current_app=self.admin_site.name)
            return ('<a class="btn btn-mini btn-success" href="%s?risk=%s">'
                    'Add</a>') % (url, obj.risk.pk)
        else:
            url = reverse('admin:risk_action_delete',
                          args=(obj.pk, self.prescription.pk),
                          current_app=self.admin_site.name)
            return ('<a class="btn btn-mini btn-danger" href="%s">'
                    'Remove</a>') % url
    add_action.short_description = "Multiple?"
    add_action.allow_tags = True

    def save_model(self, request, obj, form, change=True):
        """
        Save the model and assign delete permissions to particular objects.
        """
        if request.GET.get('risk'):
            obj.risk = Risk.objects.get(pk=request.GET.get('risk'))
        obj.risk.prescription = self.prescription
        obj.save()

        # If can_delete is set, allow the user to delete this object.
        if self.can_delete:
            opts = self.opts
            group = Group.objects.get(name='Users')
            perm = get_permission_codename('delete', opts)
            assign_perm("%s.%s" % (opts.app_label, perm), group, obj)


class TreatmentAdmin(PrescriptionMixin, BaseAdmin):
    prescription_filter_field = "register__prescription"
    list_display = ('description', 'location', 'complete')
    form = TreatmentForm
    can_delete = True
    lock_after = 'endorsement'

    def get_urls(self):
        """
        Add an extra view to handle marking a treatment as complete.
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
           re_path(r'^complete/prescription/(\d+)/$',
                wrap(self.mark_as_complete),
                name='%s_%s_complete' % info),
        ]
        return urlpatterns + super(TreatmentAdmin, self).get_urls()

    def mark_as_complete(self, request, prescription_id):
        """
        Mark a treatment as dealt with.
        """
        object_id = request.POST.get('id')
        obj = self.get_object(request, unquote(object_id))
        current = self.get_prescription(request, unquote(prescription_id))
        if ((obj is not None and self.has_change_permission(request, obj) and
            request.method == "POST" and current.is_draft)):
            # NOTE: instantiating the ModelForm below was still resulting in
            # a form with the 'locations' field (same as the TreatmentForm).
            # This would fail validation on the submit in section B2.
            # Workaround was to create and use the TreatmentCompleteForm instead.
            # Might be refactored by a better Django dev than I.
            #ModelForm = self.get_form(request, obj, fields=('complete',))
            #form = ModelForm(request.POST, request.FILES, instance=obj)
            form = TreatmentCompleteForm(request.POST, request.FILES, instance=obj)
            complete = obj.complete     # form.is_valid() updates the obj
            if form.is_valid():
                obj = self.save_form(request, form, change=True)
                self.save_model(request, obj, form, change=True)
            else:
                obj.complete = complete
            return HttpResponse(json.dumps({'complete': obj.complete, 'description': obj.description}))
        return HttpResponse(
            'Sorry, this endpoint only accepts valid POST requests.')

    def response_post_save_add(self, request, obj):
        """
        Override the redirect url after successful save of a new Treatment.
        """
        if request.session.get('previous_page', False):
            url = request.session.get('previous_page')
        else:
            url = reverse('admin:prescription_prescription_detail',
                          args=[str(obj.prescription.pk)])
        return HttpResponseRedirect(url)

    def response_post_save_change(self, request, obj):
        """
        Override the redirect url after successful save of an existing
        Treatment.
        """
        if request.session.get('previous_page', False):
            url = request.session.get('previous_page')
        else:
            url = reverse('admin:prescription_prescription_detail',
                          args=[str(obj.prescription.pk)])
        return HttpResponseRedirect(url)

    def save_model(self, request, obj, form, change):
        if not change:
            object_id = unquote(request.GET.get('register'))

            try:
                obj.register = Register.objects.get(pk=object_id)
            except Register.DoesNotExist:
                return

        if 'locations' in form.cleaned_data:
            locations = list(form.cleaned_data.get('locations'))
            obj.location = locations.pop()
            for location in locations:
                Treatment.objects.create(
                    location=location,
                    description=obj.description,
                    register=obj.register,
                )

        obj.save()

    def get_form(self, request, obj=None, **kwargs):
        previous_page = request.GET.get("next", False)
        if not previous_page:
            previous_page = request.META.get('HTTP_REFERER')
        if ((previous_page is not None and
             previous_page.split("/")[-4] not in ('add', 'change') and
             previous_page.split("/")[-5] not in ('treatment'))):
            request.session['previous_page'] = previous_page
        if obj:  # obj is not None, so this is a change page
            kwargs['exclude'] = ['register', ]
        return super(TreatmentAdmin, self).get_form(request, obj=obj, **kwargs)


class RiskAdmin(PrescriptionMixin, BaseAdmin):
    form = RiskForm

    def save_model(self, request, obj, form, change):
        super(RiskAdmin, self).save_model(request, obj, form, change)
        if not change:
            Action.objects.create(risk=obj)
