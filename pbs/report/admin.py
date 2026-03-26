from datetime import datetime

from django import forms
from django.contrib.admin.utils import unquote
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList

from pbs.admin import BaseAdmin
from pbs.prescription.admin import PrescriptionMixin, SavePrescriptionMixin
from pbs.prescription.forms import PrescriptionIgnitionCompletedForm
from pbs.report.forms import AreaAchievementForm, PostBurnChecklistForm

csrf_protect_m = method_decorator(csrf_protect)



class AreaAchievementAdmin(SavePrescriptionMixin, PrescriptionMixin,
                           BaseAdmin):
    # list_display = ("ignition", "area_estimate",
    #                 "area_treated", "edging_length",
    #                 "edging_depth_estimate", "date_escaped",
    #                 "dpaw_fire_no", "dfes_fire_no")
    # list_editable = ("ignition", "area_estimate",
    #                  "area_treated", "edging_length",
    #                  "edging_depth_estimate", "date_escaped",
    #                  "dpaw_fire_no", "dfes_fire_no")
    list_display = ["ignition", "area_estimate",
                    "area_treated", "edging_length",
                    "edging_depth_estimate", "date_escaped",
                    "dpaw_fire_no", "dfes_fire_no"]
    list_editable = ["ignition", "area_estimate",
                     "area_treated", "edging_length",
                     "edging_depth_estimate", "date_escaped",
                     "dpaw_fire_no", "dfes_fire_no"]
    list_ignition_editable = ["ignition", "ignition_types","area_estimate",
                     "area_treated", "edging_length",
                     "edging_depth_estimate", "date_escaped",
                     "dpaw_fire_no", "dfes_fire_no"]
    list_ignition_types = ("ignition_types",)
    list_display_links = (None,)
    list_empty_form = True
    actions = None
    form = AreaAchievementForm
    ignition_form = PrescriptionIgnitionCompletedForm
    can_delete = True
    lock_after = 'closure'

    @csrf_protect_m
    def changelist_view(self, request, prescription_id, extra_context=None):
        """ Add an extra ModelForm to the view, to allow updates to the
        ignition completion date.
        """        
        p = self.get_prescription(request, unquote(prescription_id))

        ignition_latest = None
        if len(p.areaachievement_set.all()) > 0:
            ignition_latest = p.areaachievement_set.all()[0].ignition
            for area in p.areaachievement_set.all():
                if area.ignition > ignition_latest:
                    ignition_latest = area.ignition

        if (request.method == "POST" and 'ignition_completed_date' in request.POST):
            # Process the seperate ignition completed modelform.
            # TODO: work out how to call the modelform's clean() method,
            # rather than duplicating it below.
            ignition = request.POST.get('ignition_completed_date', None)
            if ignition:
                ignition = datetime.strptime(ignition, '%Y-%m-%d').date()
            else:
                ignition = None
            if p.is_approved:
                latest_approval = p.approval_set.latest().valid_to
            else:
                latest_approval = None

            if(ignition is not None and len(p.areaachievement_set.all()) == 0):
                messages.add_message(request, messages.ERROR,
                "Need at least one area burn.")
            elif(ignition_latest and ignition and ignition < ignition_latest):
                messages.add_message(request, messages.ERROR,
                "Ignition Completed date cannot be before "
                "the final/latest area burn date.")
            else:
                if p.ignition_completed_date != ignition:
                    messages.add_message(request, messages.INFO,
                        "Ignition completion date saved.")
                p.ignition_completed_date = ignition
                p.save()
        context = {'ignition_completed_date_form': self.ignition_form(
            initial={'ignition_completed_date': p.ignition_completed_date})}
        context.update(extra_context or {})

        return super(AreaAchievementAdmin, self).changelist_view(
            request, prescription_id, extra_context=context)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        return super(AreaAchievementAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        """
        Allow adding achievements post approval but not post closure.
        """
        current = self.prescription
        if current.is_closed or not current.is_approved:
            return self.list_editable
        else:
            return (None,)
        


    def get_changelist(self, request, **kwargs):
        ChangeList = super().get_changelist(request, **kwargs)
        
        class AreaAchievementChangeListIn(ChangeList):
            def __init__(self, request, model, list_display, list_display_links, list_filter,
                    date_hierarchy, search_fields, list_select_related, list_per_page,
                    list_max_show_all, list_editable, model_admin, sortable_by,search_help_text,):

                super().__init__(
                request, model, list_display, list_display_links, list_filter,
                date_hierarchy, search_fields, list_select_related, list_per_page,
                list_max_show_all, list_editable, model_admin, sortable_by, search_help_text,
                )
                # self.list_display = ["ignition_types"] + self.list_display
                self.list_display.insert(1,"ignition_types")
                #self.list_editable = ["ignition_types"] + self.list_editable
                self.list_editable.insert(1,"ignition_types")
                self.list_display_links = (None,)
        return AreaAchievementChangeListIn


    def get_changelist_form(self, request, **kwargs):
        return self.form

    def get_changelist_formset(self, request, **kwargs):
        FormSet = super(AreaAchievementAdmin,
                        self).get_changelist_formset(request, **kwargs)
        return FormSet

    def get_list_editable(self, request):
        """
        A hack to display the ModelMultipleChoiceField for readonly User
        """
        current = self.prescription
        if request.user.has_perm('prescription.can_admin'):
            # return self.list_editable
            return self.list_ignition_editable
        if current.is_closed or not current.is_approved:
            return self.list_ignition_types

        return self.list_editable




class ProposedActionAdmin(PrescriptionMixin, SavePrescriptionMixin,
                          BaseAdmin):
    list_display = ('observations', 'action')
    list_editable = ('observations', 'action')
    list_empty_form = True
    list_display_links = (None, )
    actions = None
    can_delete = True
    lock_after = 'closure'

    def get_readonly_fields(self, request, obj=None):
        """
        Allow adding achievements post approval but not post closure.
        """
        current = self.prescription
        if current.is_closed or not current.is_approved:
            return self.list_editable
        else:
            return (None,)


class EvaluationAdmin(PrescriptionMixin, SavePrescriptionMixin,
                      BaseAdmin):
    prescription_filter_field = "criteria__prescription"
    list_display = ('criteria', 'achieved', 'summary')
    list_editable = ('achieved', 'summary')
    list_display_links = (None,)
    actions = None
    lock_after = 'closure'

    def queryset(self, request):
        qs = super(EvaluationAdmin, self).queryset(request)
        return qs.select_related("criteria__prescription", "criteria")

    def objectives(self, obj):
        objectives = "<ul>"
        for objective in obj.criteria.objectives.all():
            objectives += "<li>%s</li>" % objective
        objectives += "</ul>"
        return objectives
    objectives.short_description = "Burn objectives"
    objectives.allow_tags = True

    def get_readonly_fields(self, request, obj=None):
        """
        Allow adding achievements post approval but not post closure.
        """
        current = self.prescription
        if current.is_closed or not current.is_approved:
            return self.list_editable
        else:
            return (None,)


class PostBurnChecklistAdmin(PrescriptionMixin, SavePrescriptionMixin,
                             BaseAdmin):
    list_display = ('action', 'relevant', 'completed_on', 'completed_by')
    list_editable = ('relevant', 'completed_on', 'completed_by')
    list_display_links = (None,)
    actions = None
    lock_after = 'closure'
    form = PostBurnChecklistForm

    def get_readonly_fields(self, request, obj=None):
        """
        Allow adding achievements post approval but not post closure.
        """
        current = self.prescription
        if current.is_closed or not current.is_approved:
            return self.list_editable
        else:
            return (None,)

    def get_changelist_form(self, request, **kwargs):
        return self.form
