from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from django.http import HttpRequest, HttpResponse
from django.test import TestCase

from swingers.sauth.decorators import crossdomain
from swingers.sauth.models import ApplicationLink
from swingers.utils.decorators import workdir
from swingers.tests.models import Duck, ParentDuck

from swingers import models

from swingers.utils.auth import *
from swingers.utils import *
from swingers.utils.query import *
from swingers.utils.geo import *

from mock import patch
from datetime import datetime

import string
import operator
import unittest2
import json

User = get_user_model()


class UtilTests(TestCase):
    urls = 'swingers.tests.urls'
    fixtures = ['test-users', 'test-application-link']

    def setUp(self):
        patcher = patch('swingers.sauth.models.requests.sessions.Session')
        self.requests = patcher.start()
        self.addCleanup(patcher.stop)

    def test_machine_id(self):
        machine_id1 = machine_id()
        machine_id2 = machine_id()
        self.assertEqual(machine_id1, machine_id2)

    def test_shorthash(self):
        self.assertEqual(len(shorthash(self)), 10)

    def test_make_nonce(self):
        self.assertEqual(len(make_nonce()), 10)

    def test_timedcall(self):
        t, res = timedcall(chomsky, 50, line_length=150)
        self.assertTrue(t >= 0)
        self.assertTrue(bool(res))

    def test_breadcrumb_trail(self):
        bt = breadcrumb_trail((("#", "test"), (None, "testik")))
        self.assertEqual(bt, u'<a href="#">test</a> > testik')

    def test_breadcrumbs_bootstrap(self):
        bt = breadcrumb_trail((("#", "test"), (None, "testik")))
        self.assertEqual(bt, u'<a href="#">test</a> > testik')

    def test_sanitise_filename(self):
        valid_chars = '-_.{0}{1}'.format(string.letters, string.digits)
        sf = sanitise_filename(r'`1~!@#$%^&*()_+=-][{};":",./?><\|ladfjk   ')
        self.assertEqual(len([c for c in sf if c not in valid_chars]), 0)

    def test_smart_truncate(self):
        st = smart_truncate("This is a very long text that we would like to be"
                            "truncated using `smart_truncate`", 50)
        self.assertEqual(
            st, u'This is a very long text that we would like to...(more)')

    def test_label_span(self):
        ls = label_span("Tomas", "success")
        self.assertEqual(ls, u'<span class="label label-success">Tomas</span>')

    def test_content_filename(self):
        d = {
            'date': datetime.strftime(datetime.today(), '%Y/%m/%d'),
            'filename': "this_is_weird.txt",
        }
        path = 'uploads/{date}/{filename}'.format(**d)

        cf = content_filename(None, "this is weird.txt")
        self.assertEqual(cf, path)

    def test_validate_request(self):
        # Missing Input
        self.assertRaises(Exception, validate_request,
                          **{"client_id": None, "client_secret": None})
        self.assertRaises(Exception, validate_request,
                          **{"client_id": None, "user_id": None})
        self.assertRaises(Exception, validate_request,
                          **{"user_id": None, "client_secret": None})

        # Invalid user id
        self.assertRaises(Exception, validate_request,
                          **{"user_id": "blee", "client_secret": None,
                             "client_id": "restless"})

        # Application link does not exist
        self.assertRaises(Exception, validate_request,
                          **{"user_id": "admin", "client_secret": None,
                             "client_id": "restless"})

        # Missing nonce
        self.assertRaises(Exception, validate_request,
                          **{"user_id": "admin", "client_secret": None,
                             "client_id": "restless"})

        # valid (sha256)
        link = ApplicationLink.objects.get(client_name="test",
                                           server_name=settings.SERVICE_NAME)
        user, l, expires = validate_request(
            {"user_id": "admin",
             "client_secret": link.get_client_secret("admin", 5),
             "client_id": "test", "nonce": 5})
        self.assertEqual(user.username, "admin")
        self.assertEqual(link.pk, l.pk)

        # You can't reuse nonce
        self.assertRaises(Exception, validate_request,
                          **{"user_id": "admin",
                             "client_secret": link.get_client_secret(
                                 "admin", 5),
                             "client_id": "test", "nonce": 5})

        # Invalid client secret (sha256)
        self.assertRaises(Exception, validate_request,
                          **{"user_id": "admin",
                             "client_secret": link.get_client_secret(
                                 "admin", 6),
                             "client_id": "test", "nonce": 7})

        # valid (basic)
        with self.settings(SERVICE_NAME="restless2"):
            link = ApplicationLink.objects.get(client_name="test2",
                                               server_name="restless2")
            user, l, expires = validate_request(
                {"user_id": "admin", "client_secret": link.secret,
                 "client_id": "test2"})
            self.assertEqual(user.username, "admin")
            self.assertEqual(link.pk, l.pk)

            # Invalid client secret (basic)
            self.assertRaises(Exception, validate_request,
                              **{"user_id": "admin", "client_secret": "blee",
                                 "client_id": "test2"})

    def test_queryset_iterator(self):
        for u in queryset_iterator(User.objects.all()):
            self.assertTrue(bool(u.pk))

    def test_normalise_query(self):
        norm_query = normalise_query('  some random  words "with   quotes  " '
                                     'and   spaces')
        self.assertEqual(norm_query, ['some', 'random', 'words',
                                      'with quotes ', 'and', 'spaces'])

    def test_get_query(self):
        query = get_query('  issapps   admin', ['email', 'username'])
        self.assertQuerysetEqual(User.objects.filter(query), [1],
                                 transform=operator.attrgetter('pk'))

    def test_filter_queryset(self):
        duck = Duck.objects.create(name='Tomas')
        queryset = Duck.objects.all()
        q = filter_queryset('Tomas', Duck, queryset)
        self.assertQuerysetEqual(q, list(queryset.values_list('pk',
                                                              flat=True)),
                                 transform=operator.attrgetter('pk'))

        ParentDuck.objects.create(name='Tomas2', duck=duck)
        queryset = ParentDuck.objects.all()
        q = filter_queryset('bleeeee', ParentDuck, queryset)
        self.assertQuerysetEqual(q, [])

    def test_retrieve_access_token(self):
        url = reverse('request_access_token')
        request = HttpRequest()
        request.user = User.objects.get(pk=1)
        request.META = {
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': 80
        }
        request.path = request.path_info = '/'

        instance = self.requests.return_value

        link = ApplicationLink.objects.get(server_name='swingers')

        username = request.user.username
        nonce = make_nonce()

        secret = self.client.get(url, {
            "user_id": username,
            "nonce": nonce,
            "client_secret": link.get_client_secret(username, nonce),
            "client_id": link.client_name,
        })

        response = self.requests.models.Response()
        response.status_code = 200
        response.headers = {'content-type': 'text/html'}
        response._content = secret.content

        instance.request.return_value = response

        url, token = retrieve_access_token(request, 'swingers')
        self.assertEqual(url, "https://ge.dec.wa.gov.au")

    def test_chomsky(self):
        self.assertEqual(chomsky(0), '')
        self.assertEqual(chomsky(2).count("."), 2)
        self.assertGreater(len(chomsky(1)), 1)

    def test_get_random_datetime(self):
        dt = get_random_datetime()
        self.assertEqual(type(dt), datetime)
        dt = get_random_datetime(2013)
        self.assertEqual(dt.year, 2013)

    @patch('swingers.utils.auth.LDAPBackend')
    @patch('swingers.utils.auth._LDAPUser')
    def test_get_or_create_local_user(self, _LDAPUser, LDAPBackend):
        user = User.objects.get(pk=1)
        backend = LDAPBackend.return_value
        backend.populate_user.return_value = User(username="ldaptest",
                                                  email="ldap@test.blah")
        result = get_or_create_local_user('ldaptest')
        self.assertEqual(result.username, 'ldaptest')
        result = get_or_create_local_user('admin')
        self.assertEqual(result, user)

        ldap_user = _LDAPUser.return_value
        ldap_user.connection.search_s.return_value = [
            ('CN=Cale\\, Brendan,OU=Users,OU=IT Operations,OU=Locations,'
             'DC=corporateict,DC=domain', {'sAMAccountName': ['BrendanC']})
        ]
        backend.populate_user.return_value = User(
            username="brendanc", email="brendan.cale@dec.wa.gov.au")

        result = get_or_create_local_user('brendan.cale@dec.wa.gov.au')
        self.assertEqual(result.username, 'brendanc')

        ldap_user.connection.search_s.return_value = []
        result = get_or_create_local_user('testuser@broken')
        self.assertEqual(result, None)


