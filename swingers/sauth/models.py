from django.conf import settings
from django.utils import timezone
# from django.utils.encoding import python_2_unicode_compatible

from swingers import models
from swingers.models import Audit
from swingers.utils.auth import make_nonce

from model_utils import Choices

from reversion import revision

import threading
import requests
import hashlib


class Job(models.Model):
    STATES = Choices("queued", "running", "completed")
    name = models.CharField(max_length=320, unique=True)
    args = models.TextField(null=True, blank=True)
    output = models.TextField(null=True, blank=True)
    state = models.CharField(choices=STATES, default=STATES.queued,
                             max_length=64)

    class Meta:
        app_label = 'swingers'


class ApplicationLink(models.Audit):
    AUTH_METHOD = Choices('basic', 'md5', 'sha1', 'sha224', 'sha256', 'sha384',
                          'sha512')
    client_name = models.CharField(
        max_length=320,
        help_text="project/host of client, this app is {0}".format(
            settings.SITE_NAME))
    server_name = models.CharField(
        max_length=320,
        help_text="project/host of server, this app is {0}".format(
            settings.SITE_NAME))
    server_url = models.TextField(
        help_text="URL service backend requests should be made to")
    identifier = models.CharField(
        max_length=320, null=True, blank=True,
        help_text="IP or Hostname, optional for added security")
    secret = models.CharField(max_length=320, help_text="Application secret")
    timeout = models.IntegerField(default=600,
                                  help_text="Timeout of oauth tokens in "
                                            "seconds")
    auth_method = models.CharField(choices=AUTH_METHOD,
                                   default=AUTH_METHOD.sha256, max_length=20)

    class Meta(Audit.Meta):
        unique_together = ("client_name", "server_name")
        app_label = 'swingers'

    def natural_key(self):
        return (self.client_name, self.server_name)

    def get_by_natural_key(self, client_name, server_name):
        return self.get(client_name=client_name, server_name=server_name)

    def get_access_token(self, user_id, expires=600):
        """
        Returns an access token for with the current user.

        Note: uses a hardcoded URL when determining where to send the request.
        """
        url = self.server_url + "/api/swingers/v1/{0}/request_token"
        nonce = make_nonce()
        r = requests.get(url.format(self.server_name), params={
            "user_id": user_id,
            "nonce": nonce,
            "client_secret": self.get_client_secret(user_id, nonce),
            "client_id": self.client_name,
            "expires": expires
        })
        if r.ok:
            return r.content
        else:
            r.raise_for_status()

    def get_client_secret(self, user_id, nonce):
        """
        Returns the client secret based on a user and a nonce.
        """
        stringtohash = "{0}{1}{2}".format(self.secret, user_id, nonce)
        return getattr(hashlib, self.auth_method)(stringtohash).hexdigest()



class Token(models.Model):
    link = models.ForeignKey(ApplicationLink)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="%(app_label)s_%(class)s_user",
        help_text="User token authenticates as")
    url = models.TextField(help_text="Suburl this token is restricted to, "
                           "relative e.g. (/my/single/service/entrypoint)",
                           default="/")
    secret = models.CharField(max_length=320, help_text="Token Secret",
                              unique=True)
    modified = models.DateTimeField(default=timezone.now, editable=False)
    timeout = models.IntegerField(default=600, help_text="Timeout token in "
                                  "seconds, 0 means never times out")

    class Meta:
        app_label = 'swingers'

    def save(self, *args, **kwargs):
        try:
            revision.unregister(self.__class__)
        except:
            pass
        super(Token, self).save(*args, **kwargs)

    def natural_key(self):
        return (self.secret, )

    def get_by_natural_key(self, secret):
        return self.get(secret=secret)

    def __str__(self):
        return "{0} - {1}:{2}@{3}".format(self.pk, self.user, self.secret,
                                          self.link.client_name)[:320]
