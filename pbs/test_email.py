import os
import tempfile
from smtplib import SMTPException
from types import SimpleNamespace
from unittest.mock import patch

from django.core import mail
from django.test import SimpleTestCase, override_settings
from django.urls import resolve

from pbs.email import HtmlEmail, PlainTextEmail
from pbs.management.commands.process_archive_prescription_job import _send_requester_email as send_archive_email
from pbs.management.commands.process_carry_over_prescription_job import _send_requester_email
from pbs.password_reset import LoggedPasswordResetForm
from pbs.prescription.management.commands.monitor_prescription_archives import Command as MonitorCommand
from pbs.review.management.commands.updatelayers import Command as LayersCommand
from pbs.utils import support_email
from pbs.utils.pdf import _send_download_email


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    EMAIL_DELIVERY='on',
    EMAIL_INSTANCE='TEST',
)
class TemplateEmailTests(SimpleTestCase):
    def setUp(self):
        self.base_dir = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(override_settings(BASE_DIR=self.base_dir))

    def test_download_email_preserves_text_and_logs_recipients(self):
        _send_download_email(
            SimpleNamespace(email='recipient@example.com'),
            'Download', 'First line\nA & B < C',
        )

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['recipient@example.com'])
        self.assertEqual(message.subject, 'Download')
        self.assertEqual(message.body, 'First line\nA & B < C')
        self.assertEqual(message.extra_headers['System-Environment'], 'TEST')
        self.assertNotIn('ITSystem-ID', message.extra_headers)
        self.assertEqual(message.alternatives, [])
        with open(os.path.join(self.base_dir, 'logs', 'email.log')) as log:
            contents = log.read()
        self.assertIn('Download', contents)
        self.assertIn('recipient@example.com', contents)
        self.assertIn('Successfully sent to mail gateway', contents)

    def test_support_email_preserves_html(self):
        with override_settings(SUPPORT_EMAIL=['support@example.com']):
            support_email('Example', '<strong>Details</strong>')
        self.assertEqual(mail.outbox[0].to, ['support@example.com'])
        self.assertEqual(mail.outbox[0].alternatives[0].mimetype, 'text/html')
        self.assertIn('<strong>Details</strong>', mail.outbox[0].alternatives[0].content)

    def test_monitoring_email_keeps_csv_attachment(self):
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv') as csv_file:
            csv_file.write('Prescription,Issue\nABC,Missing\n')
            csv_file.flush()
            with override_settings(NOTIFICATION_EMAIL='one@example.com,two@example.com'):
                MonitorCommand().send_monitoring_email([{'prescription': 'ABC'}], csv_file)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['one@example.com', 'two@example.com'])
        self.assertEqual(len(message.attachments), 1)
        self.assertEqual(message.attachments[0].content, 'Prescription,Issue\nABC,Missing\n')
        self.assertEqual(message.attachments[0].mimetype, 'text/csv')

    def test_carry_over_requester_email(self):
        user = SimpleNamespace(email='user@example.com', first_name='User', username='user')
        job = SimpleNamespace(requested_by=user, payload={'archive_name': 'archive'}, dedupe_key='job')
        _send_requester_email(job, SimpleNamespace(burn_id='ABC'), True, 'today')
        self.assertEqual(mail.outbox[0].to, ['user@example.com'])
        self.assertIn('Carry-over completed', mail.outbox[0].subject)
        self.assertIn('archive', mail.outbox[0].body)

    def test_archive_requester_email(self):
        user = SimpleNamespace(email='user@example.com', first_name='User', username='user')
        job = SimpleNamespace(requested_by=user, payload={'archive_name': 'archive'}, dedupe_key='job')
        send_archive_email(job, SimpleNamespace(burn_id='ABC'), True, 'today')
        self.assertEqual(mail.outbox[0].to, ['user@example.com'])
        self.assertIn('Archive generated', mail.outbox[0].subject)
        self.assertIn('archive', mail.outbox[0].body)

    def test_layer_summary_email(self):
        with override_settings(ERROR_NOTIFICATION_EMAIL='one@example.com, two@example.com'):
            LayersCommand()._send_summary_email(['An error'], ['A file'], 1, 2, 3)
        self.assertEqual(mail.outbox[0].to, ['one@example.com', 'two@example.com'])
        self.assertIn('An error', mail.outbox[0].body)
        self.assertIn('A file', mail.outbox[0].body)

    def test_non_production_smtp_routing(self):
        with override_settings(
            EMAIL_BACKEND='wagov_utils.components.utils.email_backend.EmailBackend',
            PRODUCTION_EMAIL=False, NON_PROD_EMAIL='safe@example.com',
        ), patch('smtplib.SMTP') as smtp:
            PlainTextEmail(subject='Test').send(
                ['original@example.com'], from_address='sender@example.com',
                context={'body': 'Body'},
            )
        args = smtp.return_value.sendmail.call_args.args
        self.assertEqual(args[1], ['safe@example.com'])
        self.assertIn(b'Subject: Test TEST', args[2])
        with open(os.path.join(self.base_dir, 'logs', 'email.log')) as log:
            self.assertIn('original@example.com', log.read())

    def test_password_reset_uses_logged_email_and_preserves_templates(self):
        templates = [{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'OPTIONS': {'loaders': [('django.template.loaders.locmem.Loader', {
                'subject': 'Reset\npassword',
                'text': 'Hello {{ name }}: {{ token }}',
                'html': '<b>{{ name }}</b>',
                'pbs/emails/body.txt': '{{ body|safe }}',
                'pbs/emails/html_body.txt': '{{ html_body|safe }}',
            })]},
        }]
        self.assertIs(resolve('/password_reset/').func.view_initkwargs['form_class'], LoggedPasswordResetForm)
        with override_settings(TEMPLATES=templates):
            LoggedPasswordResetForm().send_mail(
                'subject', 'text',
                {'name': 'Alice', 'token': 'secret-token', 'user': SimpleNamespace(pk=1)},
                'sender@example.com', 'user@example.com', html_email_template_name='html',
            )
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'Resetpassword')
        self.assertEqual(message.body, 'Hello Alice: secret-token')
        self.assertEqual(message.alternatives[0].content, '<b>Alice</b>')
        with open(os.path.join(self.base_dir, 'logs', 'email.log')) as log:
            self.assertNotIn('secret-token', log.read())

    def test_delivery_off_is_reported_as_failure(self):
        with override_settings(EMAIL_DELIVERY='off'):
            with self.assertRaises(SMTPException):
                PlainTextEmail(subject='Disabled').send(
                    ['recipient@example.com'], context={'body': 'Body'},
                )
        self.assertEqual(len(mail.outbox), 0)

    def test_missing_recipients_are_reported_as_failure(self):
        with self.assertRaises(SMTPException):
            PlainTextEmail(subject='Missing').send([], context={'body': 'Body'})

    def test_backend_failure_is_reported_and_logged(self):
        with patch(
            'django.core.mail.backends.locmem.EmailBackend.send_messages',
            side_effect=SMTPException('mail server unavailable'),
        ):
            with self.assertRaises(SMTPException):
                HtmlEmail(subject='Failure').send(
                    ['recipient@example.com'], context={'body': 'Body'},
                )
        with open(os.path.join(self.base_dir, 'logs', 'email.log')) as log:
            self.assertIn('Error Sending - mail server unavailable', log.read())

    def test_silent_failure_is_logged(self):
        with patch(
            'django.core.mail.backends.locmem.EmailBackend.send_messages',
            side_effect=SMTPException('mail server unavailable'),
        ), self.assertLogs('pbs', level='WARNING') as logs:
            result = PlainTextEmail(subject='Failure').send(
                ['recipient@example.com'], context={'body': 'Body'}, fail_silently=True,
            )
        self.assertIsNone(result)
        self.assertIn('Email delivery was disabled or failed', logs.output[0])
