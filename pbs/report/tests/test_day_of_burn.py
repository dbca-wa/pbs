#!/usr/bin/env python
"""
Module: test_day_of_burn.py
Package: pbs.report.tests
Description: Beginning the test framwework

"""
from __future__ import print_function, division, unicode_literals, absolute_import
### Imports
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

import pytest
# from pytest.mark import django_db

import pbs
from pbs.report._views.day_of_burn import day_of_burn
### Constants

### Classes

### Functions

### Tests

def test_truth():
    assert True == True
    
@pytest.mark.django_db
def test_my_user():
    
    me = User.objects.get(username='admin')
    assert me.is_superuser
    
# def test_day_of_burn_url(db, rf):
#     """Is the base url responsive?"""
#     client = Client()
#     url = reverse('report:day_of_burn')
#     request = rf.get(url)
#     user = User.objects.create_user(tester)
#     request.user = User
#     response = day_of_burn(request)

#     assert response.status_code == 200
# @pytest.mark.django_db
# def test_day_of_burn_url(db, rf):
#     """Is the base url responsive?"""
#     client = Client()
#     url = reverse('report:day_of_burn')
#     request = rf.get(url)
#     user = User.objects.create_user(tester)
#     request.user = User
#     response = day_of_burn(request)

#     assert response.status_code == 200

if __name__ == "__main__":
    
    print("Done __main__")
