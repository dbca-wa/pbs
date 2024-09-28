
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.templatetags.static import static

from pbs.forms import PbsErrorList


class RegistrationForm(forms.Form):
    """
    Form for registering a new user account.

    """
    required_css_class = 'required'

    username = forms.RegexField(regex=r'^[\w.@+-]+$', max_length=30,
        label=_("Username"), error_messages={'invalid': _("This value may contain only letters, numbers and @/./+/-/_ characters.")})
    email = forms.EmailField(label=_("E-mail"))
    password1 = forms.CharField(widget=forms.PasswordInput,
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput,
                                label=_("Password (again)"))
    first_name = forms.CharField(max_length=20, required=True)
    last_name = forms.CharField(max_length=20, required=True)
    tos = forms.BooleanField(widget=forms.CheckboxInput,
        label=_(u'I have read and agree to the Terms of Service'),
        error_messages={'required': _("You must agree to the terms to register")})

    def __init__(self, *args, **kwargs):
        kwargs['error_class'] = PbsErrorList
        super(RegistrationForm, self).__init__(*args, **kwargs)
        terms_of_service_url = static('pbs/docs/terms_of_service.doc')
        self.fields['tos'].label = mark_safe(
            'I have read and agree to the ' +
            '<a href="{0}" title="Terms of Service">Terms of Service</a>'
            .format(terms_of_service_url)
        )

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email__iexact=email):
            raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))

        if not email.lower().endswith(settings.FPC_EMAIL_EXT):
            raise forms.ValidationError(
                _("This is not a valid FPC email address."))
        return email

    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.

        """
        existing = User.objects.filter(username__iexact=self.cleaned_data['username'])
        if existing.exists():
            raise forms.ValidationError(_("A user with that username already exists."))
        else:
            return self.cleaned_data['username']

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.

        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))
        return self.cleaned_data
