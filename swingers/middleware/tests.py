from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.db import transaction
from django.db.transaction import TransactionManagementError
from django.http import HttpRequest, HttpResponse
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.middleware.cache import FetchFromCacheMiddleware

from swingers.middleware.auth import get_exempt_urls, AuthenticationMiddleware
from swingers.middleware.transaction import ResponseStatusTransactionMiddleware
from swingers.sauth.models import ApplicationLink, Token
from swingers.tests.models import Duck, Counter

from datetime import timedelta

import unittest2
import django

User = get_user_model()


class AuthenticationMiddlewareTests(TestCase):
    """
    Test the authentication middleware included in swingers.
    """
    fixtures = ['test-users', 'test-application-link']

    def setUp(self):
        self.allow_anonymous_access = settings.ALLOW_ANONYMOUS_ACCESS

    def tearDown(self):
        settings.ALLOW_ANONYMOUS_ACCESS = self.allow_anonymous_access

    def _get_request(self, path):
        request = HttpRequest()
        request.META = {
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': 80
        }
        request.path = request.path_info = path
        return request

    @override_settings(ALLOW_ANONYMOUS_ACCESS=False)
    def test_unauthenticated_request(self):
        """
        Test that a request by an anonymous user redirects the user to the
        login page.
        """
        request = self._get_request("/")
        request.user = AnonymousUser()
        response = AuthenticationMiddleware().process_request(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/accounts/login/')

    def test_unauthenticated_request_allow_anonymous(self):
        """
        Test that setting ALLOW_ANONYMOUS_ACCESS doesn't redirect the
        request like it would if it was False.
        """
        settings.ALLOW_ANONYMOUS_ACCESS = True
        request = self._get_request("/")
        request.user = AnonymousUser()
        self.assertEqual(
            AuthenticationMiddleware().process_request(request), None)
        self.assertTrue(hasattr(request, "SITE_NAME"))
        self.assertTrue(hasattr(request, "footer"))

    def test_token_request_anonymous_get(self):
        """
        Test that making a request with an access token logs the token's user
        into the site and updates the token's modified time.
        """
        user = User.objects.get(pk=1)
        link = ApplicationLink.objects.get(pk=1)
        token = Token.objects.create(secret='sesame', user=user, link=link)
        modified = token.modified
        request = self._get_request("/")
        request.GET['access_token'] = token.secret
        request.user = AnonymousUser()
        self.assertEqual(
            AuthenticationMiddleware().process_request(request), None)
        self.assertEqual(request.user, user)
        token = Token.objects.get(secret='sesame')
        self.assertNotEqual(token.modified, modified)

    @override_settings(ALLOW_ANONYMOUS_ACCESS=False)
    def test_unauthenticated_request_allow_anonymous2(self):
        """
        Test requests to the login page or pages with LOGIN_EXEMPT_URLS don't
        redirect.
        """
        request = self._get_request("/accounts/login/")
        request.user = AnonymousUser()
        response = AuthenticationMiddleware().process_request(request)
        self.assertEqual(response, None)
        with self.settings(LOGIN_EXEMPT_URLS=('test/url/',)):
            request = self._get_request("test/url/")
            request.user = AnonymousUser()
            response = AuthenticationMiddleware().process_request(request)
            self.assertEqual(response, None)

    def test_token_request_anonymous_headers(self):
        """
        Try setting HTTP header `HTTP_ACCESS_TOKEN` in a request with an
        anonymous user and check that it logs in the token's user.
        """
        user = User.objects.get(pk=1)
        link = ApplicationLink.objects.get(pk=1)
        token = Token.objects.create(secret='sesame', user=user, link=link)
        modified = token.modified
        request = self._get_request("/")
        request.META['HTTP_ACCESS_TOKEN'] = token.secret
        request.user = AnonymousUser()
        self.assertEqual(
            AuthenticationMiddleware().process_request(request), None)
        self.assertEqual(request.user, user)
        token = Token.objects.get(secret='sesame')
        self.assertNotEqual(token.modified, modified)

    def test_token_request_invalid(self):
        """
        Try making a request with an expired `Token` and check that it gets
        deleted.
        """
        user = User.objects.get(pk=1)
        link = ApplicationLink.objects.get(pk=1)
        token = Token.objects.create(secret='sesame', user=user, link=link)
        token.modified = token.modified - timedelta(seconds=token.timeout)
        token.save()
        request = self._get_request("/")
        request.GET['access_token'] = token.secret
        request.user = user
        self.assertEqual(
            AuthenticationMiddleware().process_request(request), None)
        self.assertEqual(Token.objects.count(), 0)

    def test_authenticated_request(self):
        """
        Test that making a request with an authenticated user results in some
        extra attributes being attached to the request.
        """
        request = self._get_request("/")
        request.user = User.objects.get(pk=1)
        self.assertEqual(
            AuthenticationMiddleware().process_request(request), None)
        self.assertTrue(hasattr(request, "SITE_NAME"))
        self.assertTrue(hasattr(request, "footer"))

    def test_preflight_response_with_access_control_headers(self):
        """
        Test setting HTTP_ACCESS_CONTROL_REQUEST_HEADERS.
        """
        request = self._get_request("/")
        request.META['HTTP_ACCESS_CONTROL_REQUEST_HEADERS'] = 'TEST-HEADER'
        response = HttpResponse()
        result = AuthenticationMiddleware().process_response(request, response)
        self.assertEqual(result['Access-Control-Allow-Headers'], 'TEST-HEADER')

    def test_preflight_response_with_origin_header(self):
        request = self._get_request("/")
        request.META['HTTP_ORIGIN'] = "www.example.com"
        response = HttpResponse()
        result = AuthenticationMiddleware().process_response(request, response)
        self.assertEqual(
            result['Access-Control-Allow-Origin'], "www.example.com")

    def test_exempt_urls(self):
        self.assertEqual(len(get_exempt_urls()), 1)
        self.assertTrue(get_exempt_urls()[0] in settings.LOGIN_URL)
        with self.settings(LOGIN_EXEMPT_URLS=('/test/url',)):
            self.assertTrue(len(get_exempt_urls()), 2)
            self.assertTrue(get_exempt_urls()[1] in settings.LOGIN_EXEMPT_URLS)


@unittest2.skipIf(django.VERSION >= (1, 6, 0), 'Not supported in django>=1.6')
class TransactionMiddlewareTests(TransactionTestCase):
    fixtures = ['test-users']

    def setUp(self):
        self.request = HttpRequest()
        self.request.META = {
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': 80
        }
        self.request.path = self.request.path_info = "/"
        self.response = HttpResponse()

    def test_managed_response_clean(self):
        """
        Test that a managed response with a clean transaction state just
        leaves transaction management.
        """
        transaction.enter_transaction_management()
        transaction.managed(True)
        ResponseStatusTransactionMiddleware().process_response(self.request,
                                                               self.response)
        self.assertFalse(transaction.is_dirty())
        self.assertRaises(TransactionManagementError,
                          transaction.leave_transaction_management)

    def test_managed_response_dirty_no_http_error(self):
        """
        Test that a managed response with a dirty transaction state commits,
        then leaves transaction management.
        """
        transaction.enter_transaction_management()
        transaction.managed(True)
        duck = Duck.objects.create(name='test')
        ResponseStatusTransactionMiddleware().process_response(self.request,
                                                               self.response)
        self.assertEqual(Duck.objects.count(), 1)
        self.assertFalse(transaction.is_dirty())
        self.assertRaises(TransactionManagementError,
                          transaction.leave_transaction_management)

    def test_managed_response_dirty_with_http_error(self):
        """
        Test that a managed response with a dirty transaction state and a http
        status code corresponding to an error rolls back the transaction and
        leaves transaction management.
        """
        middleware = ResponseStatusTransactionMiddleware()

        # status codes should raise exceptions
        for status_code in [400, 401, 403, 404, 405, 409, 410, 500, 501]:
            transaction.enter_transaction_management()
            transaction.managed(True)
            Duck.objects.create(name='test')
            self.response.status_code = status_code
            middleware.process_response(self.request, self.response)
            self.assertEqual(Duck.objects.count(), 0)
            self.assertFalse(transaction.is_dirty())
            self.assertRaises(TransactionManagementError,
                              transaction.leave_transaction_management)

    def test_unmanaged_response(self):
        """
        Test an unmanaged transaction doesn't require a commit.
        """
        transaction.enter_transaction_management()
        transaction.managed(False)
        Duck.objects.create(name='test')
        ResponseStatusTransactionMiddleware().process_response(self.request,
                                                               self.response)
        self.assertEqual(Duck.objects.count(), 1)
        self.assertFalse(transaction.is_dirty())
        transaction.leave_transaction_management()


class HtmlMiddlewareTests(TestCase):
    urls = 'swingers.tests.urls'
    fixtures = ['test-users']

    def test_htmlMinifyWorks(self):
        view = 'test-create-duck2'
        self.client.login(username='test', password='test')

        # minify when debug toolbar is not shown
        DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda x: False}
        with self.settings(DEBUG=True,
                           DEBUG_TOOLBAR_CONFIG=DEBUG_TOOLBAR_CONFIG):
            resp_with_middleware = self.client.get(reverse(view))
            self.assertEqual(resp_with_middleware.status_code, 200)

        # minify based on settings.DEBUG when debug toolbar callback is undef.
        with self.settings(DEBUG=True, DEBUG_TOOLBAR_CONFIG={}):
            resp_with_middleware2 = self.client.get(reverse(view))
            self.assertEqual(resp_with_middleware2.status_code, 200)

        self.assertEqual(len(resp_with_middleware.content),
                         len(resp_with_middleware2.content))

        # don't minify when debug toolbar is shown
        DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda x: True}
        with self.settings(DEBUG=True,
                           DEBUG_TOOLBAR_CONFIG=DEBUG_TOOLBAR_CONFIG):
            resp_without_middleware = self.client.get(reverse(view))
            self.assertEqual(resp_without_middleware.status_code, 200)

        self.assertTrue(len(resp_without_middleware.content) >
                        len(resp_with_middleware.content))

    def test_JsCssCompressorWorks(self):
        # TODO: this should be a bit smarter and at least check that the
        # compressed css/js files make sense, might need to use selenium
        view = 'test-create-duck2'
        self.client.login(username='test', password='test')
        # keeps doctype
        # minify everything but js/css with @data-compress="false"
        resp_with_middleware = self.client.get(reverse(view))
        self.assertEqual(resp_with_middleware.status_code, 200)
        self.assertTrue(resp_with_middleware.content.lower().startswith(
            '<!doctype html>'))
        self.assertEqual(resp_with_middleware.content.count('<script'), 2)
        self.assertEqual(
            resp_with_middleware.content.count('<style') +
            resp_with_middleware.content.count('rel="stylesheet"'), 2
        )

        # check compress cache works
        resp_with_middleware2 = self.client.get(reverse(view))
        self.assertEqual(resp_with_middleware2.status_code, 200)
        self.assertTrue(resp_with_middleware2.content.lower().startswith(
            '<!doctype html>'))

        self.assertEqual(resp_with_middleware.content,
                         resp_with_middleware2.content)

        # don't compress when debug toolbar is shown
        DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda x: True}
        with self.settings(DEBUG=True,
                           DEBUG_TOOLBAR_CONFIG=DEBUG_TOOLBAR_CONFIG):
            resp_without_middleware = self.client.get(reverse(view))
            self.assertEqual(resp_without_middleware.status_code, 200)
            self.assertTrue(resp_without_middleware.content.lower().startswith(
                '<!doctype html>'))
            self.assertEqual(
                resp_without_middleware.content.count('<script'), 3)
            self.assertEqual(
                resp_without_middleware.content.count('<style') +
                resp_without_middleware.content.count('rel="stylesheet"'), 3
            )

        self.assertTrue(len(resp_without_middleware.content) >
                        len(resp_with_middleware.content))


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'django-swingers'
    }
}
MIDDLEWARE_CLASSES = (('swingers.middleware.cache.UpdateCacheMiddleware',) +
                      settings.MIDDLEWARE_CLASSES +
                      ('django.middleware.cache.FetchFromCacheMiddleware',))


