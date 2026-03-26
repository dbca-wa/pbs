from django import forms
from pbs.implementation.models import BurningPrescription, EdgingPlan, LightingSequence
from pbs.forms import HelperModelForm, WideTextarea


class BurningPrescriptionForm(forms.ModelForm):

    class Meta:
        model = BurningPrescription
        fields = ('prescription', 'fuel_type', 'scorch', 'grassland_curing_min', 'grassland_curing_max')


class EdgingPlanForm(HelperModelForm):

    def __init__(self, *args, **kwargs):
        super(EdgingPlanForm, self).__init__(*args, **kwargs)
        self.fields['location'].widget = WideTextarea()
        self.fields['strategies'].widget = WideTextarea()

    class Meta:
        model = EdgingPlan
        fields = '__all__'


class LightingSequenceForm(HelperModelForm):

    def __init__(self, *args, **kwargs):
        super(LightingSequenceForm, self).__init__(*args, **kwargs)
        self.fields['cellname'].widget.attrs.update({'class': 'span5'})
        self.fields['strategies'].widget = WideTextarea()
        self.fields['fuel_description'].widget = WideTextarea()
        self.fields['resources'].widget = WideTextarea()
        self.fields['wind_dir'].widget = WideTextarea()
        self.fields['ffdi_min'].required = False
        self.fields['ffdi_max'].required = False
        self.fields['grassland_curing_min'].required = False
        self.fields['grassland_curing_max'].required = False
        self.fields['gfdi_min'].required = False
        self.fields['gfdi_max'].required = False
        self.fields['ros_min'].required = False
        self.fields['ros_max'].required = False
        self.fields['wind_min'].required = False
        self.fields['wind_max'].required = False

    class Meta:
        model = LightingSequence
        fields = '__all__'