"""Handler and management command for carry_over_prescription queue jobs."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from pbs.prescription.actions import _apply_carry_over_changes, _archive_prescription_for_carry_over
from pbs.prescription.models import JobQueue, Prescription
from pbs.sites import site

logger = logging.getLogger('pdf_debugging')


def handle_carry_over_prescription_job(job, stdout=None):
    """Archive the current prescription PDF, then complete the carry-over."""
    prescription = job.prescription
    if not isinstance(prescription, Prescription):
        _fail_job(job, 'Carry-over job prescription is missing or is not a Prescription')
        return

    archive_name = job.payload.get('archive_name') if job.payload else None
    if not archive_name:
        _fail_job(job, 'Carry-over job payload is missing archive_name')
        return

    archive_completed = False
    now = timezone.now()
    try:
        _archive_prescription_for_carry_over(prescription, archive_name)
        archive_completed = True
        _apply_carry_over_changes(
            prescription,
            admin_site=site,
            user=job.requested_by,
        )

        job.status = JobQueue.STATUS_SUCCEEDED
        job.finished_at = timezone.now()
        job.save(update_fields=['status', 'finished_at', 'updated_at'])

        Prescription.objects.filter(pk=prescription.pk).update(archive_in_progress=False)
        _send_requester_email(
            job=job,
            prescription=prescription,
            succeeded=True,
            local_time=timezone.localtime(now),
        )
        if stdout:
            stdout.write('Completed carry-over job {0} for {1}.'.format(job.id, prescription.burn_id))
    except Exception as exc:
        _fail_carry_over_prescription_job(
            job=job,
            prescription=prescription,
            now=now,
            exc=exc,
            archive_completed=archive_completed,
        )


def _fail_carry_over_prescription_job(job, prescription, now, exc, archive_completed):
    """Persist failure state for a carry-over job."""
    title = 'Carry-over job failed for Prescription: {0}'.format(prescription)
    logger.warning(title)
    logger.exception(exc)

    job.status = JobQueue.STATUS_FAILED
    job.finished_at = timezone.now()
    job.error_message = str(exc)
    job.save(update_fields=['status', 'finished_at', 'error_message', 'updated_at'])

    update_values = {
        'archive_in_progress': False,
    }
    if not archive_completed:
        update_values['archive_successful'] = False
    Prescription.objects.filter(pk=prescription.pk).update(**update_values)

    _send_requester_email(
        job=job,
        prescription=prescription,
        succeeded=False,
        local_time=timezone.localtime(now),
        error=str(exc),
    )


def _fail_job(job, error_message):
    """Mark a job as failed when it cannot be validated."""
    logger.warning(error_message)
    job.status = JobQueue.STATUS_FAILED
    job.finished_at = timezone.now()
    job.error_message = error_message
    job.save(update_fields=['status', 'finished_at', 'error_message', 'updated_at'])


def _send_requester_email(job, prescription, succeeded, local_time, error=None):
    """Notify the user who requested the job that carry-over processing finished."""
    if not job.requested_by or not job.requested_by.email:
        return

    recipient = job.requested_by.email
    email_from = settings.FEX_MAIL
    payload = job.payload or {}

    if succeeded:
        subject = 'PBS – Carry-over completed for Prescription {0}'.format(prescription.burn_id)
        message = (
            'Hi {first_name},\n\n'
            'The carry-over for Prescription {burn_id} completed successfully at {time}.\n\n'
            'Archive name: {archive_name}\n'
            # 'Job id: {job_id}\n'
            # 'Job key: {dedupe_key}'
        ).format(
            first_name=job.requested_by.first_name or job.requested_by.username,
            burn_id=prescription.burn_id,
            time=local_time,
            archive_name=payload.get('archive_name', job.dedupe_key),
            # job_id=job.id,
            # dedupe_key=job.dedupe_key,
        )
    else:
        subject = 'PBS – Carry-over FAILED for Prescription {0}'.format(prescription.burn_id)
        message = (
            'Hi {first_name},\n\n'
            'The carry-over for Prescription {burn_id} FAILED at {time}.\n\n'
            'Archive name: {archive_name}\n'
            'Job id: {job_id}\n'
            'Job key: {dedupe_key}\n'
            'Error: {error}\n\n'
            'Please contact an administrator.'
        ).format(
            first_name=job.requested_by.first_name or job.requested_by.username,
            burn_id=prescription.burn_id,
            time=local_time,
            archive_name=payload.get('archive_name', job.dedupe_key),
            job_id=job.id,
            dedupe_key=job.dedupe_key,
            error=error or 'Unknown',
        )

    try:
        send_mail(subject, message, email_from, [recipient], fail_silently=False)
    except Exception:
        logger.exception(
            'Failed to send carry-over completion email to %s for prescription %s',
            recipient, prescription.burn_id
        )


class Command(BaseCommand):
    """Process a specific carry_over_prescription job by its JobQueue ID."""

    help = 'Process a specific carry_over_prescription job by its JobQueue ID'

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

        if job.job_type != JobQueue.TYPE_CARRY_OVER_PRESCRIPTION:
            self.stderr.write(self.style.ERROR(
                'Job {0} has type "{1}", expected "{2}".'.format(
                    job_id, job.job_type, JobQueue.TYPE_CARRY_OVER_PRESCRIPTION)
            ))
            return

        job.status = JobQueue.STATUS_PROCESSING
        job.started_at = timezone.now()
        job.attempts = (job.attempts or 0) + 1
        job.error_message = None
        job.save(update_fields=['status', 'started_at', 'attempts', 'error_message', 'updated_at'])

        self.stdout.write('Processing job {0} ({1}) ...'.format(job.id, job.dedupe_key))
        handle_carry_over_prescription_job(job, stdout=self.stdout)
        job.refresh_from_db(fields=['status'])
        self.stdout.write(self.style.SUCCESS(
            'Job {0} finished with status: {1}'.format(job.id, job.status)
        ))