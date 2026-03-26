"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from django.core.exceptions import ValidationError
from django.utils.encoding import force_str

from pbs.tests import BasePbsTestCase

from pbs.risk.models import (RiskCategory, Risk, Action, Register, Treatment,
                             TreatmentLocation)


class ActionTests(BasePbsTestCase):
    def test_action_index_create(self):
        """
        Test that when a new action is created for the same risk, the indexes
        are updated correctly.
        """
        category = RiskCategory.objects.create(name='test')
        risk = Risk.objects.create(prescription=None, name='Test risk',
                                   category=category)
        action = Action.objects.create(risk=risk)
        self.assertEqual(action.index, 1)
        self.assertEqual(action.total, 1)

        action2 = Action.objects.create(risk=risk)
        action = Action.objects.get(pk=action.pk)
        self.assertEqual(action.index, 1)
        self.assertEqual(action.total, 2)
        self.assertEqual(action2.index, 2)
        self.assertEqual(action2.total, 2)

    def test_action_index_delete(self):
        """
        Test that when an action is deleted for the same risk, the indexes are
        updated correctly.
        """
        category = RiskCategory.objects.create(name='test')
        risk = Risk.objects.create(prescription=None, name='Test risk',
                                   category=category)
        actions = []
        for name in range(3):
            action = Action.objects.create(risk=risk, details=force_str(name))
            actions.append(action)

        # pop the first item and delete it
        action = actions.pop(0)
        action.delete()

        action1 = Action.objects.get(pk=actions[0].pk)
        action2 = Action.objects.get(pk=actions[1].pk)

        self.assertEqual(action1.index, 1)
        self.assertEqual(action1.total, 2)
        self.assertEqual(action2.index, 2)
        self.assertEqual(action2.total, 2)

    def test_day_of_burn_include(self):
        """
        Test validation of SMEAC briefing items.
        """
        category = RiskCategory.objects.create(name='test')
        risk = Risk.objects.create(prescription=None, name='Test risk',
                                   category=category)
        action = Action.objects.create(risk=risk, day_of_burn=True)

        action.day_of_burn_include = True
        with self.assertRaises(ValidationError) as error:
            action.full_clean()
            self.assertEqual(error.exception.messages_dict, {
                'day_of_burn_include': ["Please select at least one SMEAC "
                                        "location."]})

        items = ["day_of_burn_situation", "day_of_burn_mission",
                 "day_of_burn_execution", "day_of_burn_administration",
                 "day_of_burn_command"]

        for item in items:
            setattr(action, item, True)
            action.full_clean()
            setattr(action, item, False)


class RiskRegisterTests(BasePbsTestCase):
    def test_alarp_removes_treatments(self):
        """
        Test that setting a register item as alarp removes any treatments
        associated with it.
        """
        p = self.make('Prescription')
        register = Register.objects.create(prescription=p)
        location = TreatmentLocation.objects.get(pk=1)
        Treatment.objects.create(register=register, location=location,
                                 description="Test treatment")
        self.assertEqual(Treatment.objects.count(), 1)
        register.alarp = True
        register.save()
        self.assertEqual(Treatment.objects.count(), 0)
