from django.contrib.auth import get_user_model
from django_auth_ldap.backend import LDAPBackend
from django_browserid.auth import BrowserIDBackend
from guardian.backends import ObjectPermissionBackend

User = get_user_model()


class PersonaBackend(BrowserIDBackend):
    def filter_users_by_email(self, email):
        """Return all users matching the specified email."""
        return User.objects.filter(email__iexact=email)


class EmailBackend(ObjectPermissionBackend):
    """
    An authentication backend to handle user requirements in DPaW. Performs a
    number of functions.

    It will authenticate a user against LDAP if it can't find a user entry in
    the database, and will allow users to login with their DPaW emails.

    It also handles object permissions through guardian's object permission
    framework.
    """
    def authenticate(self, username=None, password=None):
        """
        Attempt to authenticate a particular user. The username field is taken
        to be an email address and checked against LDAP if the user cannot
        be found.

        Always returns an instance of `django.contrib.auth.models.User` on
        success, otherwise returns None.
        """
        if password is None:
            return None
        try:
            user = User.objects.get(email__iexact=username)
            if user.check_password(password):
                return user
            else:
                try:
                    ldapauth = LDAPBackend()
                    return ldapauth.authenticate(username=user.username,
                                                 password=password)
                except:
                    return None
        except User.DoesNotExist:
            try:
                ldapauth = LDAPBackend()
                user = ldapauth.authenticate(username=username, password=password)
                if user is None:
                    return None

                first_name = user.first_name
                last_name = user.last_name
                email = user.email
                if email:
                    if User.objects.filter(email__iexact=email).count() > 1:
                        user.delete()
                    user = User.objects.get(email__iexact=email)
                    user.first_name, user.last_name = first_name, last_name
                    user.save()
                else:
                    user = User.objects.get(username=username)
                    user.first_name, user.last_name = first_name, last_name
                    user.save()
                return user
            except Exception as e:
                print(e)
                return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
