from django import forms
from pbs.document.models import DocumentTag, Document


class DocumentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        if (kwargs.get('initial') is not None and
                kwargs['initial'].get('tag') is not None and
                DocumentTag.objects.filter(id=int(kwargs['initial']['tag']))):
            # hide the tag choice list if the tag is preselected
            self.fields['tag'].widget = forms.HiddenInput()

    class Meta:
        model = Document
        fields = '__all__'
