from selenium.common.exceptions import NoSuchElementException

from django.conf import settings
from django.urls import reverse

from pbs.document.models import Document, DocumentCategory, DocumentTag
from pbs.prescription.models import (Prescription, Purpose, RegionalObjective,
                                     Region, Objective, SuccessCriteria,
                                     PriorityJustification)
from pbs.prescription.tests.tests import set_cbas_attributes
from pbs.risk.models import Complexity, Register
from pbs.tests import SeleniumTestCase


class RegionalFireCoordinatorSeleniumTestCase(SeleniumTestCase):
    def setUp(self):
        self.login('admin', 'test')

    def test_browse_to_changelist(self):
        """
        Test browsing to the changelist from the index page.
        """
        url = reverse('admin:index')
        self.selenium.get(self.live_server_url + url)
        self.selenium.find_element_by_partial_link_text("Welcome,").click()
        self.selenium.find_element_by_link_text("Manage Regional Fire Coordinators").click()
        self.wait_page_loaded()
        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Manage Regional Fire Management Plan Objectives")

    def test_browse_to_add_form(self):
        """
        Test browsing to the add page from the change list.
        """
        url = reverse('admin:prescription_regionalobjective_changelist')
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()
        text = "Create Regional Fire Management Plan Objective"
        self.selenium.find_element_by_partial_link_text(text).click()
        self.wait_page_loaded()
        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Add Regional Fire Management Plan Objective")

    def test_create_rfmp_without_fma(self):
        """
        Test creating a regional fire management plan objective without a fire
        management area.
        """
        url = reverse('admin:prescription_regionalobjective_add')
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        region = "//select[@id='id_region']/option[text()='Goldfields']"
        self.selenium.find_element_by_xpath(region).click()

        objectives = 'test'
        self.selenium.find_element_by_id('id_objectives').send_keys(objectives)
        fma_names = self.selenium.find_element_by_id('id_fma_names')
        self.assertFalse(fma_names.is_enabled())
        self.selenium.find_element_by_name('_save').click()
        self.wait_page_loaded()
        self.assertEqual(
            self.selenium.find_element_by_class_name('alert').text,
            'The Regional Fire Management Plan Objective "%s" '
            'was added successfully.' % objectives)
        self.assertEqual(RegionalObjective.objects.count(), 1)

    def test_create_rfmp_with_fma(self):
        """
        Test creating a regional fire management plan objective with a fire
        management area.
        """
        url = reverse('admin:prescription_regionalobjective_add')
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        region = "//select[@id='id_region']/option[text()='Goldfields']"
        self.selenium.find_element_by_xpath(region).click()

        fma = "//select[@id='id_impact']/option[text()='Fire Management Area']"
        self.selenium.find_element_by_xpath(fma).click()

        objectives = 'test'
        self.selenium.find_element_by_id('id_objectives').send_keys(objectives)
        fma_names = self.selenium.find_element_by_id('id_fma_names')
        self.assertTrue(fma_names.is_enabled())
        fma_names.send_keys('test')
        self.selenium.find_element_by_name('_save').click()
        self.wait_page_loaded()
        self.assertEqual(
            self.selenium.find_element_by_class_name('alert').text,
            'The Regional Fire Management Plan Objective "%s" '
            'was added successfully.' % objectives)
        self.assertEqual(RegionalObjective.objects.count(), 1)

    def test_edit_rfmp(self):
        """
        Test editing an existing Regional Fire Coordinator.
        """
        RegionalObjective.objects.create(
            region=Region.objects.get(pk=1), objectives='Test objective')
        url = reverse('admin:prescription_regionalobjective_changelist')
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        td = '//tr/td[@class="column-objectives" and text()="Test objective"]'
        self.selenium.find_element_by_xpath(td + '/../th/a').click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Change Regional Fire Management Plan Objective")

        # this regional objective has regional impact, check that the fma
        # input is disabled as it should be.
        fma_names = self.selenium.find_element_by_id('id_fma_names')
        self.assertFalse(fma_names.is_enabled())

        # change the regional objective to have a fire management area impact
        fma = "//select[@id='id_impact']/option[text()='Fire Management Area']"
        self.selenium.find_element_by_xpath(fma).click()

        # check that the input is now enabled.
        fma_names = self.selenium.find_element_by_id('id_fma_names')
        self.assertTrue(fma_names.is_enabled())

        # change the objectives
        text = "Another objective"
        objectives = self.selenium.find_element_by_id('id_objectives')
        objectives.clear()
        objectives.send_keys(text)

        self.selenium.find_element_by_name('_save').click()
        self.wait_page_loaded()
        self.assertEqual(
            self.selenium.find_element_by_class_name('alert').text,
            'The Regional Fire Management Plan Objective "%s" '
            'was changed successfully.' % text)
        self.assertEqual(RegionalObjective.objects.count(), 1)

    def test_edit_rfmp_cancel(self):
        """
        Test clicking cancel while editing an Regional Fire Coordinator.
        """
        objective = RegionalObjective.objects.create(
            region=Region.objects.get(pk=1), objectives='Test objective')
        url = reverse('admin:prescription_regionalobjective_change',
                      args=(str(objective.pk),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()
        self.selenium.find_element_by_id('id_cancel_button').click()
        self.wait_page_loaded()
        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Manage Regional Fire Management Plan Objectives")
        self.assertEqual(RegionalObjective.objects.count(), 1)

    def test_delete_rfmp(self):
        """
        Test deleting an Regional Fire Coordinator.
        """
        objective = RegionalObjective.objects.create(
            region=Region.objects.get(pk=1), objectives='Test objective')
        url = reverse('admin:prescription_regionalobjective_change',
                      args=(str(objective.pk),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()
        self.selenium.find_element_by_id('id_delete_button').click()
        self.wait_page_loaded()
        self.selenium.find_element_by_xpath("//input[@type='submit']").click()
        self.wait_page_loaded()
        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Manage Regional Fire Management Plan Objectives")
        self.assertEqual(RegionalObjective.objects.count(), 0)


class ComplexityAnalysisSummarySeleniumTestCase(SeleniumTestCase):
    def setUp(self):
        self.selenium.maximize_window()
        self.login('admin', 'test')

    def test_browse_to_complexity_analysis(self):
        """
        Test browse to the 'Section A5 - Prescribed burn complexity analysis
        summary' page.
        2.7.4 Event 1
        """
        prescription = self.make('Prescription')
        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                        args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_partial_link_text(
                        'Section A5').click()
        self.wait_page_loaded()

        self.assertEqual("Prescribed Burn Complexity Analysis Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)

    def test_add_complexity_info_and_save(self):
        """
        Test adding all the complexity ratings and rationales
        and save successfully
        2.7.4 Event 2
        """
        prescription = self.make('Prescription')
        # Go directly to the 'Prescribed Burn Complexity Analysis Summary' page
        url = reverse('admin:risk_complexity_changelist',
                        args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        counter = 0
        num_complexities = len(
            Complexity.objects.filter(prescription=prescription))

        for counter in range(num_complexities):
            rating_css_selector = r'#id_form-%s-rating > option[value="3"]' % str(counter)
            rationale_id = 'id_form-%s-rationale' % str(counter)
            self.selenium.find_element_by_css_selector(
                rating_css_selector).click()
            self.selenium.find_element_by_id(
                rationale_id).send_keys('Testing Complexity Rationale Text')
            counter = counter + 1

        self.selenium.find_element_by_name('_save').click()
        self.wait_page_loaded()

        try:
            # If a success element is found then it submitted successfully.
            self.selenium.find_element_by_class_name('alert-success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

class BurnObjectivesSuccessCriteriaSeleniumTestCase(SeleniumTestCase):
    def setUp(self):
        self.login('admin', 'test')

    def test_browse_to_burn_objectives(self):
        """
        Test browse to the 'Section A3 - Burn Objectives' page
        2.6.4 Event 1
        """
        prescription = self.create_initial_data()
        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                        args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_partial_link_text(
                        'Burn objectives').click()
        self.wait_page_loaded()

        self.assertEqual("Burn Objectives",
                      self.selenium.find_elements_by_tag_name('h1')[2].text)

    def test_add_burn_objective(self):
        """
        Test if the user entry text field displays after clicking the
        link 'Add another objective' on the Burn Objectives page.
        2.6.4 Event 4a
        """
        prescription = self.create_initial_data()
        # Go directly to the 'Burn Objectives' page
        url = reverse('admin:prescription_objective_changelist',
                        args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the button 'Add another objective'
        self.selenium.find_element_by_partial_link_text(
            'Add another objective').click()
        self.selenium.implicitly_wait(1)

        # Check the text box has appeared
        try:
            self.selenium.find_element_by_id('id_form-1-objectives')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

    def test_save_burn_objective(self):
        """
        Test to Save a new Burn Objective after typing it into the
        user entry text field on the Burn Objectives page.
        2.6.4 Events 4b & 5
        """
        prescription = self.create_initial_data()
        # Go directly to the 'Burn Objectives' page
        url = reverse('admin:prescription_objective_changelist',
                        args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the button 'Add another objective'
        self.selenium.find_element_by_partial_link_text(
            'Add another objective').click()
        self.selenium.implicitly_wait(1)

        # Type something in the text box
        self.selenium.find_element_by_id(
                'id_form-1-objectives').send_keys('This is a Burn Objective.')
        # Click the Save button
        self.selenium.find_element_by_name('_save').click()

        try:
            # If a success element is found then it submitted successfully.
            self.selenium.find_element_by_class_name('alert-success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

    def test_add_burn_objective_navigate_away(self):
        """
        Test to navigate away from page before saving a Burn Objective.
        Expect alert prompt by browser to leave page.
        2.6.4 Event 6a
        """
        prescription = self.create_initial_data()
        # Go directly to the 'Burn Objectives' page
        url = reverse('admin:prescription_objective_changelist',
                        args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the button 'Add another objective'
        self.selenium.find_element_by_partial_link_text(
            'Add another objective').click()
        self.selenium.implicitly_wait(1)

        # Type something in the text box
        self.selenium.find_element_by_id(
                'id_form-1-objectives').send_keys('This is a Burn Objective.')
        # Click a link to navigate away from the page
        self.selenium.find_element_by_link_text('Part A').click()

        # Check that an alert popped up
        try:
            alert = self.selenium.switch_to_alert()
            alert_exists = True
        except:
            alert_exists = False # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                        args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_partial_link_text(
                        'Burn objectives').click()
        self.wait_page_loaded()

        self.assertEqual("Burn Objectives",
                      self.selenium.find_elements_by_tag_name('h1')[2].text)
        self.assertEqual(alert_exists, True)
        # Check the text in the alert
        self.assertIn(
            'data you have entered may not be saved',
            alert.text
        )

    def test_add_burn_objective_navigate_away_dismiss(self):
        """
        Test to navigate away from page before saving a Burn Objective.
        Click 'Stay on Page' button, expects to stay on the page.
        2.6.4 Event 6b
        """
        prescription = self.create_initial_data()
        # Go directly to the 'Burn Objectives' page
        url = reverse('admin:prescription_objective_changelist',
                        args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the button 'Add another objective'
        self.selenium.find_element_by_partial_link_text(
            'Add another objective').click()
        self.selenium.implicitly_wait(1)

        # Type something in the text box
        self.selenium.find_element_by_id(
                'id_form-1-objectives').send_keys('This is a Burn Objective.')
        # Click a link to navigate away from the page
        self.selenium.find_element_by_link_text('Part A').click()

        alert = self.selenium.switch_to_alert()
        # Click the 'Stay on Page' button by sending a dismiss command
        alert.dismiss()

        # Check that we're still on the same page
        self.assertEqual("Burn Objectives",
                      self.selenium.find_elements_by_tag_name('h1')[2].text)

    def test_add_burn_objective_navigate_away_accept(self):
        """
        Test to navigate away from page before saving a Burn Objective.
        Click 'Stay on Page' button, expects to stay on the page.
        2.6.4 Event 6b
        """
        prescription = self.create_initial_data()
        # Go directly to the 'Burn Objectives' page
        url = reverse('admin:prescription_objective_changelist',
                        args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the button 'Add another objective'
        self.selenium.find_element_by_partial_link_text(
            'Add another objective').click()
        self.selenium.implicitly_wait(1)

        # Type something in the text box
        self.selenium.find_element_by_id(
                'id_form-1-objectives').send_keys('This is a Burn Objective.')
        # Click a link to navigate away from the page
        self.selenium.find_element_by_link_text('Part A').click()

        alert = self.selenium.switch_to_alert()
        # Click the 'Leave Page' button by sending an accept command
        alert.accept()

        # Check that we're no longer on the Burn Objectives page
        h1_tags = self.selenium.find_elements_by_tag_name('h1')
        burn_tag_exists = False
        for tag in h1_tags:
            if tag.text == 'Burn Objectives':
                burn_tag_exists = True

        self.assertEqual(burn_tag_exists, False)

    def test_browse_to_successcriteria(self):
        """
        Test to navigate to the 'Section A3 - Success criteria' page
        and checks if created Regional Fire Coordinators and Burn Objectives are there.
        2.6.4 Event 7
        """
        prescription = self.create_initial_data()

         # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                        args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_partial_link_text(
                        'Success criteria').click()
        self.wait_page_loaded()

        self.assertEqual("Success Criteria",
                      self.selenium.find_elements_by_tag_name('h1')[4].text)

    def test_save_success_criteria(self):
        """
        Test to Save a new Success Criteria after typing it into the
        user entry text field on the Success Criteria page.
        2.6.4 Events 7 & 8
        """
        prescription = self.create_initial_data()
        # Go directly to the 'Success Criteria' page
        url = reverse('admin:prescription_successcriteria_changelist',
                        args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the button 'Add another success criteria'
        self.selenium.find_element_by_partial_link_text(
            'Add another success criteria').click()
        self.selenium.implicitly_wait(1)

        # Type something in the text box
        self.selenium.find_element_by_id(
                'id_form-1-criteria').send_keys('This is a Success Criteria.')
        # Click the Save button
        self.selenium.find_element_by_name('_save').click()

        try:
            # If a success element is found then it submitted successfully.
            self.selenium.find_element_by_class_name('alert-success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

    def create_initial_data(self):

        # Create a fire plan application
        prescription = self.make('Prescription')

        # Get the 'Research' Burn Purpose object
        purpose_research = Purpose.objects.get(name='Research')

        # Get a region
        swan_region = Region.objects.get(name='Swan')

        # Create Regional Fire Coordinator
        rfmp1 = RegionalObjective.objects.create(
            region=swan_region,
            impact=RegionalObjective.IMPACT_REGION,
            objectives="A testing Regional Fire Coordinator for a Region."
        )
        rfmp2 = RegionalObjective.objects.create(
            region=swan_region,
            impact=RegionalObjective.IMPACT_FMA,
            fma_names="FMA Name",
            objectives="A testing Regional Fire Coordinator for a Fire Management Area."
        )

        # Update the prescription
        prescription.regional_objectives.add(rfmp1)
        prescription.regional_objectives.add(rfmp2)
        prescription.purposes.add(purpose_research)
        prescription.save()

        # Add a Burn Objective
        objective = Objective.objects.create(
            objectives="A programmatically created burn objective for testing",
            prescription=prescription
        )

        # Add a success criteria
        success_criteria = SuccessCriteria(
            prescription=prescription,
            criteria="A programmatically created success criterion for testing"
        )
        success_criteria.save()

        return prescription


class SummaryAndApprovalSeleniumTestCase(SeleniumTestCase):
    def setUp(self):
        self.login('admin', 'test')

    def test_browse_to_epfp_part_a_summary(self):
        """
        Test browse to Part A Summary page from ePFP page.
        2.5.4 Event 1
        """
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        # Go to the ePFP Overview page
        url = reverse('admin:prescription_prescription_detail',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the link
        self.selenium.find_element_by_link_text('Part A').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)

    def test_complete_section_a1_fail(self):
        """
        Test 'Complete' Section A1 before valid to do so.
        Expect no error message, and success class on the row.
        2.5.4 Event 2
        """
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
                        '#id_summary > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If an error element is found then the test is successful.
            self.selenium.find_element_by_class_name('text-error')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

        self.assertEqual(self.selenium.find_element_by_id(
                        'id_summary').get_attribute("value"), 'false')

    def test_complete_section_a1_pass(self):
        """
        Test 'Complete' Section A1 when valid to do so.
        Expect no error message and system to accept Complete status.
        2.5.4 Events 2 & 3
        """
        # Create a complete fire plan application before anything
        prescription = self.make('Prescription')
        set_cbas_attributes(self, prescription)

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
                        '#id_summary > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If a success element is found then the test is successful.
            self.selenium.find_element_by_class_name('success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

        self.assertEqual(self.selenium.find_element_by_id(
                        'id_summary').get_attribute("value"), 'true')

    def test_complete_section_a2_riskmanagement_pass(self):
        """
        Test 'Complete' Section A2 Risk Management Context when valid to do so.
        Expect no error message and system to accept Complete status.
        2.5.4 Events 2 & 3
        """
        # Create a complete fire plan application before anything
        prescription = self.make('Prescription')
        set_cbas_attributes(self, prescription)

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
                    '#id_context_statement > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If a success element is found then the test is successful.
            self.selenium.find_element_by_class_name('success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

        self.assertEqual(self.selenium.find_element_by_id(
                        'id_context_statement').get_attribute("value"), 'true')

    def test_complete_section_a2_contextmap_fail(self):
        """
        Test 'Complete' Section A2 Context Map before valid to do so.
        Expect error message and system to set it back to Incomplete.
        2.5.4 Event 2
        """
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
                    '#id_context_map > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If an error element is found then the test is successful.
            self.selenium.find_element_by_class_name('text-error')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

        self.assertEqual(self.selenium.find_element_by_id(
                        'id_context_map').get_attribute("value"), 'false')

    def test_complete_section_a2_contextmap_pass(self):
        """
        Test 'Complete' Section A2 Context Map when valid to do so.
        Expect no error message and system to accept Complete status.
        2.5.4 Events 2 & 3
        """
        # Create a complete fire plan application before anything
        prescription = self.make('Prescription')
        set_cbas_attributes(self, prescription)

        # Store a document for the Context Map
        doc_category = DocumentCategory(name='Doc Name', order=1)
        doc_category.save()

        doc_tag = DocumentTag(name='Context Map', category=doc_category)
        doc_tag.save()

        doc = Document(
            prescription=prescription,
            category=doc_category,
            tag=doc_tag,
            custom_tag='Custom Tag',
            document=settings.STATIC_ROOT + 'pbs/docs/org_chart.pdf'
            #document=settings.STATIC_ROOT + '/docs/org_chart.pdf'
        )
        doc.save()

        self.assertTrue(Document.objects.tag_names("Context Map").count(), 1)

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
                    '#id_context_map > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If a success element is found then the test is successful.
            self.selenium.find_element_by_class_name('success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

        self.assertEqual(self.selenium.find_element_by_id(
                        'id_context_map').get_attribute("value"), 'true')

    def test_complete_section_a3_burnobjectives_fail(self):
        """
        Test 'Complete' Section A3 Burn Objectives before valid to do so.
        Expect error message and system to set it back to Incomplete.
        2.5.4 Event 2
        """
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
                    '#id_objectives > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If an error element is found then the test is successful.
            self.selenium.find_element_by_class_name('text-error')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)
        self.assertEqual(self.selenium.find_element_by_id(
                        'id_objectives').get_attribute("value"), 'false')

    def test_complete_section_a3_burnobjectives_pass(self):
        """
        Test 'Complete' Section A3 Burn Objectives when valid to do so.
        Expect no error message and system to accept Complete status.
        2.5.4 Events 2 & 3
        """
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        # Store an Objective for the Burn Purpose
        burn_objective = Objective(
            objectives='A burn objective',
            prescription=prescription
        )
        burn_objective.save()

        self.assertTrue(Objective.objects.all().count(), 1)

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
                    '#id_objectives > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If a success element is found then the test is successful.
            self.selenium.find_element_by_class_name('success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)
        self.assertEqual(self.selenium.find_element_by_id(
                        'id_objectives').get_attribute("value"), 'true')

    def test_complete_section_a3_successcriteria_fail(self):
        """
        Test 'Complete' Section A3 Success Criteria before valid to do so.
        Expect error message and system to set it back to Incomplete.
        2.5.4 Event 2
        """
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
                    '#id_success_criteria > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If an error element is found then the test is successful.
            self.selenium.find_element_by_class_name('text-error')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

        self.assertEqual(self.selenium.find_element_by_id(
                        'id_success_criteria').get_attribute("value"), 'false')

    def test_complete_section_a3_successcriteria_pass(self):
        """
        Test 'Complete' Section A3 Success Criteria when valid to do so.
        Expect no error message and system to accept Complete status.
        2.5.4 Event 2
        """
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        # Store a success criteria
        success_criteria = SuccessCriteria(
            prescription=prescription,
            criteria="Some success criterion"
        )
        success_criteria.save()

        self.assertTrue(SuccessCriteria.objects.all().count(), 1)

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
                    '#id_success_criteria > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If a success element is found then the test is successful.
            self.selenium.find_element_by_class_name('success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

        self.assertEqual(self.selenium.find_element_by_id(
                        'id_success_criteria').get_attribute("value"), 'true')

    def test_complete_section_a4_fail(self):
        """
        Test 'Complete' Section A4 before valid to do so.
        Expect error message and system to set it back to Incomplete.
        2.5.4 Event 2
        """
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
            '#id_priority_justification > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If an error element is found then the test is successful.
            self.selenium.find_element_by_class_name('text-error')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

        self.assertEqual(self.selenium.find_element_by_id(
                'id_priority_justification').get_attribute("value"), 'false')

    def test_complete_section_a4_pass(self):
        """
        Test 'Complete' Section A4 when valid to do so.
        Expect no error message and system to accept Complete status.
        2.5.4 Event 2
        """
        # Create a fire plan application before anything
        prescription = self.make('Prescription')
        prescription.priority = Prescription.PRIORITY_MEDIUM
        prescription.rationale = "An overall rationale"
        prescription.save()

        # Store a Purpose object
        # 'Research' is one of the available options the system allows
        purpose = Purpose(name="Research")
        purpose.save()
        # Store a Burn Priority Justification object
        priority_justif = PriorityJustification(
            prescription=prescription,
            purpose=purpose,
            priority=PriorityJustification.PRIORITY_MEDIUM,
            rationale="Rationale for Research burn purpose"
        )
        priority_justif.save()

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
            '#id_priority_justification > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If a success element is found then the test is successful.
            self.selenium.find_element_by_class_name('success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

        self.assertEqual(self.selenium.find_element_by_id(
                'id_priority_justification').get_attribute("value"), 'true')

    def test_complete_section_a5_fail(self):
        """
        Test 'Complete' Section A5 before valid to do so.
        Expect error message and system to set it back to Incomplete.
        2.5.4 Event 2
        """
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
                '#id_complexity_analysis > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If an error element is found then the test is successful.
            self.selenium.find_element_by_class_name('text-error')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

        self.assertEqual(self.selenium.find_element_by_id(
                    'id_complexity_analysis').get_attribute("value"), 'false')

    def test_complete_section_a5_pass(self):
        """
        Test 'Complete' Section A5 when valid to do so.
        Expect no error message and system to accept Complete status.
        2.5.4 Event 2
        """
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        # Store Rating & Rationale data into all the
        # Complexity Objects belonging to this Prescription
        complexities = Complexity.objects.filter(prescription=prescription)
        for complexity in complexities:
            complexity.rating = Complexity.RATING_MEDIUM
            complexity.rationale = 'A Complexity Rationale'
            complexity.save()

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
                '#id_complexity_analysis > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If no error element is found then the test is successful.
            self.selenium.find_element_by_class_name('success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

        self.assertEqual(self.selenium.find_element_by_id(
                    'id_complexity_analysis').get_attribute("value"), 'true')

    def test_complete_section_a6_fail(self):
        """
        Test 'Complete' Section A6 before valid to do so.
        Expect error message and system to set it back to Incomplete.
        2.5.4 Event 2
        """
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
                    '#id_risk_register > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If an error element is found then the test is successful.
            self.selenium.find_element_by_class_name('text-error')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

        self.assertEqual(self.selenium.find_element_by_id(
                        'id_risk_register').get_attribute("value"), 'false')

    def test_complete_section_a6_pass(self):
        """
        Test 'Complete' Section A6 when valid to do so.
        Expect no error message and system to accept Complete status.
        2.5.4 Event 2
        """
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        # Store a Register object for the Prescription
        register = Register(
            prescription=prescription,
            draft_consequence=Register.CONSEQUENCE_CATASTROPHIC,
            draft_likelihood=Register.LIKELIHOOD_CERTAIN
        )
        register.save()

        # Go to the Part A Summary - Summary & Approval page
        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.pk)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.find_element_by_css_selector(
                    '#id_risk_register > option[value="True"]').click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If no error element is found then the test is successful.
            self.selenium.find_element_by_class_name('success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

        self.assertEqual(self.selenium.find_element_by_id(
                        'id_risk_register').get_attribute("value"), 'true')


class BurnPriorityJustificationSeleniumTestCase(SeleniumTestCase):
    def setUp(self):
        self.login('admin', 'test')

    def test_browse_to_priority_justification(self):
        """
        Test browsing to the Burn Priority Justification page.
        2.3.4 Event 1
        """
        self.selenium.maximize_window()
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.id)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the link
        self.selenium.find_element_by_partial_link_text(
                        'Section A4').click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Burn Priority Justification")

    def test_save_priority_justification_good_data(self):
        """
        Test save Burn Priority Justification, priorities and rationales.
        2.3.4 Event 2
        """
        self.selenium.maximize_window()
        # Create a complete fire plan application
        prescription = self.make('Prescription')
        set_cbas_attributes(self, prescription)

        # Load the Burn Priority Justification page
        url = reverse('admin:prescription_priorityjustification_changelist',
                      args=(str(prescription.id)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Fill out the form completely and click the Save button
        self.selenium.find_element_by_css_selector(
                        '#id_priority > option[value=\"2\"]').click()
        self.selenium.find_element_by_id('id_rationale').send_keys(
                    'Overall rationale text')
        self.selenium.find_element_by_id('id_form-0-rationale').send_keys(
                    'Rationale text for this burn purpose')
        self.selenium.find_element_by_css_selector(
                        '#id_form-0-priority > option[value=\"2\"]').click()
        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Burn Priority Justification")
        try:
            # If a success element is found then it submitted successfully.
            self.selenium.find_elements_by_class_name('alert-success')[0]
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

    def test_save_priority_justification_no_overall_priority(self):
        """
        Test save with missing Overall Priority on the Burn Priority
        Justification page.
        2.3.4 Events 2 and 4.
        """
        self.selenium.maximize_window()
        # Create a complete fire plan application
        prescription = self.make('Prescription')
        set_cbas_attributes(self, prescription)

        # Load the Burn Priority Justification page
        url = reverse('admin:prescription_priorityjustification_changelist',
                      args=(str(prescription.id)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Fill out the form (except Overall Priority) and click the Save button
        self.selenium.find_element_by_css_selector(
                        '#id_priority > option[value=\"0\"]').click()
        self.selenium.find_element_by_id('id_rationale').send_keys(
                    'Overall rationale text')
        self.selenium.find_element_by_id('id_form-0-rationale').send_keys(
                    'Rationale text for this burn purpose')
        self.selenium.find_element_by_css_selector(
                        '#id_form-0-priority > option[value=\"2\"]').click()
        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Burn Priority Justification")
        try:
            # If an error element is found then the test is successful.
            self.selenium.find_elements_by_class_name('alert-error')[0]
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

    def test_save_priority_justification_no_overall_rationale(self):
        """
        Test save with missing Overall Rationale on the Burn Priority
        Justification page.
        2.3.4 Events 2 and 4.
        """
        self.selenium.maximize_window()
        # Create a complete fire plan application
        prescription = self.make('Prescription')
        set_cbas_attributes(self, prescription)

        # Load the Burn Priority Justification page
        url = reverse('admin:prescription_priorityjustification_changelist',
                      args=(str(prescription.id)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Fill out the form (except Overall Rationale) and click the Save button
        self.selenium.find_element_by_css_selector(
                        '#id_priority > option[value=\"2\"]').click()
        self.selenium.find_element_by_id('id_form-0-rationale').send_keys(
                    'Rationale text for this burn purpose')
        self.selenium.find_element_by_css_selector(
                        '#id_form-0-priority > option[value=\"2\"]').click()
        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Burn Priority Justification")
        try:
            # If an error element is found then the test is successful.
            self.selenium.find_elements_by_class_name('alert-error')[0]
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

    def test_save_priority_justification_no_burn_purpose_rationale(self):
        """
        Test save with a missing burn purpose Rationale on the Burn Priority
        Justification page.
        2.3.4 Events 2 and 4.
        """
        self.selenium.maximize_window()
        # Create a complete fire plan application
        prescription = self.make('Prescription')
        set_cbas_attributes(self, prescription)

        # Load the Burn Priority Justification page
        url = reverse('admin:prescription_priorityjustification_changelist',
                      args=(str(prescription.id)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Fill out the form (except the specific burn purpose Rationale)
        # and click the Save button
        self.selenium.find_element_by_css_selector(
                        '#id_priority > option[value=\"2\"]').click()
        self.selenium.find_element_by_id('id_rationale').send_keys(
                    'Overall rationale text')
        self.selenium.find_element_by_css_selector(
                        '#id_form-0-priority > option[value=\"2\"]').click()
        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Burn Priority Justification")
        try:
            # If an error element is found then the test is successful.
            self.selenium.find_elements_by_class_name('alert-error')[0]
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

    def test_save_priority_justification_no_burn_purpose_priority(self):
        """
        Test save with a missing burn purpose Priority on the Burn Priority
        Justification page.
        2.3.4 Events 2 and 4.
        """
        self.selenium.maximize_window()
        # Create a complete fire plan application
        prescription = self.make('Prescription')
        set_cbas_attributes(self, prescription)

        # Load the Burn Priority Justification page
        url = reverse('admin:prescription_priorityjustification_changelist',
                      args=(str(prescription.id)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Fill out the form (except the specific burn purpose Rationale)
        # and click the Save button
        self.selenium.find_element_by_css_selector(
                        '#id_priority > option[value=\"2\"]').click()
        self.selenium.find_element_by_id('id_rationale').send_keys(
                    'Overall rationale text')
        self.selenium.find_element_by_id('id_form-0-rationale').send_keys(
                    'Rationale text for this burn purpose')
        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Burn Priority Justification")
        try:
            # If an error element is found then the test is successful.
            self.selenium.find_elements_by_class_name('alert-error')[0]
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

    def test_browse_edit_priority_justification(self):
        """
        Test browse to edit Priority/Rationale info on the Burn Priority
        Justification page and save it.
        2.3.4 Event 3
        """
        self.selenium.maximize_window()
        # Create a fire plan application before anything
        prescription = self.make('Prescription')
        set_cbas_attributes(self, prescription)

        url = reverse('admin:prescription_prescription_summary',
                      args=(str(prescription.id)))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the link
        self.selenium.find_element_by_partial_link_text(
                        'Section A4').click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Burn Priority Justification")

        # Fill out the form completely and click the Save button
        self.selenium.find_element_by_css_selector(
                        '#id_priority > option[value=\"2\"]').click()
        self.selenium.find_element_by_id('id_rationale').send_keys(
                    'Overall rationale text')
        self.selenium.find_element_by_id('id_form-0-rationale').send_keys(
                    'Rationale text for this burn purpose')
        self.selenium.find_element_by_css_selector(
                        '#id_form-0-priority > option[value=\"2\"]').click()
        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Burn Priority Justification")
        try:
            # If a success element is found then it submitted successfully.
            self.selenium.find_elements_by_class_name('alert-success')[0]
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)


class PrescribedFirePlanSeleniumTestCase(SeleniumTestCase):
    def setUp(self):
        self.login('admin', 'test')

    def test_browse_to_add_fire_plan(self):
        """
        Test browsing to add a new fire plan from the index page.
        2.2.4 Event 1.
        """
        url = reverse('admin:index')
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()
        self.selenium.maximize_window()

        self.selenium.find_element_by_link_text(
            "Create Prescribed Burn").click()
        self.wait_page_loaded()
        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Create Prescribed Burn")

    def test_add_fire_plan_good_data(self):
        """
        Test to fill in the Create Prescribed Burn form with good data and
        save. 2.2.4 Event 2.
        """
        url = reverse('admin:prescription_prescription_add')
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.maximize_window()
        self.fill_in_form(True, True, True, True)

        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()
        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "ePFP Overview")

    def test_add_fire_plan_no_name(self):
        """
        Test to fill in the Create Prescribed Burn form without the Name
        field being filled out.
        2.2.4 Event 2.
        """
        url = reverse('admin:prescription_prescription_add')
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.maximize_window()
        self.fill_in_form(False, True, True, True)

        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()
        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Create Prescribed Burn")

    def test_add_fire_plan_no_planned_burn_season(self):
        """
        Test to fill in the Create Prescribed Burn form without a Planned
        Burn Season dropdown option being selected.
        2.2.4 Event 2.
        """
        url = reverse('admin:prescription_prescription_add')
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.maximize_window()
        self.fill_in_form(True, False, True, True)

        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()
        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Create Prescribed Burn")

    def test_add_fire_plan_no_contentious(self):
        """
        Test to fill in the Create Prescribed Burn form without a
        Contentious dropdown option being selected.
        2.2.4 Event 2.
        """
        url = reverse('admin:prescription_prescription_add')
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.maximize_window()
        self.fill_in_form(True, True, False, True)

        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()
        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Create Prescribed Burn")

    def test_add_fire_plan_no_burn_purpose(self):
        """
        Test to fill in the Create Prescribed Burn form without
        any of the Burn Options checkboxes selected.
        2.2.4 Event 2.
        """
        url = reverse('admin:prescription_prescription_add')
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        self.selenium.maximize_window()
        self.fill_in_form(True, True, True, False)

        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()
        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Create Prescribed Burn")

    def test_choose_existing_fire_plan(self):
        """
        Test to select an existing burn application and go to its Overview page
        2.2.4 Event 3.
        """
        self.selenium.maximize_window()
        # Create a fire plan application before anything
        self.make('Prescription')

        # Refresh the Regional Overview page to click the created prescription
        self.selenium.find_element_by_link_text('Regional Overview').click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Regional Overview")

        self.selenium.find_element_by_link_text('KAL_001').click()
        self.wait_page_loaded()
        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "ePFP Overview")

    def test_browse_summary_and_approval_workflow_1(self):
        """
        Test to browse to the Summary and Approval page - 1st workflow method.
        2.2.4 Event 4.
        """
        self.selenium.maximize_window()
        # Create a fire plan application before anything
        self.make('Prescription')

        # Refresh the Regional Overview page to click the created prescription
        self.selenium.find_element_by_link_text('Regional Overview').click()
        self.wait_page_loaded()
        self.selenium.find_element_by_link_text('KAL_001').click()
        self.wait_page_loaded()
        self.selenium.find_element_by_link_text('Summary & Approval').click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Summary & Approval")

    def test_browse_summary_and_approval_workflow_2(self):
        """
        Test to browse to the Summary and Approval page - 2nd workflow method.
        2.2.4 Event 4.
        """
        self.selenium.maximize_window()
        # Create a fire plan application before anything
        self.make('Prescription')

        # Refresh the Regional Overview page to click the created prescription
        self.selenium.find_element_by_link_text('Regional Overview').click()
        self.wait_page_loaded()
        self.selenium.find_element_by_link_text('KAL_001').click()
        self.wait_page_loaded()

        self.selenium.find_element_by_link_text('Part A').click()
        self.wait_page_loaded()

        self.selenium.find_element_by_partial_link_text(
            'Section A1').click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Summary & Approval")

    def test_browse_edit_overall_priority(self):
        """
        Test to browse to Edit Overall Burn priority.
        2.2.4 Event 5.
        """
        self.selenium.maximize_window()
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        url = reverse('admin:prescription_prescription_pre_summary',
                      args=(str(prescription.id),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click Edit for the overall priority
        overall_priority = self.selenium.find_element_by_id('id_td_priority')
        overall_priority.find_element_by_link_text('Edit').click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Burn Priority Justification")

    def test_browse_edit_overall_rationale(self):
        """
        Test to browse to Edit Overall Burn rationale.
        2.2.4 Event 6.
        """
        self.selenium.maximize_window()
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        url = reverse('admin:prescription_prescription_pre_summary',
                      args=(str(prescription.id),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click Edit for the overall priority
        overall_priority = self.selenium.find_element_by_id('id_td_rationale')
        overall_priority.find_element_by_link_text('Edit').click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         "Burn Priority Justification")

    def test_browse_to_submit_corporate_approval_incomplete(self):
        """
        Test to browse to Submit for Corporate Approval for the burn
        application. When all necessary input has not been filled.
        2.2.4 Event 7
        """
        self.selenium.maximize_window()
        # Create a fire plan application before anything
        prescription = self.make('Prescription')

        # Go to the ePFP Overview page
        url = reverse('admin:prescription_prescription_detail',
                      args=(str(prescription.id),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the link
        self.selenium.find_element_by_link_text(
            'Submit for corporate approval').click()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         'Submit for Corporate Approval')

        self.assertIn(
            'Click here to navigate to Section',
            self.selenium.find_element_by_partial_link_text(
            'Click here to navigate to Section').text
        )

    def test_browse_to_submit_corporate_approval_complete(self):
        """
        Test to browse to Submit for Corporate Approval for the burn
        application. When all necessary input is correctly filled.
        2.2.4 Event 7
        """
        self.selenium.maximize_window()
        # Create a complete fire plan application before anything
        prescription = self.make('Prescription')
        self.set_cbas_attributes(prescription)

        # Go to the ePFP Overview page
        url = reverse('admin:prescription_prescription_detail',
                      args=(str(prescription.id),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the link
        self.selenium.find_element_by_link_text(
            'Submit for corporate approval').click()
        self.wait_page_loaded()

        self.assertEqual(self.selenium.find_elements_by_tag_name('h1')[1].text,
                         'Submit for Corporate Approval')

        try:
            # If the string below is not found, then it is good to approve.
            self.selenium.find_element_by_partial_link_text(
                'Click here to navigate to Section')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertFalse(exists)

    def test_submit_corporate_approval(self):
        """
        Test to click the Submit button on the
        Submit for Corporate Approval page.
        Event 2.2.4 Event 8
        """
        self.selenium.maximize_window()
        # Create a complete fire plan application before anything
        prescription = self.make('Prescription')
        set_cbas_attributes(prescription)

        # Go to the Submit for corporate approval page
        url = reverse('admin:prescription_prescription_corporate_approve',
                      args=(str(prescription.id),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the Submit button
        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()
        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)

        try:
            # If a success element is found then it submitted successfully.
            self.selenium.find_element_by_class_name('alert-success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

    def test_cancel_corporate_approval(self):
        """
        Test to click the Go Back button on the
        Submit for Corporate Approval page.
        Event 2.2.4 Event 8
        """
        self.selenium.maximize_window()
        # Create a complete fire plan application before anything
        prescription = self.make('Prescription')
        set_cbas_attributes(prescription)

        # Go to the Submit for corporate approval page
        url = reverse('admin:prescription_prescription_corporate_approve',
                      args=(str(prescription.id),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the Go Back button
        self.selenium.find_element_by_name("_cancel").click()
        self.wait_page_loaded()
        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)

        try:
            # If a success element is not found then it cancelled successfully.
            self.selenium.find_element_by_class_name('alert-success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertFalse(exists)

    def test_browse_apply_corporate_approval(self):
        """
        Test to click the Apply Corporate Approval link on the ePFP Overview
        page.
        Event 2.2.4 Event 9
        """
        self.selenium.maximize_window()
        # Create a complete fire plan application before anything
        prescription = self.make('Prescription')
        set_cbas_attributes(prescription)

        # Go to the Submit for corporate approval page
        url = reverse('admin:prescription_prescription_corporate_approve',
                      args=(str(prescription.id),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()
        # Click the Submit button
        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()

        # Go to ePFP Overview page
        url = reverse('admin:prescription_prescription_detail',
                      args=(str(prescription.id),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the Apply Corporate Approval link
        self.selenium.find_element_by_link_text(
            'Apply corporate approval').click()
        self.wait_page_loaded()
        self.assertEqual(self.selenium.find_element_by_tag_name('h4').text,
                         "Apply Corporate Approval")

    def test_submit_apply_corporate_approval(self):
        """
        Test to click on the Submit button on the
        Apply Corporate Approval page.
        Event 2.2.4 Event 10
        """
        # Create a complete fire plan application before anything
        prescription = self.make('Prescription')
        set_cbas_attributes(prescription)

        # Submit it for corporate approval
        url = reverse('admin:prescription_prescription_corporate_approve',
                      args=(str(prescription.id),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()
        # Click the Submit button
        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()

        # Go to the Apply Corporate Approval page
        url = reverse('admin:prescription_prescription_corporate_approve',
                      args=(str(prescription.id),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the Submit button
        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If a success element is found then it submitted successfully.
            self.selenium.find_element_by_class_name('alert-success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertTrue(exists)

    def test_cancel_apply_corporate_approval(self):
        """
        Test to click on the Go Back button on the
        Apply Corporate Approval page.
        Event 2.2.4 Event 10
        """
        self.selenium.maximize_window()
        # Create a complete fire plan application before anything
        prescription = self.make('Prescription')
        set_cbas_attributes(prescription)

        # Submit it for corporate approval
        url = reverse('admin:prescription_prescription_corporate_approve',
                      args=(str(prescription.id),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()
        # Click the Submit button
        self.selenium.find_element_by_name("_save").click()
        self.wait_page_loaded()

        # Go to the Apply Corporate Approval page
        url = reverse('admin:prescription_prescription_corporate_approve',
                      args=(str(prescription.id),))
        self.selenium.get(self.live_server_url + url)
        self.wait_page_loaded()

        # Click the Go Back button
        self.selenium.find_element_by_name("_cancel").click()
        self.wait_page_loaded()

        self.assertIn("Part A Summary",
                      self.selenium.find_elements_by_tag_name('h1')[1].text)
        try:
            # If a success element is not found then it cancelled successfully.
            self.selenium.find_element_by_class_name('alert-success')
            exists = True
        except NoSuchElementException:
            exists = False

        self.assertFalse(exists)

    def fill_in_form(self, name, burn_season, contentious, burn_purpose):
        """
        Fills in the form with test data. If any one of the inputs 'name',
        'burn_season', 'contentious' or 'burn_purpose' is False, then its
        element/s on the form will not be filled in.
        """
        selenium = self.selenium
        if name:
            selenium.find_element_by_id("id_name").send_keys("Test Burn Plan")

        if burn_season:
            selenium.find_element_by_css_selector(
                "#id_planned_season > option[value=\"4\"]").click()
            selenium.find_element_by_id("id_planned_year").clear()
            selenium.find_element_by_id("id_planned_year").send_keys("2013")

        selenium.find_element_by_id("id_last_season_unknown").click()
        selenium.find_element_by_id("id_last_year").clear()
        selenium.find_element_by_id("id_last_year").send_keys("2012")

        selenium.find_element_by_css_selector(
            "#id_region > option[value=\"7\"]").click()
        selenium.implicitly_wait(1)

        selenium.find_element_by_css_selector(
            "#id_district > option[value=\"13\"]").click()

        selenium.find_element_by_id("id_location_0").send_keys(
            "Test Locality")
        selenium.find_element_by_id("id_location_1").send_keys("3")
        selenium.find_element_by_css_selector(
            "#id_location_2 > option[value=\"NNE\"]").click()
        selenium.find_element_by_id("id_location_3").send_keys("Some Place")

        selenium.find_element_by_id("id_forest_blocks").clear()
        selenium.find_element_by_id("id_forest_blocks").send_keys(
            "Forest Blocks Optional Text")

        if contentious:
            selenium.find_element_by_css_selector(
                "#id_contentious > option[value=\"True\"]").click()
            selenium.find_element_by_id("id_contentious_rationale").clear()
            selenium.find_element_by_id("id_contentious_rationale").send_keys(
                "Reason for contentiousness.")
        selenium.find_element_by_id("id_aircraft_burn").click()
        selenium.find_element_by_css_selector(
            "#id_remote_sensing_priority > option[value=\"2\"]").click()

        if burn_purpose:
            selenium.find_element_by_id("id_purposes_0").click()
            selenium.find_element_by_id("id_biodiversity_text").clear()
            selenium.find_element_by_id("id_biodiversity_text").send_keys(
                "Reason for biodiversity management.")
            selenium.implicitly_wait(1)
            selenium.find_element_by_id("id_purposes_1").click()
            selenium.find_element_by_id("id_bushfire_risk_text").clear()
            selenium.find_element_by_id("id_bushfire_risk_text").send_keys(
                "Reason for bushfire risk.")
            selenium.implicitly_wait(1)
            selenium.find_element_by_id("id_purposes_2").click()
            selenium.implicitly_wait(1)
            selenium.find_element_by_id("id_purposes_3").click()
            selenium.implicitly_wait(1)
            selenium.find_element_by_id("id_purposes_4").click()
            selenium.implicitly_wait(1)
            selenium.find_element_by_id("id_purposes_5").click()
            selenium.find_element_by_id("id_vegetation_text").clear()
            selenium.find_element_by_id("id_vegetation_text").send_keys(
                "Reason for vegetation management.")
            selenium.implicitly_wait(1)
            selenium.find_element_by_id("id_purposes_6").click()

        selenium.find_element_by_css_selector(
            "#id_allocation > option[value=\"41\"]").click()
        selenium.find_element_by_id("id_treatment_percentage").send_keys("6")
        selenium.find_element_by_id("id_area").clear()
        selenium.find_element_by_id("id_area").send_keys("5.6")
        selenium.find_element_by_id("id_perimeter").clear()
        selenium.find_element_by_id("id_perimeter").send_keys("17.3")