class UpdateCacheMiddlewareTests(TestCase):
    urls = 'swingers.tests.urls'

    def setUp(self):
        # the db connection has probably already been established so don't rely
        # on the signal being handled
        from swingers.middleware.cache import patch_db_cursor
        from django.db import connections
        self.use_debug_cursor = connections['default'].use_debug_cursor
        patch_db_cursor(connections['default'].__class__,
                        connections['default'])

    def tearDown(self):
        # revert the debug cursor setting
        from django.db import connections
        connections['default'].use_debug_cursor = self.use_debug_cursor

    def _get_request(self, method, path):
        request = HttpRequest()
        request.META = {
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': 80,
        }
        request.method = method
        request.path = request.path_info = path
        return request

    def _cache_miss(self, path):
        request = self._get_request('GET', path)
        get_cache_data = FetchFromCacheMiddleware().process_request(request)
        return get_cache_data is None

    @override_settings(CACHES=CACHES, ALLOW_ANONYMOUS_ACCESS=True,
                       MIDDLEWARE_CLASSES=MIDDLEWARE_CLASSES)
    def test_updateCacheMiddleware(self):
        """
        2 different views - reading/writing at least one common table (a, b)

        Scenario:
        *   a) GET request
        *   a) GET request (verify HIT)
        *   B) GET request
        *   B) GET request (verify HIT)
        *   a) POST request
        *   a) GET request (verify MISS)
        *   a) GET request (verify HIT)
        *   B) GET request (verify MISS)
        *   B) GET request (verify HIT)
        *   B) POST request
        *   a) GET request (verify MISS)
        *   B) GET request (verify MISS)
        *   B) GET request (verify HIT)

        We have got one view that is bound to two url endpoints - urla, urlb.
        A post to these views can arbitrarily update the counter.
        """
        Counter.objects.get_or_create(pk=1)
        urla = reverse('test-update-counter', args=(1,))
        urlb = reverse('test-update-counter2', args=(1,))

        # A
        self.assertTrue(self._cache_miss(urla))     # MISS

        # GET request
        self.client.get(urla)
        self.assertFalse(self._cache_miss(urla))    # HIT

        # B
        self.assertTrue(self._cache_miss(urlb))     # MISS

        self.client.get(urlb)
        self.assertFalse(self._cache_miss(urlb))    # HIT

        # A POST
        self.client.post(urla, {'num': 5})
        self.assertEqual(Counter.objects.get(pk=1).num, 5)

        self.assertTrue(self._cache_miss(urla))     # MISS

        self.client.get(urla)
        self.assertFalse(self._cache_miss(urla))     # HIT

        self.assertTrue(self._cache_miss(urlb))     # MISS

        self.client.get(urlb)
        self.assertFalse(self._cache_miss(urlb))     # HIT

        # B POST
        self.client.post(urlb, {'num': 7})
        self.assertEqual(Counter.objects.get(pk=1).num, 7)

        self.assertTrue(self._cache_miss(urla))     # MISS

        self.assertTrue(self._cache_miss(urlb))     # MISS