class DecoratorTests(TestCase):
    urls = 'swingers.tests.urls'
    fixtures = ['test-users.json']

    def setUp(self):
        self.directory = "/tmp/test-workdir"
        patcher = patch('tempfile.mkdtemp')
        self.mkdtemp = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch('os.makedirs')
        self.makedirs = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch('os.chdir')
        self.chdir = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch('shutil.rmtree')
        self.rmtree = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch('os.path.exists')
        self.exists = patcher.start()
        self.addCleanup(patcher.stop)

    def test_workdir_remove(self):
        """
        Test the workdir decorator cleans up after itself.
        """
        @workdir()
        def temp_workdir():
            pass

        self.exists.return_value = False

        temp_workdir(self.directory)

        self.makedirs.assert_called_with(self.directory)
        self.rmtree.assert_called_with(self.directory)

        self.mkdtemp.return_value = '/tmp/random-temp-dir'

        temp_workdir()

        self.mkdtemp.assert_called_with()
        self.rmtree.assert_called_with('/tmp/random-temp-dir')

    def test_workdir_permanent(self):
        """
        Test the workdir doesn't remove its directory when instructed not to.
        """
        @workdir(remove=False)
        def temp_workdir_keep():
            pass

        self.exists.return_value = True

        temp_workdir_keep(self.directory)

        self.assertEqual(self.makedirs.mock_calls, [])
        self.assertEqual(self.rmtree.mock_calls, [])

        temp_workdir_keep()
        self.mkdtemp.assert_called_with()
        self.assertEqual(self.rmtree.mock_calls, [])

    def test_crossdomain(self):
        @crossdomain
        def index_view(request):
            return HttpResponse("Hello there")

        request = HttpRequest()
        request.META = {
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': 80,
            'HTTP_ORIGIN': 'www.example.com'
        }
        request.path = request.path_info = "/"

        # check an OPTIONS request returns an empty response body.
        request.method = "OPTIONS"
        response = index_view(request)
        self.assertEqual(response.content, "")
        self.assertEqual(response['Access-Control-Allow-Origin'],
                         "www.example.com")
        self.assertEqual(response['Access-Control-Allow-Methods'],
                         "GET, POST, OPTIONS")
        self.assertEqual(response['Access-Control-Allow-Headers'],
                         "Content-Type, X-Requested-With")
        self.assertEqual(response['Access-Control-Allow-Credentials'],
                         "true")

        # check a GET/POST request returns the response as normal.
        request.method = "GET"
        response = index_view(request)
        self.assertEqual(response.content, "Hello there")
        self.assertEqual(response['Access-Control-Allow-Origin'],
                         "www.example.com")
        self.assertEqual(response['Access-Control-Allow-Methods'],
                         "GET, POST, OPTIONS")
        self.assertEqual(response['Access-Control-Allow-Headers'],
                         "Content-Type, X-Requested-With")
        self.assertEqual(response['Access-Control-Allow-Credentials'],
                         "true")

        del request.META['HTTP_ORIGIN']
        response = index_view(request)
        self.assertEqual(response.content, "Hello there")
        self.assertFalse(response.has_header('Access-Control-Allow-Origin'))
        self.assertFalse(response.has_header('Access-Control-Allow-Methods'))
        self.assertFalse(response.has_header('Access-Control-Allow-Headers'))
        self.assertFalse(
            response.has_header('Access-Control-Allow-Credentials'))


