from django import forms
from pbs.prescription.widgets import LocationWidget


class LocationMultiField(forms.MultiValueField):
    widget = LocationWidget()

    def __init__(self, *args, **kwargs):

        fields = (
            forms.CharField(max_length=150),
            forms.CharField(max_length=3),
            forms.CharField(max_length=3),
            forms.CharField(max_length=150),
        )
        super(LocationMultiField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if ((data_list and not data_list[1] and not data_list[2] and not
             data_list[3])):
            return 'Within the locality of {0}'.format(data_list[0])
        elif data_list:
            return '|'.join(data_list)
        else:
            return ''
