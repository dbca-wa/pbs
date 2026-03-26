from django.contrib.admin.utils import quote
from django.contrib.auth.models import User
from django.urls import reverse

from pbs.tests import BasePbsTestCase

from pbs.prescription.models import Prescription
from pbs.risk.admin import ActionAdmin
from pbs.sites import site


class ActionAdminTests(BasePbsTestCase):
    """
    Test the functionality of the ActionAdmin.
    """
    def setUp(self):
        super(ActionAdminTests, self).setUp()
        self.prescription = self.make(Prescription)
        user = User.objects.create(username='test')
        url = reverse('admin:risk_action_changelist',
                      args=(quote(self.prescription.id),))
        self.request = self._mocked_authenticated_request(url, user)
        self.admin = ActionAdmin(Prescription, site)
        self.admin.prescription = self.prescription

    def test_get_list_display(self):
        """
        Test get_list_display with different request types.
        """
        # if there are no pre_burn, day_of_burn or post_burn variables set
        Prescription.is_draft = True
        self.assertIn("add_action", self.admin.get_list_display(self.request))
        Prescription.is_draft = False
        self.assertNotIn("add_action",
                         self.admin.get_list_display(self.request))
        # pre-burn
        self.request.GET = {'pre_burn': True}
        Prescription.is_draft = True
        self.assertEqual(("__str__", "details", "pre_burn_resolved",
                          "pre_burn_explanation"),
                         self.admin.get_list_display(self.request))
        Prescription.is_draft = False
        self.assertEqual(("__str__", "details", "pre_burn_resolved",
                          "pre_burn_explanation", "pre_burn_approved",
                          "pre_burn_approver"),
                         self.admin.get_list_display(self.request))

        # day-of-burn
        self.request.GET = {'day_of_burn': True}
        Prescription.is_draft = True
        self.assertEqual(("__str__", "details", "day_of_burn_include",
                          "day_of_burn_situation", "day_of_burn_mission",
                          "day_of_burn_execution", "day_of_burn_administration",
                          "day_of_burn_command"),
                         self.admin.get_list_display(self.request))
        Prescription.is_draft = False
        self.assertEqual(("__str__", "details", "day_of_burn_include",
                          "day_of_burn_situation", "day_of_burn_mission",
                          "day_of_burn_execution", "day_of_burn_administration",
                          "day_of_burn_command"),
                         self.admin.get_list_display(self.request))

        # post-burn
        self.request.GET = {'post_burn': True}
        Prescription.is_draft = True
        self.assertIn("add_action", self.admin.get_list_display(self.request))
        Prescription.is_draft = False
        self.assertNotIn("add_action",
                         self.admin.get_list_display(self.request))

    def test_get_list_editable(self):
        pass

    def test_get_readonly_fields(self):
        pass
