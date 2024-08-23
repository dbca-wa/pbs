from django.test import TestCase, SimpleTestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.contrib.admin.tests import AdminSeleniumWebDriverTestCase
from django.db.models.base import ModelBase

from selenium.common.exceptions import NoSuchElementException

from model_mommy import mommy
from model_mommy.recipe import Recipe
from model_mommy.exceptions import InvalidQuantityException

from pbs.prescription.models import Region, District, Prescription
from pbs.risk.models import Complexity


# model_mommy customization
# custom recipes due to custom model save() methods
prescription_recipe = Recipe(Prescription, district=1, region=1, name='test',
                             planned_year=2013, planned_season=1)


complexity_recipe = Recipe(Complexity, factor="bla", sub_factor="bla",
                           rating=1, rationale="bla")


# model <-> recipes mapping
model_recipes = {'prescription': prescription_recipe,
                 'complexity': complexity_recipe}


def _get_model_name(model):
    """Extract lowercase model name from either a model class or import path.
    """
    if isinstance(model, ModelBase):
        model_name = model().__class__.__name__
    else:
        model_name = model
    return model_name.lower().split('.')[-1]  # it could be pbs.models.*


# overwrite some stuff from model_mommy
class PatchedMommy(mommy.Mommy):
    def instance(self, attrs, _commit):
        # the instance might have already been created by a post_save hook, if
        # we generate a new instance, a unique key error might be raised.
        instance = None
        unique_checks, date_checks = self.model()._get_unique_checks()
        for model, unique_attrs in unique_checks:
            if model == self.model:
                attrs_ = dict((attr, attrs[attr])
                              for attr in unique_attrs if attr in attrs)
                if len(attrs_.keys()):
                    try:
                        instance = self.model.objects.get(**attrs_)
                    except (self.model.DoesNotExist,
                            self.model.MultipleObjectsReturned):
                        pass
        instance = instance or self.model(**attrs)
        if _commit:
            instance.save()
            self._handle_m2m(instance)
        return instance


# custom make and prepare methods to read from model_recipes mapping table
def make(model, _quantity=None, make_m2m=False, **attrs):
    """We have a special recipe for Prescription and Complexity models."""
    model_name = _get_model_name(model)
    if model_name in model_recipes.keys():
        if _quantity and (not isinstance(_quantity, int) or _quantity < 1):
            raise InvalidQuantityException

        if _quantity:
            return [model_recipes[model_name].make(**attrs)
                    for i in range(_quantity)]
        else:
            return model_recipes[model_name].make(**attrs)
    else:
        patchedMommy = PatchedMommy(model, make_m2m=make_m2m)
        return patchedMommy.make(**attrs)
make.required = mommy.foreign_key_required


def prepare(model, _quantity=None, **attrs):
    """We have a special recipe for Prescription and Complexity models."""
    model_name = _get_model_name(model)
    if model_name in model_recipes.keys():
        if _quantity and (not isinstance(_quantity, int) or _quantity < 1):
            raise InvalidQuantityException

        if _quantity:
            return [model_recipes[model_name].prepare(**attrs)
                    for i in range(_quantity)]
        else:
            return model_recipes[model_name].prepare(**attrs)
    else:
        return mommy.prepare(model, _quantity, **attrs)
prepare.required = mommy.foreign_key_required


def __m2m_generator(model, **attrs):
    return make(model, _quantity=mommy.MAX_MANY_QUANTITY, **attrs)
__m2m_generator.required = mommy.foreign_key_required


def gen_file_field():
    # TODO: this could try to do model_mommy's get_file_field() and if
    # permission denied or something else, it could just try to return a random
    # file in the FileSystemStorage, not sure how to pass the FileSystemStorage
    # here though
    return 'UNKNOWN'


MOMMY_CUSTOM_FIELDS_GEN = {
    'smart_selects.db_fields.ChainedForeignKey': make,
    # generators.gen_file_field,
    'pbs.document.models.ContentTypeRestrictedFileField': gen_file_field,
    'django.db.models.ForeignKey': make,
    'django.db.models.OneToOneField': make,
    'django.db.models.ManyToManyField': __m2m_generator,
    'django.db.models.FileField': gen_file_field,
}


class Model_mommyMixin(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        cls = override_settings(
            MOMMY_CUSTOM_FIELDS_GEN=MOMMY_CUSTOM_FIELDS_GEN)(cls)
        super(Model_mommyMixin, cls).setUpClass()

    def make(self, model_class, **kwargs):
        return make(model_class, **kwargs)

    def prepare(self, model_class, **kwargs):
        return prepare(model_class, **kwargs)


# the actual abstract TestCase classes
class BasePbsTestCase(TestCase, Model_mommyMixin):
    def setUp(self):
        super(BasePbsTestCase, self).setUp()
        self.factory = RequestFactory()

    def _mocked_authenticated_request(self, url, user):
        request = self.factory.get(url)
        request.user = user
        return request


class SeleniumTestCase(AdminSeleniumWebDriverTestCase,
                       Model_mommyMixin):
    def login(self, username, password):
        """
        Log the user in if they are not already.
        """
        try:
            self.selenium.find_element_by_partial_link_text("Welcome,")
        except NoSuchElementException:
            self.admin_login(username, password,
                             login_url=reverse('admin:index'))
