from __future__ import absolute_import, unicode_literals

from functools import update_wrapper

from django.contrib.admin import ModelAdmin
# from django.contrib.admin.util import unquote
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.template.response import TemplateResponse
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils.encoding import force_text


class RegionAdmin(ModelAdmin):
    """
    A ModelAdmin class for the Region and District model types.
    """
    list_display = ('id', 'name', 'slug', 'modified', 'effective_to')
    raw_id_fields = ('creator', 'modifier')
    prepopulated_fields = {'slug': ['name']}


class RelatedFieldAdmin(ModelAdmin):
    def __getattr__(self, name):
        if '__' in name:
            related_names = name.split('__')
            description = related_names[-1].title()

            def getter(self, obj):
                for related_name in related_names:
                    obj = getattr(obj, related_name)
                return obj
            getter.admin_order_field = name
            getter.short_description = description.replace('_', ' ')
            setattr(self, name, getter)
            return getter
        raise AttributeError


class DetailAdmin(ModelAdmin):
    detail_template = None
    changelist_link_detail = False
    # prevents django-guardian from clobbering change_form template (Scott)
    change_form_template = None

    def get_changelist(self, request, **kwargs):
        from swingers.admin.views import DetailChangeList
        return DetailChangeList

    def has_view_permission(self, request, obj=None):
        opts = self.opts
        return request.user.has_perm(
            opts.app_label + '.' + 'view_%s' % opts.object_name.lower()
        )

    def get_urls(self):
        from django.conf.urls import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name

        urlpatterns = patterns(
            '',
            url(r'^$',
                wrap(self.changelist_view),
                name='%s_%s_changelist' % info),
            url(r'^add/$',
                wrap(self.add_view),
                name='%s_%s_add' % info),
            url(r'^(\d+)/history/$',
                wrap(self.history_view),
                name='%s_%s_history' % info),
            url(r'^(\d+)/delete/$',
                wrap(self.delete_view),
                name='%s_%s_delete' % info),
            url(r'^(\d+)/change/$',
                wrap(self.change_view),
                name='%s_%s_change' % info),
            url(r'^(\d+)/$',
                wrap(self.detail_view),
                name='%s_%s_detail' % info),
        )
        return urlpatterns

    def detail_view(self, request, object_id, extra_context=None):
        opts = self.opts

        obj = self.get_object(request, unquote(object_id))

        if not self.has_view_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does '
                            'not exist.') % {
                                'name': force_text(opts.verbose_name),
                                'key': escape(object_id)})

        context = {
            'title': _('Detail %s') % force_text(opts.verbose_name),
            'object_id': object_id,
            'original': obj,
            'is_popup': "_popup" in request.REQUEST,
            'media': self.media,
            'app_label': opts.app_label,
            'opts': opts,
            'has_change_permission': self.has_change_permission(request, obj),
        }
        context.update(extra_context or {})
        return TemplateResponse(request, self.detail_template or [
            "admin/%s/%s/detail.html" % (opts.app_label,
                                         opts.object_name.lower()),
            "admin/%s/detail.html" % opts.app_label,
            "admin/detail.html"
        ], context, current_app=self.admin_site.name)

    def queryset(self, request):
        qs = super(DetailAdmin, self).queryset(request)
        return qs.select_related(
            *[field.rsplit('__', 1)[0]
              for field in self.list_display if '__' in field]
        )
