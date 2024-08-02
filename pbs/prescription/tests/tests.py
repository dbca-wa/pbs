from __future__ import unicode_literals

from decimal import Decimal

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.test.client import RequestFactory
from django.utils import timezone

from pbs.tests import BasePbsTestCase
from pbs.sites import site
from pbs.prescription.admin import PrescriptionAdmin
from pbs.prescription.models import Prescription, Purpose


def set_cbas_attributes(self, prescription, exclude_fields=None,
                        extra_fields=None):
    """
    Year, season, burn id, burn name, region, district, and purposes are
    required fields to create a burn plan, so we can ignore these.
    """
    defaults = {
        'priority': prescription.PRIORITY_UNSET,
        'remote_sensing_priority': prescription.PRIORITY_NOT_APPLICABLE,
        'area': Decimal('0.0'),
        'perimeter': Decimal('0.0'),
        'treatment_percentage': None,
        'last_season': None,
        'last_year': None,
        'contentious': False,
        'aircraft_burn': False,
        'allocation': None,
        'location': None,
    }

    values = {
        'priority': prescription.PRIORITY_MEDIUM,
        'area': Decimal('111.1'),
        'perimeter': Decimal('111.1'),
        'treatment_percentage': 50,
        'last_season': 1,
        'last_year': 2000,
        'allocation': 4,
        'location': 'test',
    }

    if exclude_fields is not None:
        for field in exclude_fields:
            del values[field]

    values.update(extra_fields or {})
    defaults.update(values)

    for field, value in defaults.items():
        setattr(prescription, field, value)

    prescription.save()
    purpose = Purpose.objects.get(pk=1)
    prescription.purposes.add(purpose)


