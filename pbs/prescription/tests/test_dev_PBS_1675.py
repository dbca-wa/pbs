#! /usr/bin/env python2.7
"""
Module: test_dev_PBS_1675.py
Package: pbs.prescription.tests
Description: **Dangerous** testing

This test suite must only be conducted on a pre-existing test database.
Difficulties forming a temporary database have forced me to this.
"""
from __future__ import print_function, division, unicode_literals, absolute_import
# Imports
import pytest
from django.test.client import Client, RequestFactory
from django.urls import reverse
from nose.tools import *
from bs4 import BeautifulSoup

from pbs.forms import EndorseAuthoriseSummaryForm as form
from datetime import date
import os

import logging
logging.disable(logging.CRITICAL)
# Constants

# Classes

# Fixtures

# Tests

def test_truth():
    assert True == True

def test_base_url():
    client = Client()
    response = client.get('/prescription/prescription/')
    assert response.content

def test_prescription_url():
    client = Client()
    response = client.get('/prescription/prescription/635/')
    assert response.content

def test_endorsement_url():
    c = Client()
    response = c.get("/endorse-authorise/")
    eq_(response.status_code, 200)

# Test the view
class testView():
    def setUp(self):
        from pbs.sites import PrescriptionSite
        self.site = PrescriptionSite()
        self.rf = RequestFactory()
        self.url = reverse('admin:endorse_authorise_summary')
        self.client = Client()
        self.client.login(username=os.environ['USERNAME'],
                          password=os.environ['PASSWORD'])

    def test_base_url(self):
        req = self.rf.get(self.url)
        res = self.site.endorse_authorise_summary(req)
        eq_(res.status_code, 200)

    def test_report_summary_url(self):
        url = self.url + "?report=summary"
        req = self.rf.get(url)
        eq_(req.GET['report'], 'summary')
        res = self.site.endorse_authorise_summary(req)
        eq_(res.status_code, 200)

    def test_client_can_login(self):
        assert self.client.login(username=os.environ['USERNAME'], password=os.environ['PASSWORD'])

    def test_report_approvals_has_dates(self):
        url = self.url + "?report=approvals"
        req = self.rf.get(url)
        data = {
            'toDate': None,
            'fromDate': None
        }
        response = self.client.post(url, data=data)
        form = response.context['form']
        assert form.is_valid()
        eq_(response.context['title'], 'Approvals summary')
        eq_(form.cleaned_data.get('toDate'), date.today())

    def test_report_ignitions_has_dates(self):
        url = self.url + "?report=ignitions"
        req = self.rf.get(url)
        data = {
            'toDate': None,
            'fromDate': None
        }
        response = self.client.post(url, data=data)
        form = response.context['form']
        assert form.is_valid()
        eq_(response.context['title'], 'Ignitions summary')
        eq_(form.cleaned_data.get('toDate'), date.today())

    def test_one_active_tab_summary(self):
        url = self.url + "?report=summary"
        response = self.client.get(url)
        soup = BeautifulSoup(response.content)
        report_tabs = soup.find("ul", {'id': 'report-tabs'})
        active_tabs = report_tabs.find_all("li", {'class': 'active' })
        eq_(len(active_tabs), 1)
        summary_tab = report_tabs.find_all("li", {'id': 'summary-tab', 'class': 'active' })
        assert summary_tab

    def test_one_active_tab_approvals(self):
        url = self.url + "?report=approvals"
        response = self.client.get(url)
        soup = BeautifulSoup(response.content)
        report_tabs = soup.find("ul", {'id': 'report-tabs'})
        active_tabs = report_tabs.find_all("li", {'class': 'active'})
        eq_(len(active_tabs), 1)
        approvals_tab = report_tabs.find_all("li", {'id': 'approvals-tab', 'class': 'active' })
        assert approvals_tab

    def test_one_active_tab_ignitions(self):
        url = self.url + "?report=ignitions"
        response = self.client.get(url)
        soup = BeautifulSoup(response.content)
        report_tabs = soup.find("ul", {'id': 'report-tabs'})
        active_tabs = report_tabs.find_all("li", {'class': 'active'})
        eq_(len(active_tabs), 1)
        ignitions_tab = report_tabs.find_all("li", {'id': 'ignitions-tab', 'class': 'active' })
        assert ignitions_tab

def test_can_I_get_a_PrescriptionSite():
    from pbs.sites import PrescriptionSite
    site = PrescriptionSite()
    assert site

def test_can_I_call_the_endorse_method():
    from pbs.sites import PrescriptionSite
    site = PrescriptionSite()
    rf = RequestFactory()
    url = reverse('admin:endorse_authorise_summary')
    request = rf.get(url)
    response = site.endorse_authorise_summary(request)
    eq_(response.status_code, 200)

def test_we_have_a_endorsement_summary_view():
    c = Client()
    url = reverse('admin:endorse_authorise_summary')
    response = c.get(url)
    eq_(response.status_code, 200)

def test_we_have_a_context():
    c = Client()
    url = reverse('admin:endorse_authorise_summary')
    response = c.get(url)
    assert response.context['form']

def test_included_dates_in_form():
    init = {
        'fromDate': date(2014,1,1),
        'toDate': date.today(),
    }
    f = form(init)
    assert f.is_bound
    assert f.is_valid()

def test_missing_dates_in_form():
    init = {}
    f = form(init)
    assert f.is_bound
    assert f.is_valid()
    eq_(f.cleaned_data['fromDate'], date(1970, 1, 1))

def test_default_dates_in_form():
    init = {
        'fromDate': None,
        'toDate': None,
    }
    f = form(init)
    assert f.is_bound
    assert f.is_valid()
    eq_(f.cleaned_data['fromDate'], date(1970, 1, 1))
    eq_(f.cleaned_data['toDate'], date.today())

if __name__ == "__main__":

    test_base_url()

    print("Done __main__")
