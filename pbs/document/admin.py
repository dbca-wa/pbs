from __future__ import unicode_literals, absolute_import

import re
from functools import partial, update_wrapper

from django_downloadview import ObjectDownloadView
from django.contrib import messages
from django.contrib.admin.utils import quote, unquote
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from .models import Document, DocumentTag, DocumentCategory
from .forms import DocumentForm

from pbs.admin import BaseAdmin
from pbs.prescription.admin import PrescriptionMixin, SavePrescriptionMixin
from pbs.prescription.actions import delete_selected, archive_documents
from django.shortcuts import redirect


class DocumentAdmin(SavePrescriptionMixin, PrescriptionMixin,
                    BaseAdmin):
    list_display = ("descriptor_download", "category", "date_document_created", "uploaded_on",
                    "uploaded_by")
    list_display_links = (None,)
    search_fields = ("category__name", "tag__name", "custom_tag",
                     "modifier__username")
    #actions = None
    actions = [delete_selected, archive_documents]

    form = DocumentForm
    can_delete = True
    lock_after = "closure"

#    def changelist_view(self, request, prescription_id, extra_context=None):
        #"""
        #set the default view queryset to display un-archived documents
        #"""
        #referrer = request.META.get('HTTP_REFERER', '')
        #if len(request.GET) == 0 and '?' not in referrer:
            #get_param = "document_archived__exact=0"
            #return redirect("{url}?{get_parms}".format(url=request.path, get_parms=get_param))

        #return super(DocumentAdmin, self).changelist_view(
