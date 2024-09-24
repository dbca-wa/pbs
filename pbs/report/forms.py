from django import forms
from django.core.exceptions import ValidationError
from select2.fields import ModelMultipleChoiceField

from pbs.report.models import (SummaryCompletionState, BurnImplementationState,
                               BurnClosureState, AreaAchievement, IgnitionType,
                               PostBurnChecklist)
from django.contrib.admin.widgets import FilteredSelectMultiple


class SummaryCompletionStateForm(forms.ModelForm):
    """
    Validates the completion status of the ePFP.
    """

    class Meta:
        model = SummaryCompletionState
        exclude = ('prescription',)


class PatchedModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PatchedModelForm, self).__init__(*args, **kwargs)
        # there is a bug in django's fields.NullBooleanField
        # if it gets custom choices, it always adds an extra
        # blank_choice '-----', so let's remove it (there is None choice
        # already)
        for field_key in self.fields:
            field = self.fields[field_key]
            if hasattr(field, 'choices'):
                if (len(field.choices) > 1 and field.choices[0][0] == '' and
                        field.choices[1][0] is None):
                    # we definitely don't need None and '' as two separate
                    # choices
                    field.choices = field.choices[1:]


class BurnImplementationStateForm(PatchedModelForm):
    """
    Validates the completion status of Part B of an ePFP.
    """
    class Meta:
        model = BurnImplementationState
        exclude = ('prescription',)


class BurnClosureStateForm(PatchedModelForm):
    class Meta:
        model = BurnClosureState
        exclude = ('prescription',)


class AreaAchievementForm(forms.ModelForm):

    ignition_types = ModelMultipleChoiceField(queryset=IgnitionType.objects.all(), model=IgnitionType, name="ignition_types")
    # ignition_types = forms.ModelMultipleChoiceField(queryset=IgnitionType.objects.all(), widget=FilteredSelectMultiple("Ignition Types", is_stacked=False))
    #ignition_types = forms.ModelMultipleChoiceField(queryset=IgnitionType.objects.all())
    
    def __init__(self, *args, **kwargs):
        super(AreaAchievementForm, self).__init__(*args, **kwargs)
        # if self.fields.has_key('ignition'):
        if 'ignition' in self.fields:
            self.fields['ignition'].widget.attrs.update({'class': 'vDateField input-small'})
            self.fields['date_escaped'].widget.attrs.update({'class': 'vDateField input-small'})
        #self.fields['ignition_types'] = ModelMultipleChoiceField(queryset=IgnitionType.objects.all(), model=IgnitionType, name="ignition_types")
        # if(self.instance and self.instance.id):
        #     self.fields['ignition_types'].initial= self.instance.ignition_types.all()
        self.fields['ignition_types'].widget.attrs.update({'style': 'width: 400px; height: 150 px;'})

    def clean(self):
        """
        Test that if there is an ignition type, there also has to be treated
        area, burnt area, edging length and edging depth entered.
        """
        cleaned_data = super(AreaAchievementForm, self).clean()
        ignition_types = cleaned_data.get("ignition_types")

        if ignition_types:
            if not all([cleaned_data.get('area_estimate')]):
                raise ValidationError("You must fill in values for "
                                      "burnt area if you select an "
                                      "ignition type.")

        return cleaned_data
    

    class Meta:
        model = AreaAchievement
        fields ='__all__'


class PostBurnChecklistForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(PostBurnChecklistForm, self).__init__(*args, **kwargs)
        if 'completed_on' in self.fields:
          self.fields['completed_on'].widget.attrs.update({'class': 'vDateField input-small'})

    class Meta:
        model = PostBurnChecklist
        fields='__all__'
