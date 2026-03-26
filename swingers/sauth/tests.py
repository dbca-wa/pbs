from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from django.test.utils import override_settings

from swingers.sauth.backends import PersonaBackend, EmailBackend
from swingers.sauth.models import ApplicationLink, Token
from swingers.utils.auth import make_nonce

from swingers.tests.forms import DuckForm
from swingers.tests.models import Duck

from datetime import timedelta
from mock import patch

import json

User = get_user_model()


class AuditTests(TestCase):
    fixtures = ['test-users.json']
    urls = 'swingers.tests.urls'

    def test_audit_save(self):
        """
        Tests that saving an audit model updates its attributes correctly.
        """
        user = User.objects.get(username='test')
        self.client.login(username='test', password='test')
        self.client.get(reverse('test-create-duck'))
        donald = Duck.objects.get(name='donald')
        self.assertEqual(donald.creator, user)
        self.assertEqual(donald.modifier, user)

        # we need to login as a different user and create a new duck in
        # order to change _locals.request.user so that saving a duck results
        # in a different user in the modified field.
        self.client.login(username='admin', password='test')
        self.client.get(reverse('test-create-duck'), {'name': 'daffy'})
        admin = User.objects.get(username='admin')

        # test that creation time doesn't change on update and that modified
        # time does.
        created = donald.created
        modified = donald.modified
        donald.name = 'donald2'
        donald.save()
        self.assertEqual(donald.created, created)
        self.assertNotEqual(donald.modified, modified)

        # test that saving with a different user doesn't change creator, but
        # does modify modifier.
        self.assertEqual(donald.creator, user)
        self.assertEqual(donald.modifier.username, admin.username)

    def test_audit_save_outside_request(self):
        """
        Tests that model creation/modification outside of the request cycle
        results in a default user (pk=1) assigned to creation/modification.
        """
        daffy = Duck.objects.create(name='daffy')
        user = User.objects.get(pk=1)
        self.assertEqual(daffy.creator.username, user.username)
        self.assertEqual(daffy.modifier.username, user.username)

    def test_audit_save_initial_version(self):
        pass

    def test_audit_str(self):
        pass


class BrowserIDBackendTests(TestCase):
    fixtures = ['test-users']

    def test_email_identifier(self):
        backend = PersonaBackend()
        qs = User.objects.filter(email__iexact='issapps@dec.wa.gov.au')
        users = backend.filter_users_by_email('ISSAPPS@dec.wa.gov.au')
        self.assertEqual(list(users), list(qs))


class EmailBackendTests(TestCase):
    """
    Test the authentication backends included in swingers.
    """
    fixtures = ['test-users']

    def setUp(self):
        patcher = patch('swingers.sauth.backends.LDAPBackend')
        self.ldap = patcher.start()
        self.backend = EmailBackend()
        self.addCleanup(patcher.stop)

    def test_email_backend_no_password(self):
        """
        Test that attempting to authenticate with no password returns None.
        """
        instance = self.ldap.return_value
        user = self.backend.authenticate(username='issapps@dec.wa.gov.au')
        self.assertEqual(user, None)
        self.assertEqual(instance.authenticate.mock_calls, [])

    def test_email_backend_user_exists(self):
        """
        Test authenticating with a user that exists in the database.
        """
        instance = self.ldap.return_value
        user = self.backend.authenticate(username='issapps@dec.wa.gov.au',
                                         password='test')
        self.assertEqual(user.username, 'admin')
        self.assertEqual(instance.authenticate.mock_calls, [])

    def test_email_backend_password_incorrect(self):
        """
        Test that using a password that is incorrect in the database falls
        back to ldap authenticate to check against the information there.
        """
        instance = self.ldap.return_value
        instance.authenticate.return_value = User.objects.get(pk=1)
        user = self.backend.authenticate(username='issapps@dec.wa.gov.au',
                                         password='testing')
        self.assertEqual(user.username, 'admin')
        instance.authenticate.assert_called_once_with(username='admin',
                                                      password='testing')

    def test_email_backend_nonexistant_user(self):
        """
        Test authenticating as a user that doesn't exist in database, check
        that it creates a user from ldap and returns it.
        """
        instance = self.ldap.return_value

        def create_user(*args, **kwargs):
            return User.objects.create(username='test-create',
                                       password='testing',
                                       email='issapps3@dec.wa.gov.au',
                                       first_name='test', last_name='test')

        instance.authenticate.side_effect = create_user
        user = self.backend.authenticate(username='test-create',
                                         password='testing')
        self.assertEqual(user.username, 'test-create')
        instance.authenticate.assert_called_once_with(username='test-create',
                                                      password='testing')

        def create_user(*args, **kwargs):
            return User.objects.create(username='test-no-email-2',
                                       password='testing',
                                       email='issapps3@dec.wa.gov.au',
                                       first_name='test', last_name='test')

        instance.authenticate.side_effect = create_user
        user = self.backend.authenticate(username='test-create',
                                         password='testing')
        self.assertEqual(user.username, 'test-create')
        self.assertEqual(
            User.objects.filter(username='test-create').count(), 1)

    def test_email_backend_user_no_email(self):
        """
        Test authenticating as a user that doesn't exist in database, check
        that it creates a user from ldap and returns it.
        """
        instance = self.ldap.return_value

        def create_user(*args, **kwargs):
            return User.objects.create(username='test-no-email',
                                       password='testing',
                                       first_name='test', last_name='test')

        instance.authenticate.side_effect = create_user
        user = self.backend.authenticate(username='test-no-email',
                                         password='testing')
        self.assertEqual(user.username, 'test-no-email')
        instance.authenticate.assert_called_once_with(username='test-no-email',
                                                      password='testing')

    def test_email_backend_nonexistant_user_ldap(self):
        """
        Test authenticating as a user that doesn't exist in the database or in
        LDAP.
        """
        instance = self.ldap.return_value
        instance.authenticate.return_value = None
        user = self.backend.authenticate(username='test-not-there',
                                         password='testing')
        self.assertEqual(user, None)

    def test_email_backend_get_user(self):
        user = self.backend.get_user(1)
        self.assertEqual(user, User.objects.get(pk=1))
        self.assertIsNone(self.backend.get_user(99))

    def test_email_backend_ldap_auth_exception(self):
        """
        Test LDAP authenticate exception handling.
        """
        instance = self.ldap.return_value
        instance.authenticate.side_effect = Exception()
        user = self.backend.authenticate(username='issapps@dec.wa.gov.au',
                                         password='blah')
        self.assertIsNone(user)


