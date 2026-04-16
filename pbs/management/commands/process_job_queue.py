import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from pbs.prescription.models import JobQueue
from pbs.management.commands.process_archive_prescription_job import handle_archive_prescription_job

logger = logging.getLogger('pdf_debugging')


class Command(BaseCommand):
    """Process queued jobs from the general-purpose job queue.

    Jobs are claimed one-by-one using SELECT FOR UPDATE SKIP LOCKED so multiple
    worker processes can run safely without double-processing the same row.
    Each job type is dispatched to a dedicated handler method.
    """

    help = 'Process queued jobs from the shared PBS job queue'

    def add_arguments(self, parser):
        """Define command line options for queue processing."""
        parser.add_argument(
            '--max-jobs',
            type=int,
            default=1,
            help='Maximum queued jobs to process in this run (default: 1).'
        )
        parser.add_argument(
            '--job-type',
            default=None,
            help='Optional job_type filter, e.g. archive_prescription.'
        )

    def handle(self, *args, **options):
        """Claim and process up to max_jobs queued jobs, then exit."""
        max_jobs = max(1, int(options.get('max_jobs') or 1))
        job_type = options.get('job_type') or None
        processed = 0

        for _ in range(max_jobs):
            job = self._claim_next_job(job_type=job_type)
            if not job:
                break
            self._process_job(job)
            processed += 1

        self.stdout.write('Processed {0} job(s).'.format(processed))

    def _claim_next_job(self, job_type=None):
        """Atomically claim the next queued job, optionally filtered by type."""
        with transaction.atomic():
            jobs = JobQueue.objects.select_for_update(skip_locked=True)
            jobs = jobs.filter(status=JobQueue.STATUS_QUEUED)
            if job_type:
                jobs = jobs.filter(job_type=job_type)

            job = jobs.order_by('requested_at', 'id').first()
            if not job:
                return None

            job.status = JobQueue.STATUS_PROCESSING
            job.started_at = timezone.now()
            job.attempts = (job.attempts or 0) + 1
            job.error_message = None
            job.save(update_fields=['status', 'started_at', 'attempts', 'error_message', 'updated_at'])
            return job

    def _process_job(self, job):
        """Dispatch the claimed job to its type-specific handler."""
        handlers = {
            JobQueue.TYPE_ARCHIVE_PRESCRIPTION: self._process_archive_prescription,
        }
        handler = handlers.get(job.job_type)
        if not handler:
            self._fail_job(job, 'Unsupported job type: {0}'.format(job.job_type))
            return
        handler(job)

    def _process_archive_prescription(self, job):
        """Delegate to the archive_prescription handler module."""
        handle_archive_prescription_job(job, stdout=self.stdout)

    def _fail_job(self, job, error_message):
        """Mark a generic job as failed when it cannot be dispatched or validated."""
        logger.warning(error_message)
        job.status = JobQueue.STATUS_FAILED
        job.finished_at = timezone.now()
        job.error_message = error_message
        job.save(update_fields=['status', 'finished_at', 'error_message', 'updated_at'])