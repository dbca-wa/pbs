"""Handler and management command for archive_prescription queue jobs.

The module-level functions (handle_archive_prescription_job, etc.) are imported
by the generic process_job_queue dispatcher, so the logic lives in exactly one
place. The Command class exposes the same logic as a standalone management command
that accepts a --job-id argument, allowing operators to manually retry or process
a specific job without going through the queue worker.

Example usage:
    python manage.py process_archive_prescription_job --job-id 42
"""

import logging
import os
import shutil

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.utils import timezone

from pbs.prescription.models import JobQueue, Prescription
from pbs.utils import pdflatex

logger = logging.getLogger('pdf_debugging')


def handle_archive_prescription_job(job, stdout=None):
    """Generate the PDF archive for an archive_prescription queue entry.

    Called by the generic queue worker dispatcher and by the standalone
    management command. ``stdout`` is the management command's stdout stream
    for progress messages; pass None to suppress output.
    """
    prescription = job.prescription
    if not isinstance(prescription, Prescription):
        _fail_job(job, 'Archive job prescription is missing or is not a Prescription')
        return

    archive_name = job.payload.get('archive_name')
    if not archive_name:
        _fail_job(job, 'Archive job payload is missing archive_name')
        return

    now = timezone.now()
    try:
        with pdflatex(
            prescription,
            template='pfp',
            downloadname=archive_name,
            embed=True,
            headers=True,
            title='Prescribed Fire Plan'
        ) as pdfresult:
            logger.debug(pdfresult.__dict__)

            if not pdfresult.succeed:
                raise Exception(pdfresult.errormessage or 'Unknown PDF generation error')

            directory = os.path.join(
                settings.MEDIA_ROOT,
                'snapshots',
                prescription.financial_year.replace('/', '-'),
                prescription.burn_id
            )
            if not os.path.exists(directory):
                os.makedirs(directory)

            source_file = pdfresult.pdf_file
            destination = os.path.join(directory, '{0}.pdf'.format(archive_name))
            shutil.copyfile(source_file, destination)
            os.remove(source_file)

            job.status = JobQueue.STATUS_SUCCEEDED
            job.finished_at = timezone.now()
            job.save(update_fields=['status', 'finished_at', 'updated_at'])

            Prescription.objects.filter(pk=prescription.pk).update(
                archive_in_progress=False,
                archive_successful=True,
            )

            _send_requester_email(
                job=job,
                prescription=prescription,
                succeeded=True,
                local_time=timezone.localtime(now),
            )
    except Exception as exc:
        _fail_archive_prescription_job(job, prescription, now, exc)


def _fail_archive_prescription_job(job, prescription, now, exc):
    """Persist failure state for a prescription archive job and notify users."""
    title = 'PDF production failed when attempting to archive Prescription: {0}'.format(prescription)
    logger.warning(title)
    logger.exception(exc)

    job.status = JobQueue.STATUS_FAILED
    job.finished_at = timezone.now()
    job.error_message = str(exc)
    job.save(update_fields=['status', 'finished_at', 'error_message', 'updated_at'])

    Prescription.objects.filter(pk=prescription.pk).update(
        archive_in_progress=False,
        archive_successful=False,
    )

    _send_requester_email(
        job=job,
        prescription=prescription,
        succeeded=False,
        local_time=timezone.localtime(now),
        error=str(exc),
    )

    if settings.NOTIFICATION_EMAIL:
        local_time = timezone.localtime(now)
        email_from = settings.FEX_MAIL
        message = (
            'An attempt was made to create an archive for Prescription: {0} at {1}. \n\n'
            'The archive attempt failed to generate the required pdf.\n\n'
            'Queue job id: {2}\n'
            'Job type: {3}\n'
            'Dedupe key: {4}\n'
            'Error: {5}'
        ).format(prescription, local_time, job.id, job.job_type, job.dedupe_key, job.error_message)
        email_instance = settings.EMAIL_INSTANCE if hasattr(settings, 'EMAIL_INSTANCE') else ''
        systemid = settings.SYSTEM_ID if hasattr(settings, 'SYSTEM_ID') else ''
        headers = {
            'System-Environment': email_instance,
            'ITSystem-ID': systemid + '-' + email_instance,
        }
        # send_mail(title, message, email_from, settings.NOTIFICATION_EMAIL.split(','), fail_silently=True)
        email = EmailMessage(
            subject=title,
            body=message,
            from_email=email_from,
            to=settings.NOTIFICATION_EMAIL.split(','),
            headers=headers,
        )
        email.send(fail_silently=True)
    else:
        logger.warning('ENV NOTIFICATION_EMAIL is not set. Unable to send notification email.')