#            request, prescription_id, extra_context={})

    def get_actions(self, request):
        actions = super(DocumentAdmin, self).get_actions(request)
        if not request.user.has_perm('prescription.delete_prescription'):
            if actions['delete_selected']:
                del actions['delete_selected']
        if not request.user.has_perm('document.archive_document'):
            if actions['archive_documents']:
                del actions['archive_documents']
        return actions

    def get_list_display(self, request):
        """
        Allow the use of the current request inside our remove function.
        This lets us check if the current user has permission to delete a
        particular document. Pretty nifty.
        """
        delete = partial(self.remove, request=request)
        delete.short_description = ""
        delete.allow_tags = True
        return self.list_display + (delete,)

    def get_list_filter(self, request):
        if request.get_full_path().find("/tag/") == -1:
            return ("document_archived", "category", "modified", "modifier")
        else:
            return ()

    def date_document_created(self, obj):
        if obj.document_created is None:
            return 'N/A'
        return obj.document_created.date()
    date_document_created.admin_order_field = "document_created"

    def uploaded_by(self, obj):
        return obj.creator.get_full_name()
    uploaded_by.admin_order_field = "creator"

    def uploaded_on(self, obj):
        return obj.created
    uploaded_on.admin_order_field = "created"

    def descriptor_download(self, obj):
        return mark_safe('<a href="{0}" target="_blank">'
                         '<i class="icon-file"></i> {1}'
                         '</a>'.format(reverse('document_download', kwargs={'pk': obj.pk}), obj.descriptor))
    descriptor_download.admin_order_field = "tag"
    descriptor_download.short_description = "Descriptor"

    def response_post_save_add(self, request, obj):
        """
        Override the redirect url after successful save of a new document.
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
        document.
        """
        if request.session.get('previous_page', False):
            url = request.session.get('previous_page')
        else:
            url = reverse('admin:prescription_prescription_detail',
                          args=[str(obj.prescription.pk)])
        return HttpResponseRedirect(url)

    def get_changelist(self, request, **kwargs):
        # Returns customised changelist filtered by tag or category as well as
        # current prescription
        ChangeList = super(DocumentAdmin, self).get_changelist(request, **kwargs)
        model_admin = self

        class DocumentChangeList(ChangeList):
            def get_query_set(self, request):
                qs = super(DocumentChangeList, self).get_query_set(request)
                current = model_admin.prescription

                if current:
                    fields = {
                        model_admin.prescription_filter_field: current
                    }
                    qs = qs.filter(**fields)

                category = re.findall("/category/(.+)/", request.path)
                tag = re.findall("/tag/(.+)/", request.path)

                if category:
                    category = category[0].replace('_', ' ')
                    qs = qs.filter(tag__category__name__iexact=category)
                if tag:
                    tag = tag[0].replace('_', ' ')
                    #only show non-archived documents for tag view
                    qs = qs.filter(tag__name__iexact=tag,document_archived=False)
              

                return qs

        return DocumentChangeList

    def save_model(self, request, obj, form, change):
        obj.category = obj.tag.category
        super(DocumentAdmin, self).save_model(
            request=request, obj=obj, form=form, change=change)

    def get_form(self, request, obj=None, **kwargs):
        previous_page = request.GET.get("next", False) or request.META.get('HTTP_REFERER')
        if ((previous_page is not None and
             previous_page.split("/")[-4] not in ('add', 'change'))):
            request.session['previous_page'] = previous_page
        tag = request.GET.get('tag', None)
        if tag is not None:
            kwargs['fields'] = ("tag", "document")
        return super(DocumentAdmin, self).get_form(request, obj=obj, **kwargs)

    def add_view(self, request, prescription_id, form_url='', extra_context=None):
        model = self.model
        opts = model._meta
        tag_id = request.GET.get('tag', None)
        if tag_id is not None:
            tag = get_object_or_404(DocumentTag, pk=unquote(tag_id))
            extra_context = extra_context or {}
            extra_context.update({
                'title': (_('Add %s %s') %
                         (force_text(tag.name),
                          force_text(opts.verbose_name)))
            })

        # I think the approach is to capture and validate the form on post,
        # and if its invalid redirect to the original url with an error message.
        if request.method == "POST":
            ModelForm = self.get_form(request)
            form = ModelForm(request.POST, request.FILES)
            if form.is_valid():
                # From django.contrib.admin.options.add_view Line 1118+
                new_object = self.save_form(request, form, change=False)
                if new_object.prescription is None:
                    new_object.prescription = self.get_prescription(request, prescription_id)
                self.save_model(request, new_object, form, False)
                return self.response_add(request, new_object)
            else:
                messages.error(request, "Was that a supported file type? Or some fields missing?")
                base_url = reverse('admin:document_document_add',
                                   args=[str(prescription_id)])
                # querystring = "?tag={d[tag]}".format(d=request.POST)
                # url = base_url + querystring
                return HttpResponseRedirect(base_url)
        return super(DocumentAdmin, self).add_view(request, prescription_id,
                                                form_url, extra_context)

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
            return ('<a href="%s" class="btn btn-mini alert-error" '
                    'title="Delete"><i class="icon-trash"></i></a>') % delete_url
        else:
            return ""

    def category_view(self, request, prescription_id, category_name,
                      extra_context=None):
        """
        Wraps the change list with some extra category related information.
        """
        opts = DocumentCategory._meta

        category_name = unquote(category_name.replace("_", " "))

        try:
            category = DocumentCategory.objects.get(name__iexact=category_name)
        except DocumentCategory.DoesNotExist:
            raise Http404(
                _('%(name)s object with primary key %(key)r does not exist.') %
                {'name': force_text(opts.verbose_name), 'key': escape(category_name)}
            )

        context = {
            "title": category.name,
            "tags": category.documenttag_set.all()
        }
        context.update(extra_context or {})
        return self.changelist_view(request, prescription_id, context)

    def tag_view(self, request, prescription_id, tag_name, extra_context=None):
        """
        Wraps the change list with some extra tag related information.
        """
        tag = unquote(tag_name.replace("_", " "))
        opts = DocumentCategory._meta

        try:
            document_tag = DocumentTag.objects.get(name__iexact=tag)
        except DocumentTag.DoesNotExist:
            raise Http404(
                _('%(name)s object with primary key %(key)r does not exist.') %
                {'name': force_text(opts.verbose_name), 'key': escape(tag)}
            )

        context = {
            "title": document_tag.name,
            "tags": [document_tag]
        }
        context.update(extra_context or {})
        return self.changelist_view(request, prescription_id, context)

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
           re_path(r'^prescription/(.+)/all/$',
                wrap(self.changelist_view),
                {"extra_context": {
                    "title": "Documents",
                    "tags": DocumentTag.objects.not_tag_names(
                        "Traffic Diagrams",
                        "Sign Inspection and Surveillance Form",
                        ("Prescribed Burning Organisational Structure "
                            "and Communications Plan"),
                        "Context Map", "Prescribed Burning SMEAC Checklist")
                }},
                name='%s_%s_all' % info),
           re_path(r'^prescription/(.+)/category/(.+)/$',
                wrap(self.category_view),
                name='%s_%s_category' % info),
           re_path(r'^prescription/(.+)/tag/(.+)/$',
                wrap(self.tag_view),
                name='%s_%s_tag' % info)
        ]

        return urlpatterns + super(DocumentAdmin, self).get_urls()