class GeoUtilsTests(TestCase):
    fixtures = ['test-users.json']

    @unittest2.skipIf(not models.GIS_ENABLED, "DB is not geo-enabled.")
    def test_render_to_geojson(self):
        # TODO: could be more thorough
        from swingers.tests.models import GeoDuck
        out = render_to_geojson(GeoDuck.objects.all())
        self.assertEqual(out, '{"type": "FeatureCollection", "features": []}')

        GeoDuck.objects.create(
            poly="POLYGON ((30 10, 10 20, 20 40, 40 40, 30 10))")
        out = render_to_geojson(GeoDuck.objects.all())
        out_json = json.loads(out)

        self.assertEqual(out_json['srid'], 4326)
        self.assertEqual(len(out_json['features']), 1)
        self.assertEqual(out_json['features'][0]['geometry']['type'],
                         "Polygon")
        self.assertEqual(out_json['features'][0]['geometry']['coordinates'],
                         [[[30.0, 10.0], [10.0, 20.0], [20.0, 40.0],
                           [40.0, 40.0], [30.0, 10.0]]])
        self.assertEqual(out_json['crs']['properties']['href'],
                         "http://spatialreference.org/ref/epsg/4326/")
        self.assertEqual(out_json['type'], "FeatureCollection")
        self.assertEqual(out_json['bbox'], [10.0, 10.0, 40.0, 40.0])
        self.assertEqual(out_json['features'][0]['properties']['creator'],
                         "admin")
        self.assertEqual(out_json['features'][0]['properties']['modifier'],
                         "admin")

    @unittest2.skipIf(not models.GIS_ENABLED, "DB is not geo-enabled.")
    def test_find_geom_field(self):
        from swingers.tests.models import GeoDuck
        field = find_geom_field(GeoDuck.objects.all())
        self.assertEqual(field, 'poly')

        GeoDuck.objects.create(
            poly="POLYGON ((30 10, 10 20, 20 40, 40 40, 30 10))")
        field = find_geom_field(GeoDuck.objects.all())
        self.assertEqual(field, 'poly')

        Duck.objects.create(name='Tomas')
        self.assertRaises(ValueError, find_geom_field, Duck.objects.all())

    @unittest2.skipIf(not models.GIS_ENABLED, "DB is not geo-enabled.")
    def test_transform_geom(self):
        from swingers.tests.models import GeoDuck
        geo_duck = GeoDuck.objects.create(
            poly="SRID=28349;POLYGON ((110 1200, 120 1210, 120 1220, 130 1222,"
                 " 110 1200))")
        geom = transform_geom(geo_duck.poly)
        self.assertEqual(geom.coords,
                         (((499999.99999999994, 2035.0570603180677),
                           (499999.99999999994, 2035.0570603180677),
                           (499999.99999999994, 2035.0570603180677),
                           (499999.99999999994, 2035.0570603180677),
                           (499999.99999999994, 2035.0570603180677)),
                          ))
        self.assertEqual(geom.srid, 28351)

        geo_duck = GeoDuck.objects.create(
            poly="POLYGON ((30 10, 10 20, 20 40, 40 40, 30 10))")
        geom = transform_geom(geo_duck.poly)
        self.assertIsNone(geom)

    def test_direction_name(self):
        self.assertEqual(direction_name(0.0), "N")
        self.assertEqual(direction_name(90.0), "E")
        self.assertEqual(direction_name(152.0), "SSE")

    @unittest2.skipIf(not models.GIS_ENABLED, "DB is not geo-enabled.")
    def test_text_location(self):
        from swingers.tests.models import GeoDuck
        geo_duck = GeoDuck.objects.create(
            poly="POLYGON ((30 10, 10 20, 20 40, 40 40, 30 10))")
        tl = text_location(geo_duck.poly)
        # the text string keeps changing :(
        #self.assertEqual(tl, u'586.70 KM N of \u0645\u0635\u0631 (Egypt)')
        self.assertTrue(" KM" in tl)

        geo_duck = GeoDuck.objects.create(
            poly="POLYGON ((-10 100000, -10 100001, 10 100001, 10 100000,"
                 " -10 100000))")
        tl = text_location(geo_duck.poly)
        self.assertEqual(tl, u'Nominatim Error: Unable to geocode')

    def test_distance_bearing(self):
        from django.contrib.gis.geos import Point
        p1 = Point(x=1, y=2, srid=4326)
        p2 = Point(x=3, y=4, srid=4326)
        db = distance_bearing(p1, p2)
        self.assertEqual(db, '317.12 KM SW')
