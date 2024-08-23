#! /usr/bin/env python2.7
"""
Module     : test_PBS_1672.py
Package    : pbs.prescription.tests
Description: Ensure initial data follows through.


Notes on these tests.

The test machinery is working, but we don't yet have data for the db.
So most of these tests are failing, because we need a prescription tools
make the views.
"""
from __future__ import print_function, division, unicode_literals, absolute_import

# Imports
import os
from django.test.client import Client, RequestFactory
from django.urls import reverse
from nose.tools import *
from bs4 import BeautifulSoup

from pbs.prescription.models import (
    Region, District, Prescription,
)

# Logging
import logging
logging.disable(logging.CRITICAL)

# Functions
def test_truth():
    assert True == True

# Test the url
# def test_no_descriptor_select():
#     url = ("/document/document/add/prescription/642/?tag=167&next=" +
#               "/implementation/burningprescription/prescription/642/")
#     c = Client()
#     r = c.get(url)
#     soup = BeautifulSoup(r.content)
#     labels = soup.find_all('label')
#     for lab in labels:
#         print(lab.string)
#     is_document_label = lambda t: t.text.startswith("Doc")
#     bad_labels = filter(is_document_label, labels)
#     assert not any(bad_labels)
#     assert False

class testView():

    def setUp(self):
        from pbs.sites import PrescriptionSite
        self.site = PrescriptionSite()
        self.rf = RequestFactory()
        # e.g. url = ("/document/document/add/prescription/642/?tag=167&next=" +
        #         "/implementation/burningprescription/prescription/642/")
        self.url = reverse('admin:document_document_add', args= ['642'])
        self.client = Client()
        self.client.login(username=os.environ['USERNAME'],
                          password=os.environ['PASSWORD'])
        self.add_season()
        self.add_region()
        self.add_

    def add_season(self):
        s = Season()
        s.save()

    def add_region(self, name="test"):
        r = Region()
        r.name = name
        r.save()

    def test_we_can_add_a_region(self):
        qs = Region.objects.all()
        assert qs.count() == 0
        name = "foo"
        self.add_region("foo")
        r = Region.objects.get(name=name)
        eq_(r.name, name)

    def test_base_url(self):
        req = self.rf.get(self.url)
        res = self.site.endorse_authorise_summary(req)
        eq_(res.status_code, 200)

    def xtest_document_base_url(self):
        print(os.environ['USERNAME'])
        url = reverse('admin:document_document_add', args= ['642'])
        print("url is ", url)
        r = self.client.get(url)
        eq_(r.status_code, 200)

    def xtest_we_have_the_right_page(self):
        r = self.client.get(self.url)
        soup = BeautifulSoup(r.content)
        req_text = "Add Fire Behaviour Calculation document"
        h1_tags = soup.find_all('h1')
        print(h1_tags)
        assert False
        assert any(tag.string == req_text for tag in soup.findall('h1'))

    def test_no_bad_descriptor_on_get(self):
        url = reverse('admin:document_document_add', args= ['642'])
        r = self.client.get(url)
        soup = BeautifulSoup(r.content)
        labels = soup.find_all('label')
        for lab in labels:
            print(lab.string)
        is_document_label = lambda t: t.text.startswith("Doc")
        bad_labels = filter(is_document_label, labels)
        assert not any(bad_labels)


    def test_empty_post_returns_bad_descriptor(self):
        pass



# Test the model

# Test the view

# Test the template

if __name__ == "__main__":

    print("Done __main__")
