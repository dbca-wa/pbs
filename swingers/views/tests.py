from django.test import TestCase
from django.utils.six import StringIO
from django.http import HttpRequest, HttpResponse
from django.urls import reverse

from swingers.tests.models import Duck
from swingers.tests.views import create_duck

from swingers.views.decorators import log_view_dec

import logging


class ViewsTests(TestCase):
    urls = 'swingers.tests.urls'
    fixtures = ['test-users']

    def setUp(self):
        pass

    def test_cancel_view_m(self):
        self.client.login(username='admin', password='test')
        self.assertEqual(Duck.objects.all().count(), 0)
        url = reverse('test-create-duck2')
        self.client.post(url, {'name': 'test'})
        self.assertEqual(Duck.objects.filter(name='test').count(), 1)
        self.client.post(url, {'name': 'test', '_cancel': '1'})
        self.assertEqual(Duck.objects.all().count(), 1)
        self.client.post(url, {'name': 'test2', 'cancel': None})
        self.assertEqual(Duck.objects.all().count(), 1)

    def test_log_view_dec(self):
        logger = logging.getLogger('test_view_stats')
        output = StringIO()
        if len(logger.handlers):
            logger.handlers[0].stream = output
        else:
            logger.handlers.append(logging.StreamHandler(output))

        self.client.login(username='admin', password='test')
        path = reverse('test-create-duck4', args=('Tomas',))
        r = self.client.get(path)
        self.assertEqual(r.status_code, 200)
        log = ('{"username":"admin", "view":"create_duck2", '
               '"path":"%s"}\n' % path)
        self.assertEqual(output.getvalue(), log)

    def test_log_view_dec_m(self):
        logger = logging.getLogger('test_view_stats')
        output = StringIO()
        if len(logger.handlers):
            logger.handlers[0].stream = output
        else:
            logger.handlers.append(logging.StreamHandler(output))

        self.client.login(username='admin', password='test')
        path = reverse('test-create-duck3')
        r = self.client.get(path)
        self.assertEqual(r.status_code, 200)
        log = ('{"username":"admin", "view":"CreateDuck2.get", '
               '"path":"%s"}\n' % path)
        self.assertEqual(output.getvalue(), log)
