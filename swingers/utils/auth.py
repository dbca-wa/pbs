from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from django.utils import timezone
from django.contrib.auth.models import User
from django.core.cache import cache
from django.conf import settings

# from django_auth_ldap.backend import LDAPBackend, _LDAPUser

import hashlib
import warnings


def make_nonce():
    """
    Generate a unique nonce for use in token generation.
    """
    return hashlib.md5(timezone.now().isoformat()).hexdigest()[:10]


def retrieve_access_token(request, service):
    """
    Returns url, access_token for a service and request.
    Service should be a string representing a service to connect to.
    System will introspect settings.SITE_NAME to find service.
    Probably issues if more than one link, will default to using latest
    modified.
    """
    from swingers.sauth.models import ApplicationLink
    link = ApplicationLink.objects.get(server_name=service)
    url = link.server_url
    access_token = link.get_access_token(request.user.username)
    return url, access_token


def get_or_create_local_user(user):
    """
    Create a local user if the username exists in the configured LDAP server.
    Returns the updated or newly created local django.contrib.auth.models.User
    """
    warnings.warn('This is most likely going to be deprecated due to upcoming'
                  'demerger work', PendingDeprecationWarning)

    # instantiate the LDAPBackend model class
    # magically finds the LDAP server from settings.py
    # ldap_backend = LDAPBackend()

    # if user.find('@') != -1:
    #     ldap_user = _LDAPUser(ldap_backend, username="")

    #     result = ldap_user.connection.search_s(
    #         "dc=corporateict,dc=domain", scope=ldap_backend.ldap.SCOPE_SUBTREE,
    #         filterstr='(mail=' + user + ')',
    #         attrlist=[str("sAMAccountName").encode('ASCII')]
    #     )
    #     if result:
    #         user = result[0][1]["sAMAccountName"][0].lower()
    #     else:
    #         return None

    # try:
    #     user = User.objects.get(username=user)
    # except User.DoesNotExist:
    #     user = ldap_backend.populate_user(user)

    # return user
    return None


def validate_request(data, expires=600):
    """
    validates a dictionary of request data and returns a User,
    ApplicationLink and token expiry time
    """
    # from swingers.sauth.models import ApplicationLink
    # # sanity check the dictionary
    # for key in ["client_id", "client_secret", "user_id"]:
    #     if not key in data:
    #         raise Exception("Missing Input")

    # # set default expiry to 10 mins unless specified
    # # 0 means never expires
    # if "expires" in data:
    #     expires = int(data["expires"])

    # # Try and find the user for the user_id
    # ldapbackend = LDAPBackend()
    # user = data["user_id"]
    # if User.objects.filter(username=user):
    #     user = User.objects.get(username=user)
    # else:
    #     try:
    #         ldapbackend.populate_user(user)
    #         user = User.objects.get(username=user)
    #     except:
    #         raise Exception("Invalid user_id")
    # # Try and find the client_id
    # try:
    #     link = ApplicationLink.objects.get(client_name=data["client_id"],
    #                                        server_name=settings.SERVICE_NAME)
    # except ApplicationLink.DoesNotExist:
    #     raise Exception("Application link does not exist")
    # # Validate the secret
    # if link.auth_method == ApplicationLink.AUTH_METHOD.basic:
    #     client_secret = link.secret
    # elif "nonce" in data:
    #     if cache.get(link.secret) == data["nonce"]:
    #         raise Exception("No you can't reuse nonce's!")
    #     cache.set(link.secret, data["nonce"], expires)
    #     # client_secret should be hexdigest, hash algorithm selected based on
    #     # application link
    #     client_secret = link.get_client_secret(data["user_id"], data["nonce"])
    # else:
    #     raise Exception("Missing nonce")
    # if not client_secret == data["client_secret"]:
    #     raise Exception("Invalid client_secret")
    # return user, link, expires
    return None
