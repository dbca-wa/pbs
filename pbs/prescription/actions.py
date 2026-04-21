import os
import shutil

from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext
from django.db import router, transaction
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy, gettext as _

from guardian.shortcuts import assign_perm

from pbs.prescription.models import JobQueue, Prescription
from pbs.utils import get_deleted_objects, update_permissions, support_email

from pbs.document.models import Document, DocumentCategory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.conf import settings
import datetime
import subprocess

from pbs.utils import pdflatex

import logging
logger = logging.getLogger('pbs')


def _carry_over_archive_name(prescription, now=None):
    local_now = timezone.localtime(now or timezone.now())
    timestamp = local_now.strftime("%Y-%m-%dT%H%M%S")
    return "{0}_pre_carry_over_{1}".format(prescription.burn_id, timestamp)


def _archive_prescription_for_carry_over(prescription, archive_name):
    with pdflatex(
        prescription,
        template="pfp",
        downloadname=archive_name,
        embed=True,
        headers=True,
        title="Prescribed Fire Plan"
    ) as pdfresult:
        if pdfresult.succeed:
            directory = os.path.join(
                settings.MEDIA_ROOT,
                'snapshots',
                prescription.financial_year.replace("/", "-"),
                prescription.burn_id
            )
            if not os.path.exists(directory):
                os.makedirs(directory)

            source_file = pdfresult.pdf_file
            shutil.copyfile(source_file, os.path.join(directory, "{}.pdf".format(archive_name)))
            os.remove(source_file)
            Prescription.objects.filter(pk=prescription.pk).update(archive_successful=True)
            return

        title = 'PDF production failed when attempting to archive Prescription at Carry over burn function: {}'.format(prescription)
        logger.warning(title)
        Prescription.objects.filter(pk=prescription.pk).update(archive_successful=False)
        raise Exception(pdfresult.errormessage)


def _apply_carry_over_changes(prescription, admin_site, request=None, user=None):
    prescription.clear_approvals()
    prescription.carried_over = True
    prescription.planning_status = prescription.PLANNING_DRAFT
    prescription.planning_status_modified = timezone.now()
    prescription.prescribing_officer = None
    prescription.financial_year = ''
    # Skip the status-change archive signal: the pre-carry-over archive created
    # by this workflow is the authoritative snapshot for this action.
    prescription._updating_pdf_status = True
    prescription.save()
    update_permissions(prescription, admin_site, "endorsement", assign_perm)
    _create_approvals_pdf(prescription, request=request, user=user)


def _enqueue_carry_over_prescription(prescription, requested_by):
    archive_name = _carry_over_archive_name(prescription)

    def _enqueue():
        JobQueue.objects.get_or_create(
            dedupe_key=archive_name,
            defaults={
                'job_type': JobQueue.TYPE_CARRY_OVER_PRESCRIPTION,
                'prescription': prescription,
                'requested_by': requested_by,
                'payload': {
                    'archive_name': archive_name,
                },
                'status': JobQueue.STATUS_QUEUED,
            }
        )
        Prescription.objects.filter(pk=prescription.pk).update(archive_in_progress=True)

    transaction.on_commit(_enqueue)


