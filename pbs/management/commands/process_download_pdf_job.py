"""Handler and management command for download_pdf queue jobs."""

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from pbs.prescription.models import JobQueue, Prescription
from pbs.utils.pdf import process_download_pdf_job

logger = logging.getLogger('pdf_debugging')


def _finish_job(job, succeeded, error_message=None):
    job.status = JobQueue.STATUS_SUCCEEDED if succeeded else JobQueue.STATUS_FAILED
    job.finished_at = timezone.now()
    job.error_message = None if succeeded else error_message
    job.save(update_fields=['status', 'finished_at', 'error_message', 'updated_at'])


def handle_download_pdf_job(job, stdout=None):
    """Create the PDF and email the download link to the requester."""
    if not isinstance(job.prescription, Prescription):
        _finish_job(job, False, 'Download PDF job prescription is missing or is not a Prescription')
        return
    payload = job.payload or {}
    if not payload.get('baseurl') or not payload.get('downloadname'):
        _finish_job(job, False, 'Download PDF job payload is missing baseurl or downloadname')
        return

    try:
        succeeded, error = process_download_pdf_job(job)
    except Exception as exc:
        logger.exception('Download PDF job %s failed', job.id)
        _finish_job(job, False, str(exc))
        return

    _finish_job(job, succeeded, error)
    if stdout:
        stdout.write('Download PDF job {0} {1}.'.format(job.id, 'succeeded' if succeeded else 'failed'))


class Command(BaseCommand):
    """Process a specific download_pdf job by its JobQueue ID."""

    help = 'Process a specific download_pdf job by its JobQueue ID'

    def add_arguments(self, parser):
        parser.add_argument('--job-id', type=int, required=True, help='ID of the JobQueue entry to process.')

    def handle(self, *args, **options):
        job_id = options['job_id']
        try:
            job = JobQueue.objects.get(pk=job_id)
        except JobQueue.DoesNotExist:
            self.stderr.write(self.style.ERROR('JobQueue entry {0} not found.'.format(job_id)))
            return

        if job.job_type != JobQueue.TYPE_DOWNLOAD_PDF:
            self.stderr.write(self.style.ERROR(
                'Job {0} has type "{1}", expected "{2}".'.format(
                    job_id, job.job_type, JobQueue.TYPE_DOWNLOAD_PDF)
            ))
            return

        job.status = JobQueue.STATUS_PROCESSING
        job.started_at = timezone.now()
        job.attempts = (job.attempts or 0) + 1
        job.error_message = None
        job.save(update_fields=['status', 'started_at', 'attempts', 'error_message', 'updated_at'])
        handle_download_pdf_job(job, stdout=self.stdout)
        job.refresh_from_db(fields=['status'])
        self.stdout.write(self.style.SUCCESS('Job {0} finished with status: {1}'.format(job.id, job.status)))
