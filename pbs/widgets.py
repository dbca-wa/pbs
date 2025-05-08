from django import forms

class NullBooleanSelect(forms.widgets.NullBooleanSelect):
    """
    A Select Widget intended to be used with NullBooleanField.
    """
    def __init__(self, attrs=None,true='Yes',false='No',none='--------'):
        if none is None:
            choices = (('true', true),
                       ('false', false))
        else:
            choices = (('--', none),
                       ('true', true),
                       ('false', false))
        forms.widgets.Select.__init__(self,attrs, choices)