def delete_selected(modeladmin, request, queryset):
    """
    Default action which deletes the selected objects.

    This action first displays a confirmation page whichs shows all the
    deleteable objects, or, if the user has no permission one of the related
    childs (foreignkeys), a "permission denied" message.

    Next, it deletes all selected objects and redirects back to the change
    list.
    """
    opts = modeladmin.model._meta
    app_label = opts.app_label

    # Check that the user has delete permission for the actual model
    if not modeladmin.has_delete_permission(request):
        raise PermissionDenied

    using = router.db_for_write(modeladmin.model)

    # Populate deletable_objects, a data structure of all related objects that
    # will also be deleted.
    deletable_objects, perms_needed, protected = get_deleted_objects(
        queryset, opts, request.user, modeladmin.admin_site, using)

    # The user has already confirmed the deletion.
    # Do the deletion and return a None to display the change list view again.
    if request.POST.get('post'):
        if perms_needed:
            raise PermissionDenied
        n = queryset.count()
        if n:
            prescription_list = []
            for obj in queryset:
                if obj._meta.object_name == 'Prescription':
                    prescription_list.append(obj.burn_id + ' - ' + obj.name + ' (' + obj.season + ')')
                obj_display = force_str(obj)
                modeladmin.log_deletion(request, obj, obj_display)
            queryset.delete()
            if str(opts) == 'prescription.prescription':
                msg = ''
                for pfp in prescription_list:
                    msg += '<ul>' + pfp + '</ul>'
                modeladmin.message_user(request, _("Successfully deleted the following ePFPs:\n{0}").format(msg),
                                        messages.SUCCESS, extra_tags="safe")
            else:
                modeladmin.message_user(request, _("Successfully deleted %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                }, messages.SUCCESS)
        # Return None to display the change list page again.
        return None

    if len(queryset) == 1:
        objects_name = force_str(opts.verbose_name)
    else:
        objects_name = force_str(opts.verbose_name_plural)

    if perms_needed or protected:
        title = _("Cannot delete %(name)s") % {"name": objects_name}
    else:
        title = _("Are you sure?")

    context = {
        "title": title,
        "objects_name": objects_name,
        "deletable_objects": [deletable_objects],
        'queryset': queryset,
        "perms_lacking": perms_needed,
        "protected": protected,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        "current_app": modeladmin.admin_site.name
    }

    # Display the confirmation page
    # return TemplateResponse(request, modeladmin.delete_selected_confirmation_template or [
    #     "admin/%s/%s/delete_selected_confirmation.html" % (app_label, opts.model_name),
    #     "admin/%s/delete_selected_confirmation.html" % app_label,
    #     "admin/delete_selected_confirmation.html"
    # ], context, current_app=modeladmin.admin_site.name)
    return TemplateResponse(request, modeladmin.delete_selected_confirmation_template or [
        "admin/%s/%s/delete_selected_confirmation.html" % (app_label, opts.model_name),
        "admin/%s/delete_selected_confirmation.html" % app_label,
        "admin/delete_selected_confirmation.html"
    ], context)

delete_selected.short_description = gettext_lazy("Delete selected %(verbose_name_plural)s")


def delete_approval_endorsement(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    app_label = opts.app_label

    if not request.user.has_perm('prescription.can_delete_approval'):
        raise PermissionDenied

    if len(queryset) > 1:
        messages.error(request, _(
            "You can only remove approvals and endorsements "
            "from one ePFP at a time."))
        return None

    # The user has already confirmed the deletion.
    # Do the deletion and return a None to display the change list view again.
    # We have already evaluated the queryset at this point and ensured that
    # there is only one member, just index it directly.
    if request.POST.get('post'):
        obj = queryset[0]
        obj.clear_approvals()
        msg = 'Delete: Clearing Approvals/Endorsements', 'Burn ID: {}, Deleted by: {}'. format(obj.burn_id, request.user.get_full_name())
        logger.warning(msg)
        support_email('Delete: Clearing Approvals/Endorsements', msg)

        update_permissions(obj, modeladmin.admin_site, "endorsement",
                           assign_perm)

        modeladmin.message_user(
            request, _("Successfully removed endorsements and approval from "
                       "%(id)s - %(name)s (%(season)s).") % {
                "id": obj.burn_id,
                "name": obj.name,
                "season": obj.season
            }, messages.SUCCESS
        )
        # Return None to display the change list page again.
        return None

    title = _("Are you sure?")

    context = {
        "title": title,
        "remove": 'all endorsements and approval',
        "action": 'delete_approval_endorsement',
        "objects_name": force_str(opts.verbose_name),
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        "current_app": modeladmin.admin_site.name
    }

    # Display the confirmation page
    return TemplateResponse(
        request, modeladmin.remove_selected_confirmation_template,
        context)

delete_approval_endorsement.short_description = gettext_lazy("Remove Burn Plan Endorsements and Approval")


def carry_over_burns(modeladmin, request, queryset):
    """
    Carry over the selected burns into another year or season. This strips the
    burn of any corporate approval, endorsements, and approvals and allows
    the burn program developer to reschedule and edit the burn again.
    """
    opts = modeladmin.model._meta
    app_label = opts.app_label

    if not request.user.has_perm('prescription.can_carry_over'):
        raise PermissionDenied

    # Check if the user has selected any closed burns, and redirect them back
    # to the regional overview with a message if they have.
    if queryset.filter(status=Prescription.STATUS_CLOSED).count() > 0:
        modeladmin.message_user(request,
            _("You cannot carry over closed burns. Please review your "
              "selection and run this action again."),
            messages.ERROR)
        url = reverse('admin:prescription_prescription_changelist')
        return HttpResponseRedirect(url)

    # The user confirmed they want to carry over the selected burns.
    if request.POST.get('post'):
        if getattr(settings, 'PRESCRIPTION_ARCHIVE_USE_QUEUE', False):
            for prescription in queryset:
                _enqueue_carry_over_prescription(
                    prescription=prescription,
                    requested_by=request.user,
                )

            modeladmin.message_user(
                request,
                _("Queued carry over for %s burns. They will become available for editing once archiving finishes." % queryset.count()),
                messages.SUCCESS
            )
            url = reverse('admin:prescription_prescription_changelist')
            return HttpResponseRedirect(url)

        # Queue processing is disabled, so preserve the legacy synchronous
        # carry-over flow: archive first, then mutate the prescription.
        for prescription in queryset:
            # Legacy synchronous implementation retained for reference.
            # now = timezone.localtime(timezone.now())
            # timestamp = now.strftime("%Y-%m-%dT%H%M%S")
            # archivename = "{0}_pre_carry_over_{1}".format(prescription.burn_id, timestamp)
            # with pdflatex(
            #     prescription,
            #     template="pfp",
            #     downloadname=archivename,
            #     embed=True,
            #     headers=True,
            #     title="Prescribed Fire Plan"
            # ) as pdfresult:
            #     if pdfresult.succeed:
            #         directory = os.path.join(
            #             settings.MEDIA_ROOT,
            #             'snapshots',
            #             prescription.financial_year.replace("/", "-"),
            #             prescription.burn_id
            #         )
            #         if not os.path.exists(directory):
            #             os.makedirs(directory)
            #         source_file = pdfresult.pdf_file
            #         shutil.copyfile(
            #             source_file,
            #             os.path.join(directory, "{}.pdf".format(archivename))
            #         )
            #         os.remove(source_file)
            #         prescription._updating_pdf_status = True
            #         Prescription.objects.filter(pk=prescription.pk).update(archive_successful=True)
            #     else:
            #         title = 'PDF production failed when attempting to archive Prescription at Cary over burn function: {}'.format(prescription)
            #         logger.warning(title)
            #         prescription._updating_pdf_status = True
            #         Prescription.objects.filter(pk=prescription.pk).update(archive_successful=False)
            #         raise Exception(pdfresult.errormessage)
            #
            # prescription.clear_approvals()
            # prescription.carried_over = True
            # prescription.planning_status = prescription.PLANNING_DRAFT
            # prescription.planning_status_modified = timezone.now()
            # prescription.prescribing_officer = None
            # prescription.financial_year = ''
            # prescription.save()
            # update_permissions(prescription, modeladmin.admin_site,
            #     "endorsement", assign_perm)
            # _create_approvals_pdf(prescription, request)
            archive_name = _carry_over_archive_name(prescription)
            _archive_prescription_for_carry_over(prescription, archive_name)
            _apply_carry_over_changes(
                prescription,
                modeladmin.admin_site,
                request=request,
                user=request.user,
            )

        modeladmin.message_user(request,
            _("Successfully carried over %s burns. They are now available for "
              "editing again." % queryset.count()),
            messages.SUCCESS)
        url = reverse('admin:prescription_prescription_changelist')
        return HttpResponseRedirect(url)

    title = _("Are you sure you want to reschedule these burns?")

    context = {
        "title": title,
        "action": 'carry_over_burns',
        "objects_name": force_str(opts.verbose_name),
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        "current_app": modeladmin.admin_site.name
    }

    # return TemplateResponse(
    #     request, "admin/prescription/prescription/carry_over_burns.html",
    #     context, current_app=modeladmin.admin_site.name)
    return TemplateResponse(
        request, "admin/prescription/prescription/carry_over_burns.html",
        context)

carry_over_burns.short_description = gettext_lazy("Carry over burns")


def _create_approvals_pdf(prescription, request=None, user=None):
    now = datetime.datetime.now()
    date_str = now.strftime('%d%b%Y_%H%M%S')
    texname = '/tmp/parta_approvals-' + date_str + '.tex'
    directory = os.path.split(texname)[0]
    context = {
        'current': prescription,
        'prescription': prescription,
        'embed': False,
        'headers': True,
        'title': "Prescribed Fire Plan",
        'subtitle': "parta_approvals",
        'settings': settings,
        'timestamp': now,
    }

    output = render_to_string("latex/parta_approvals.tex", context)
    with open(texname, "w") as f:
        # f.write(output.encode('utf-8'))
        f.write(output)

    cmd = ['latexmk', '-f', '-silent', '-pdf', '-outdir={}'.format(directory), texname]
    subprocess.call(cmd)

    # clean up
    cmd = ['latexmk', '-c', '-outdir={}'.format(directory),texname]
    subprocess.call(cmd)

    with open(texname.replace('tex','pdf'), "rb") as f:
        suf = SimpleUploadedFile('Approvals PDF', f.read(), content_type='application/pdf')

    uid = request.user.id if request else (user.id if user else 1)
    cat = DocumentCategory.objects.get(pk=61) # defined in pbs/document/fixtures/initial_data.json
    tag = cat.documenttag_set.get(pk=218)

    Document.objects.get_or_create(
        creator_id=uid,
        modifier_id=uid,
        created=now,
        modified=now,
        prescription_id=prescription.id,
        category_id=cat.id,
        tag_id=tag.id,
        document=suf
    )

def bulk_corporate_approve(modeladmin, request, queryset):
    """
    Allow ePFP Application Administrator
    to bulk apply corporate approval to selected
    burns.
    """
    opts = modeladmin.model._meta
    app_label = opts.app_label

    if not request.user.has_perm('prescription.can_corporate_approve'):
        raise PermissionDenied

    # If any ePFPs are not seeking corporate approval, redirect back to the
    # regional overview with a message.
    prescriptions = list(queryset)
    if any([prescription.planning_status != prescription.PLANNING_SUBMITTED
            for prescription in prescriptions]):
        modeladmin.message_user(request,
            _("All ePFPs must be seeking corporate approval. Please review "
              "your selection and run this action again."),
            messages.ERROR)
        url = reverse('admin:prescription_prescription_changelist')
        return HttpResponseRedirect(url)

    # The user confirmed they want to carry over the selected burns.
    if request.POST.get('post'):
        for prescription in prescriptions:
            prescription.planning_status = prescription.PLANNING_APPROVED
            prescription.planning_status_modified = timezone.now()
            prescription.save()
            update_permissions(prescription, modeladmin.admin_site,
                "endorsement", assign_perm)

        modeladmin.message_user(request,
            _("Successfully applied approval for %s burns. They are now "
              "available to continue editing." % len(prescriptions)),
            messages.SUCCESS)
        url = reverse('admin:prescription_prescription_changelist')
        return HttpResponseRedirect(url)

    title = _("Are you sure you wish to apply corporate approval?")

    context = {
        "title": title,
        "action": 'bulk_corporate_approve',
        "objects_name": force_str(opts.verbose_name),
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
    }

    return TemplateResponse(
        request, "admin/prescription/prescription/bulk_corporate_approve.html",
        context, current_app=modeladmin.admin_site.name)

bulk_corporate_approve.short_description = gettext_lazy("Apply corporate approval")


def archive_documents(modeladmin, request, queryset):
    """
    Archive the documents in Part D
    """
    opts = modeladmin.model._meta
    app_label = opts.app_label
    if not request.user.has_perm('document.archive_document'):
        raise PermissionDenied

    # The user confirmed they want to carry over the selected burns.
    if request.POST.get('post'):
        for document in queryset:
            document.document_archived = True
            document.modifier = request.user
            document.save()

        modeladmin.message_user(request,
            _("Successfully archived %s document(s)." % queryset.count()),
            messages.SUCCESS)
        #url = reverse('admin:document_document_changelist')
        #url = reverse("admin/document/document/change_list.html")
        return None
        #return HttpResponseRedirect(url)

    title = _("Are you sure you want to archive these documents?")

    context = {
        "title": title,
        "action": 'archive_documents',
        "objects_name": force_str(opts.verbose_name),
        'queryset': queryset,
        "opts": opts,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
    }

    return TemplateResponse(
        request, "admin/document/document/archive_documents.html",
        context, current_app=app_label)

archive_documents.short_description = gettext_lazy("Archive documents")


