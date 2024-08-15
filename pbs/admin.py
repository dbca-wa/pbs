from functools import partial

from django.contrib.admin import ModelAdmin, widgets
from django.forms.models import modelformset_factory

from pbs.forms import PbsModelForm

import logging
logger = logging.getLogger("log." + __name__)


def get_permission_codename(action, opts):
    """
    Returns the codename of the permission for the specified action.
    """
    # return '%s_%s' % (action, opts.module_name)
    return '%s_%s' % (action, opts.model_name)


class BaseAdmin(ModelAdmin):
    list_editable_extra = 0
    list_empty_form = False

    def save_model(self, request, obj, form, change):
        """
        Save user to object if an audit object
        """
        if not obj.pk:
            obj.creator = request.user
        obj.modifier = request.user
        obj.save()

    def get_list_editable(self, request):
        return self.list_editable

    def formfield_for_dbfield(self, db_field, **kwargs):
        # a quick patch to handle our "special" prescription-aware urls
        # disable the plus/add link (alias RelatedFieldWidgetWrapper)
        formfield = super(BaseAdmin, self).formfield_for_dbfield(db_field,
                                                                 **kwargs)
        if formfield and isinstance(formfield.widget,
                                    widgets.RelatedFieldWidgetWrapper):
            # bypass the wrapper, it quietly hides the "real" widget inside
            formfield.widget = formfield.widget.widget
        return formfield

    def get_changelist_formset(self, request, **kwargs):
        """
        Returns a FormSet class for use on the changelist page if list_editable
        is used.
        """
        defaults = {
            "formfield_callback": partial(self.formfield_for_dbfield,
                                          request=request),
        }

        defaults.update(kwargs)
        fields = self.get_list_editable(request)
        return modelformset_factory(
            self.model, self.get_changelist_form(request, form=PbsModelForm),
            extra=self.list_editable_extra, fields=fields, **defaults)

    def has_delete_permission(self, request, obj=None):
        """
        Add object permissions to the check for delete permissions.
        Module-level permissions will trump object-level permissions.
        """
        opts = self.opts
        codename = get_permission_codename('delete', opts)
        return any([
            request.user.has_perm("%s.%s" % (opts.app_label, codename)),
            request.user.has_perm("%s.%s" % (opts.app_label, codename), obj)])

    def has_change_permission(self, request, obj=None):
        """
        Add object permissions to the check for change permissions.
        Module-level permissions will trump object-level permissions.
        """
        opts = self.opts
        codename = get_permission_codename('change', opts)
        return any([
            request.user.has_perm("%s.%s" % (opts.app_label, codename)),
            request.user.has_perm("%s.%s" % (opts.app_label, codename), obj)])

    def has_view_permission(self, request, obj=None):
        """
        Check for view permissions. Module-level permissions will trump
        object-level permissions.
        """
        opts = self.opts
        codename = get_permission_codename('view', opts)
        return any([
            request.user.has_perm("%s.%s" % (opts.app_label, codename)),
            request.user.has_perm("%s.%s" % (opts.app_label, codename), obj)])