class TokenTests(TestCase):
    """
    Tests swingers token generation views.
    """
    urls = 'swingers.tests.urls'
    fixtures = ['test-users', 'test-application-link']

    def setUp(self):
        self.client.login(username='admin', password='test')
        #patcher = patch('swingers.utils.auth.ldapbackend.populate_user')
        patcher = patch('django_auth_ldap.backend.LDAPBackend.populate_user')
        self.ldap = patcher.start()
        self.addCleanup(patcher.stop)

    def test_request_access_token(self):
        """
        Test requesting a token.
        """
        link = ApplicationLink.objects.get(pk=1)
        user = 'admin'
        nonce = make_nonce()
        url = reverse('request_access_token')
        data = {
            'user_id': user,
            'client_id': 'test',
            'client_secret': link.get_client_secret(user, nonce),
            'nonce': nonce
        }
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)
        # ensure that a token is created with the returned secret
        self.assertEqual(Token.objects.count(), 1)
        self.assertEqual(Token.objects.all()[0].secret, response.content)

        # test reusing the same nonce
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, "No you can't reuse nonce's!")
        self.assertEqual(Token.objects.count(), 1)

        # test omitting required data
        requests = [
            # missing client_secret
            {
                'user_id': 'admin',
                'client_id': 'test',
                'nonce': 'nonce'
            },
            # missing user_id
            {
                'client_id': 'test',
                'client_secret': 'secret',
                'nonce': 'nonce'
            },
            # missing client_id
            {
                'user_id': 'admin',
                'client_secret': 'secret',
                'nonce': 'nonce'
            }
        ]
        for data in requests:
            response = self.client.get(url, data)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.content, "Missing Input")

        # test missing nonce
        data = {
            'user_id': user,
            'client_id': 'test',
            'client_secret': 'missing-nonce',
        }

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, "Missing nonce")

        # test invalid secret
        data = {
            'user_id': user,
            'client_id': 'test',
            'client_secret': 'invalid-secret',
            'nonce': make_nonce()
        }

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, "Invalid client_secret")

        # test applicationlink not existing
        nonce = make_nonce()
        data = {
            'user_id': user,
            'client_id': 'invalid-client-id',
            'client_secret': link.get_client_secret(user, nonce),
            'nonce': nonce
        }

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, "Application link does not exist")

        # test expiry data
        nonce = make_nonce()
        data = {
            'user_id': user,
            'client_id': 'test',
            'client_secret': link.get_client_secret(user, nonce),
            'nonce': nonce,
            'expires': 100
        }

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)
        token = Token.objects.get(secret=response.content)
        self.assertEqual(token.timeout, 100)

        # Make sure there are only 2 tokens created.
        self.assertEqual(Token.objects.count(), 2)

        user = 'not-in-db'
        nonce = make_nonce()
        data = {
            'user_id': user,
            'client_id': 'test',
            'client_secret': link.get_client_secret(user, nonce),
            'nonce': nonce,
        }

        def create_user(*args, **kwargs):
            return User.objects.create(username=user,
                                       password='testing',
                                       email='issapps3@dec.wa.gov.au',
                                       first_name='test', last_name='test')

        self.ldap.side_effect = create_user

        response = self.client.get(url, data)

        self.ldap.assert_called_with(user)
        self.assertEqual(User.objects.get(username=user).first_name, 'test')
        self.assertEqual(response.status_code, 200)

        user = 'does-not-exist'
        self.ldap.side_effect = None
        self.ldap.return_value = None
        data['user_id'] = user
        data['nonce'] = make_nonce()
        data['client_secret'] = link.get_client_secret(user, data['nonce'])

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, "Invalid user_id")

    @override_settings(SERVICE_NAME='restless2')
    def test_request_token_basic_auth(self):
        link = ApplicationLink.objects.get(pk=2)
        user = 'admin'
        url = reverse('request_access_token')
        data = {
            'user_id': user,
            'client_id': 'test2',
            'client_secret': link.secret,
        }
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)
        # ensure that a token is created with the returned secret
        self.assertEqual(Token.objects.count(), 1)
        self.assertEqual(Token.objects.all()[0].secret, response.content)

    def test_list_tokens(self):
        """
        Tests to that `list_tokens` returns a blank list if no tokens for an
        application link and user exist, and returns the list of secrets if
        tokens do exist.
        """
        url = reverse('list_access_tokens')
        user = User.objects.get(pk=1)
        link = ApplicationLink.objects.get(pk=1)

        nonce = make_nonce()
        data = {
            'user_id': user.username,
            'client_id': 'test',
            'client_secret': link.get_client_secret(user, nonce),
            'nonce': nonce,
        }

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "[]")

        # create some tokens for this application link and user and test that
        # a new request correctly returns these two tokens.
        Token.objects.create(secret="abc123", user=user, link=link)
        Token.objects.create(secret="abc321", user=user, link=link)

        # create a token that doesn't belong to our user to ensure that this
        # token is not returned in the list of tokens.
        test = User.objects.get(username='test')
        Token.objects.create(secret="testing", user=test, link=link)

        data['nonce'] = make_nonce()
        data['client_secret'] = link.get_client_secret(user, data['nonce'])

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "[u'abc123', u'abc321']")

    def test_delete_token(self):
        """
        Test deleting access tokens from a particular application link for a
        particular user.
        """
        url = reverse('delete_access_token')
        user = User.objects.get(pk=1)
        link = ApplicationLink.objects.get(pk=1)

        # test a request with a missing token secret
        nonce = make_nonce()
        data = {
            'user_id': user.username,
            'client_id': 'test',
            'client_secret': link.get_client_secret(user, nonce),
            'nonce': nonce,
        }

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, "Missing access_token")

        # test a request with a non-existant token secret
        data['nonce'] = make_nonce()
        data['client_secret'] = link.get_client_secret(user, data['nonce'])
        data['access_token'] = 'non-existant-token'

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, 'Token does not exist')

        # create a token to delete, and make a valid request to delete it
        Token.objects.create(secret="abc123", user=user, link=link)

        data['nonce'] = make_nonce()
        data['client_secret'] = link.get_client_secret(user, data['nonce'])
        data['access_token'] = 'abc123'

        response = self. client.get(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "Token abc123 deleted")

        self.assertEqual(Token.objects.count(), 0)

    def test_session(self):
        """
        Test swingers' session view is capable of setting arbitrary session
        keys if the user is authenticated.
        """
        url = reverse('session')
        # test that unauthenticated users can't set session variables
        self.client.logout()
        response = self.client.get(url, {'test-get': 'test'})
        self.assertEqual(response.status_code, 302)

        # login and test that setting variables on the session works
        # correctly. `self.client.login` sets two session variables,
        # _auth_user_id and _auth_user_backend.
        self.client.login(username='admin', password='test')

        response = self.client.get(url, {'test-get': 'test'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['test-get'], 'test')

        response = self.client.post(url, {'test-post': 'test'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['test-post'], 'test')

        # the length of data.keys should be 4: two keys set by the login
        # process and two set manually by us.
        self.assertEqual(len(data.keys()), 4)

    @override_settings(LOGIN_EXEMPT_URLS='swingers/validate_token/')
    def test_refresh_token(self):
        """
        Test validate token.
        """
        user = User.objects.get(pk=1)
        link = ApplicationLink.objects.get(pk=1)
        token = Token.objects.create(secret='sesame', user=user, link=link)
        modified = token.modified - timedelta(seconds=30)
        token.modified = modified
        token.save()
        url = reverse('validate_token')

        data = {
            'access_token': token.secret
        }
        response = self.client.get(url, data)
        token = Token.objects.get(pk=token.pk)
        self.assertNotEqual(token.modified, modified)
        self.assertEqual(response.content, "true")

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.content, "false")


class FormsTests(TestCase):
    def test_base_audit_form(self):
        form = DuckForm({'name': 'test'})
        self.assertTrue(form.is_valid())
        self.assertTrue(hasattr(form, 'helper'))