class PrescriptionCreationTests(BasePbsTestCase):
    fixtures = ['test-users', 'test-seasons']

    def setUp(self):
        self.client.login(username='admin', password='test')

    def test_create_prescription(self):
        url = reverse('admin:prescription_prescription_add')
        data = {
            'name': 'Test',
            'planned_season': 1,
            'planned_year': 2013,
            'region': 1,
            'district': 1,
            'location': 'Test location',
            'perimeter': 20,
            'area': 100,
            'purposes': [1],
            'remote_sensing_priority': 4,
            'priority': 2,
            'contentious': False,
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(Prescription.objects.count(), 1)
        prescription = Prescription.objects.get(name='Test')
        redirect = reverse('admin:prescription_prescription_detail',
                           args=[str(prescription.id)])
        self.assertRedirects(response, redirect)
        # burn id must be district code + three-digit number starting from 000
        # i.e. KAL_001. Refs BR-02.
        self.assertEqual(prescription.burn_id, 'KAL_001')
        # initial status should be "Draft" (CBAS). Refs BR-06
        self.assertEqual(prescription.get_planning_status_display(),
                         'Draft')

    def test_prescription_more_than_4_digit_year(self):
        """
        Test for PBS-1208 regression.
        """
        url = reverse('admin:prescription_prescription_add')
        data = {
            'name': 'Test',
            'planned_season': 1,
            'planned_year': 99999,
            'region': 1,
            'district': 1,
            'location': 'Test location',
            'perimeter': 20,
            'area': 100,
            'purposes': [1],
            'remote_sensing_priority': 4,
            'priority': 2,
            'contentious': False,
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(Prescription.objects.count(), 1)
        prescription = Prescription.objects.get(name='Test')
        redirect = reverse('admin:prescription_prescription_detail',
                           args=[str(prescription.id)])
        self.assertRedirects(response, redirect)
        self.assertTrue(Prescription.objects.count(), 1)

    def test_contentious_prescription_no_rationale(self):
        """
        Any burn identified as contentious requires a rationale.
        Refs BR-13.
        """
        url = reverse('admin:prescription_prescription_add')
        data = {
            'name': 'Test',
            'planned_season': 1,
            'planned_year': 2013,
            'region': 1,
            'district': 1,
            'location': 'Test location',
            'perimeter': 20,
            'area': 100,
            'purposes': [1],
            'remote_sensing_priority': 4,
            'priority': 2,
            'contentious': True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Prescription.objects.count(), 0)
        form = response.context['adminform'].form
        self.assertEqual(form.errors, {
            'contentious_rationale': ['A contentious burn requires a '
                                      'contentious rationale.']
        })

    def test_contentious_prescription(self):
        url = reverse('admin:prescription_prescription_add')
        data = {
            'name': 'Test',
            'planned_season': 1,
            'planned_year': 2013,
            'region': 1,
            'district': 1,
            'location': 'Test location',
            'perimeter': 20,
            'area': 100,
            'remote_sensing_priority': 4,
            'priority': 2,
            'contentious': True,
            'purposes': [1],
            'contentious_rationale': 'Some stuff might happen.'
        }
        self.client.post(url, data, follow=True)
        self.assertEqual(Prescription.objects.count(), 1)


class PrescriptionClosureTests(BasePbsTestCase):
    def test_ignition_completion_date_required(self):
        """
        Test that ignition completion date is required to close the burn.
        """
        p = self.make('Prescription')
        # set up the prescription to be ready to close
        fields = ["summary", "context_statement", "context_map", "objectives",
                  "success_criteria", "priority_justification",
                  "complexity_analysis", "risk_register"]

        for field in fields:
            setattr(p.pre_state, field, True)
        p.pre_state.save()

        fields = ["pre_actions", "actions", "roads", "traffic", "tracks",
                  "burning_prescription", "edging_plan", "contingency_plan",
                  "lighting_sequence", "exclusion_areas",
                  "organisational_structure", "briefing", "operation_maps",
                  "aerial_maps"]

        for field in fields:
            setattr(p.day_state, field, True)
        p.day_state.save()

        p.post_state.post_burn_checklist = True
        p.post_state.save()

        self.assertTrue(p.pre_state.finished)
        self.assertTrue(p.day_state.finished)
        self.assertTrue(p.post_state.post_burn_checklist)

        self.assertFalse(p.can_close)
        p.ignition_completed_date = timezone.now()
        p.save()
        self.assertTrue(p.can_close)


class CorporateApprovalTests(BasePbsTestCase):
    fixtures = ['test-users']

    def setUp(self):
        self.client.login(username='admin', password='test')

    def set_cbas_attributes(self, prescription, exclude_fields=None,
                            extra_fields=None):
        """
        Year, season, burn id, burn name, region, district, and purposes are
        required fields to create a burn plan, so we can ignore these.
        """
        defaults = {
            'priority': prescription.PRIORITY_UNSET,
            'remote_sensing_priority': prescription.PRIORITY_NOT_APPLICABLE,
            'area': Decimal('0.0'),
            'perimeter': Decimal('0.0'),
            'treatment_percentage': None,
            'last_season': None,
            'last_year': None,
            'contentious': False,
            'aircraft_burn': False,
            'allocation': None,
            'location': None,
        }

        values = {
            'priority': prescription.PRIORITY_MEDIUM,
            'area': Decimal('111.1'),
            'perimeter': Decimal('111.1'),
            'treatment_percentage': 50,
            'last_season': 1,
            'last_year': 2000,
            'allocation': 4,
            'location': 'test',
        }

        if exclude_fields is not None:
            for field in exclude_fields:
                del values[field]

        values.update(extra_fields or {})
        defaults.update(values)

        for field, value in defaults.items():
            setattr(prescription, field, value)

        prescription.save()
        purpose = Purpose.objects.get(pk=1)
        prescription.purposes.add(purpose)

    def test_corporate_approval_allowed(self):
        """
        Test all combinations of attributes to ensure that each attribute
        is required before corporate submission is allowed.
        """
        p = self.make('Prescription')
        self.assertFalse(p.can_corporate_approve)
        self.assertFalse(p.has_corporate_approval)

        fields = ['priority', 'location', 'perimeter', 'area', 'last_season',
                  'last_year', 'treatment_percentage', 'allocation']
        for field in fields:
            self.set_cbas_attributes(p, exclude_fields=[field])
            self.assertFalse(p.can_corporate_approve)
            self.set_cbas_attributes(p)
            self.assertTrue(p.can_corporate_approve)

    def test_submit_for_corporate_approval(self):
        """
        Test that submitting for corporate approval works as expected.
        """
        # set up the prescription to be ready for corporate approval
        p = self.make('Prescription')
        self.set_cbas_attributes(p)
        self.assertTrue(p.can_corporate_approve)
        self.assertTrue(p.planning_status == p.PLANNING_DRAFT)

        # submit for corporate approval
        url = reverse('admin:prescription_prescription_corporate_approve',
                      args=(str(p.id),))
        response = self.client.post(url, {}, follow=True)
        self.assertEqual(response.status_code, 200)

        # refresh prescription object
        p = Prescription.objects.get(name='test')
        self.assertTrue(p.planning_status == p.PLANNING_SUBMITTED)
        self.assertTrue(p.planning_status_modified is not None)

    def test_apply_corporate_approval(self):
        """
        Test that applying corporate approval works.
        """
        p = self.make('Prescription')
        self.set_cbas_attributes(p)
        p.planning_status = p.PLANNING_SUBMITTED
        p.save()

        url = reverse('admin:prescription_prescription_corporate_approve',
                      args=(str(p.id),))
        self.client.login(username='fmsb', password='test')
        response = self.client.post(url, {}, follow=True)
        self.assertEqual(response.status_code, 200)

        p = Prescription.objects.get(name='test')
        self.assertTrue(p.planning_status == p.PLANNING_APPROVED)
        self.assertTrue(p.planning_status_modified is not None)


class EndorsementTests(BasePbsTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _mocked_authenticated_request(self, url, user):
        request = self.factory.get(url)
        request.user = user
        return request

    def test_submit_for_endorsement(self):
        """
        Test submitting for endorsement.
        """

    def test_apply_endorsements(self):
        """
        Test applying all endorsements.
        """

    def test_areas_locked_ok(self):
        """
        Test that all sections of the ePFP are locked correctly.
        """

    def test_remove_endorsement(self):
        """
        Test removing an endorsement from a prescription.
        """
        self.client.login(username='user', password='test')
        p = self.make('Prescription')

        url = reverse('admin:prescription_prescription_changelist')
        response = self.client.get(url)

        self.assertContains(response, 'No prescribing officer')

        u = User.objects.create(username='test2', password='test',
                                first_name='Test', last_name='McTest')
        p.prescribing_officer = u
        p.save()

        response = self.client.get(url)


class ApprovalTests(BasePbsTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _mocked_authenticated_request(self, url, user):
        request = self.factory.get(url)
        request.user = user
        return request


class PrescriptionAdminTests(BasePbsTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _mocked_authenticated_request(self, url, user):
        request = self.factory.get(url)
        request.user = user
        return request

    def test_prescribing_officer_name(self):
        self.client.login(username='admin', password='test')
        p = self.make('Prescription')

        url = reverse('admin:prescription_prescription_changelist')
        response = self.client.get(url)

        self.assertContains(response, 'No prescribing officer')

        u = User.objects.create(username='test2', password='test',
                                first_name='Test', last_name='McTest')
        p.prescribing_officer = u
        p.save()

        response = self.client.get(url)

        self.assertContains(response, 'Test McTest')

    def test_changelist_actions(self):
        """
        Test that users get the right actions that they can perform on the
        page.
        """
        user = User.objects.create(username='test')
        url = reverse('admin:prescription_prescription_changelist')
        request = self._mocked_authenticated_request(url, user)
        admin = PrescriptionAdmin(Prescription, site)

        self.assertFalse(user.has_perm('prescription.can_delete'))
        self.assertFalse(user.has_perm('prescription.can_delete_approval'))

        actions = admin.get_actions(request)

        self.assertTrue('delete_selected' not in actions)
        self.assertTrue('delete_approval_endorsement' not in actions)

        content_type = ContentType.objects.get(app_label='prescription',
                                               model='prescription')
        delete = Permission.objects.get(codename='delete_prescription',
                                        content_type=content_type)
        approval = Permission.objects.get(codename='can_delete_approval',
                                          content_type=content_type)
        permissions = [
            (delete, 'delete_selected'),
            (approval, 'delete_approval_endorsement')]

        for permission, action in permissions:
            # ensure that for each permission and action name, the user is
            # able to perform that action from the action dropdown.
            user.user_permissions.add(permission)
            user = User.objects.get(username='test')
            request = self._mocked_authenticated_request(url, user)
            actions = admin.get_actions(request)
            self.assertTrue(action in actions)
