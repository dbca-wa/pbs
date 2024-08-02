#! /usr/bin/env python2.7
"""
Module     : test_PBS_1672.py
Package    : pbs.prescription.tests
Description: Ensure initial data follows through.
"""
from __future__ import print_function, division, unicode_literals, absolute_import

# Imports
import os
from django.test.client import Client, RequestFactory
from django.urls import reverse
from nose.tools import *
from bs4 import BeautifulSoup

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
        self.url = reverse('admin:endorse_authorise_summary')
        self.client = Client()
        self.client.login(username=os.environ['USERNAME'],
                          password=os.environ['PASSWORD'])

    def test_base_url(self):
        req = self.rf.get(self.url)
        res = self.site.endorse_authorise_summary(req)
        eq_(res.status_code, 200)

    def test_document_base_url(self):
        # url = ("/document/document/add/prescription/642/?tag=167&next=" +
        #         "/implementation/burningprescription/prescription/642/")
        url = reverse('admin:document_document_add', args= ['642'])
        r = self.client.get(url)



# Test the model

# Test the view

# Test the template

if __name__ == "__main__":

    print("Done __main__")
