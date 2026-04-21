from django import forms

from pbs.risk.models import Risk, Treatment, TreatmentLocation
from pbs.utils.widgets import CheckboxSelectMultiple
from pbs.forms import Bootstrap5FormMixin


class RiskForm(Bootstrap5FormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RiskForm, self).__init__(*args, **kwargs)
        if (kwargs.get('initial') is not None and
                kwargs['initial'].get('prescription') is not None):
            self.fields['prescription'].widget = forms.HiddenInput()
            self.fields['prescription'].help_text = ''

    class Meta:
        model = Risk
        exclude = ('custom', 'risk', )
        fields = ('prescription', 'category', 'name', )


class TreatmentForm(Bootstrap5FormMixin, forms.ModelForm):
    #locations = forms.ModelMultipleChoiceField(required=True,
    #    queryset=TreatmentLocation.objects.all(),
    #    widget=CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        super(TreatmentForm, self).__init__(*args, **kwargs)
        #self.fields['locations'].help_text = ''

        #if self.fields.has_key('location'):
        #    self.fields['location'].widget = forms.HiddenInput()

    class Meta:
        model = Treatment
        exclude = ('register', 'complete')


class TreatmentCompleteForm(Bootstrap5FormMixin, forms.ModelForm):
    class Meta:
        model = Treatment
        exclude = ('register', 'description', 'location')
