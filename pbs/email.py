import logging
from smtplib import SMTPException

from wagov_utils.components.utils.email import TemplateEmailBase


logger = logging.getLogger('pbs')


class PlainTextEmail(TemplateEmailBase):
    html_template = None
    txt_template = 'pbs/emails/body.txt'

    def send(self, to_addresses, from_address=None, context=None, attachments=None,
             cc=None, bcc=None, headers=None, fail_silently=False):
        if not (to_addresses or cc or bcc):
            if fail_silently:
                logger.warning('Email has no recipients for subject: %s', self.subject)
                return False
            raise SMTPException('Email has no recipients.')
        result = super().send(
            to_addresses, from_address=from_address, context=context,
            attachments=attachments, cc=cc, bcc=bcc, headers=headers,
        )
        if not result:
            if fail_silently:
                logger.warning('Email delivery was disabled or failed for subject: %s', self.subject)
                return result
            raise SMTPException('Email delivery was disabled or failed; see email log for details.')
        return result


class HtmlEmail(PlainTextEmail):
    html_template = 'pbs/emails/body.txt'