def _fail_job(job, error_message):
    """Mark a job as failed when it cannot be validated."""
    logger.warning(error_message)
    job.status = JobQueue.STATUS_FAILED
    job.finished_at = timezone.now()
    job.error_message = error_message
    job.save(update_fields=['status', 'finished_at', 'error_message', 'updated_at'])


def _send_requester_email(job, prescription, succeeded, local_time, error=None):
    """Notify the user who requested the job that archive processing finished."""
    if not job.requested_by or not job.requested_by.email:
        return

    recipient = job.requested_by.email
    email_from = settings.FEX_MAIL
    payload = job.payload or {}

    if succeeded:
        subject = 'PBS \u2013 Archive generated for Prescription {0}'.format(prescription.burn_id)
        message = (
            'Hi {first_name},\n\n'
            'The PDF archive for Prescription {burn_id} has been generated successfully at {time}.\n\n'
            'Archive name: {archive_name}\n'
            'Status change: {changed_status} changed from "{prev}" to "{new}".'
        ).format(
            first_name=job.requested_by.first_name or job.requested_by.username,
            burn_id=prescription.burn_id,
            time=local_time,
            archive_name=payload.get('archive_name', job.dedupe_key),
            changed_status=payload.get('changed_status', ''),
            prev=payload.get('previous_status', ''),
            new=payload.get('new_status', ''),
        )
    else:
        subject = 'PBS \u2013 Archive generation FAILED for Prescription {0}'.format(prescription.burn_id)
        message = (
            'Hi {first_name},\n\n'
            'The PDF archive for Prescription {burn_id} FAILED to generate at {time}.\n\n'
            'Archive name: {archive_name}\n'
            'Status change: {changed_status} changed from "{prev}" to "{new}".\n\n'
            'Error: {error}\n\n'
            'The prescription has been locked. Please contact an administrator.'
        ).format(
            first_name=job.requested_by.first_name or job.requested_by.username,
            burn_id=prescription.burn_id,
            time=local_time,
            archive_name=payload.get('archive_name', job.dedupe_key),
            changed_status=payload.get('changed_status', ''),
            prev=payload.get('previous_status', ''),
            new=payload.get('new_status', ''),
            error=error or 'Unknown',
        )

    try:
        email_instance = settings.EMAIL_INSTANCE if hasattr(settings, 'EMAIL_INSTANCE') else ''
        systemid = settings.SYSTEM_ID if hasattr(settings, 'SYSTEM_ID') else ''
        headers = {
            'System-Environment': email_instance,
            'ITSystem-ID': systemid + '-' + email_instance,
        }
        # send_mail(subject, message, email_from, [recipient], fail_silently=False)
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=email_from,
            to=[recipient],
            headers=headers,
        )
        email.send(fail_silently=False)
    except Exception:
        logger.exception(
            'Failed to send archive completion email to %s for prescription %s',
            recipient, prescription.burn_id
        )


class Command(BaseCommand):
    """Process a specific archive_prescription job by its JobQueue ID.

    Useful for manually retrying a failed job or processing a specific job
    without waiting for the queue worker. The job is set to STATUS_PROCESSING
    before the handler runs, so a concurrent queue worker will skip it.

    Example:
        python manage.py process_archive_prescription_job --job-id 42
    """

    help = 'Process a specific archive_prescription job by its JobQueue ID'

    def add_arguments(self, parser):
        parser.add_argument(
            '--job-id',
            type=int,
            required=True,
            help='ID of the JobQueue entry to process.',
        )

    def handle(self, *args, **options):
        job_id = options['job_id']
        try:
            job = JobQueue.objects.get(pk=job_id)
        except JobQueue.DoesNotExist:
            self.stderr.write(self.style.ERROR('JobQueue entry {0} not found.'.format(job_id)))
            return

        if job.job_type != JobQueue.TYPE_ARCHIVE_PRESCRIPTION:
            self.stderr.write(self.style.ERROR(
                'Job {0} has type "{1}", expected "{2}".'.format(
                    job_id, job.job_type, JobQueue.TYPE_ARCHIVE_PRESCRIPTION)
            ))
            return

        job.status = JobQueue.STATUS_PROCESSING
        job.started_at = timezone.now()
        job.attempts = (job.attempts or 0) + 1
        job.error_message = None
        job.save(update_fields=['status', 'started_at', 'attempts', 'error_message', 'updated_at'])

        self.stdout.write('Processing job {0} ({1}) ...'.format(job.id, job.dedupe_key))
        handle_archive_prescription_job(job, stdout=self.stdout)
        # Reload to get the final status set by the handler.
        job.refresh_from_db(fields=['status'])
        self.stdout.write(self.style.SUCCESS(
            'Job {0} finished with status: {1}'.format(job.id, job.status)
        ))
