import logging

from django.contrib.auth.forms import PasswordResetForm
from django.template import loader

from pbs.email import PlainTextEmail


logger = logging.getLogger('django.contrib.auth')


class LoggedPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name, context,
                  from_email, to_email, html_email_template_name=None):
        subject = loader.render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)
        email_kwargs = {}
        email_context = {'body': body}
        if html_email_template_name is not None:
            email_context['html_body'] = loader.render_to_string(html_email_template_name, context)
            email_kwargs['html_template'] = 'pbs/emails/html_body.txt'

        # Django's PasswordResetForm.send_mail() uses EmailMultiAlternatives directly.
        # super().send_mail(subject_template_name, email_template_name, context,
        #                   from_email, to_email, html_email_template_name)
        try:
            PlainTextEmail(subject=subject, **email_kwargs).send(
                [to_email], from_address=from_email, context=email_context,
            )
        except Exception:
            logger.exception('Failed to send password reset email to %s', context['user'].pk)
