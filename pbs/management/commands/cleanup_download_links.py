import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from pbs.models import FileDownloadHash

logger = logging.getLogger('download_link_cleanup')


class Command(BaseCommand):
    help = 'Remove expired private download links from the database'

    def handle(self, *args, **options):
        now = timezone.now()
        expired_links = FileDownloadHash.objects.filter(expires_at__lte=now)
        expired_count = expired_links.count()

        if not expired_count:
            self.stdout.write('No expired download links found.')
            return

        logger.info('Deleting %s expired private download link(s).', expired_count)
        expired_links.delete()
        self.stdout.write('Deleted {0} expired download link(s).'.format(expired_count))