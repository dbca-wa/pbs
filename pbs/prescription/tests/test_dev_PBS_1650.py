#! /usr/bin/env python2.7
"""
Module     : test_PBS_1650.py
Package    : pbs.prescription.tests
Description: Ensure the state of the treamtent checkboxes is carried forward in the forms

NB. These test will require access to a generated database and will/should not be
used with the nose test runner
"""
from __future__ import print_function, division, unicode_literals, absolute_import

# Imports
from django.test.client import Client, RequestFactory
from django.urls import reverse
from nose.tools import *
from bs4 import BeautifulSoup

# Logging
import logging
logging.disable(logging.CRITICAL)

# Functions
def test_truth():
    assert True == False



# Test the url

# Test the model

# Test the view

# Test the template

if __name__ == "__main__":

    
    print("Done __main__")
