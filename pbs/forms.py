from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.conf import settings
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.utils.html import format_html_join, format_html
# from django.utils.encoding import force_text
from django.utils.encoding import force_str
# from django.utils.translation import ugettext_lazy as _
from django.utils.translation import gettext_lazy as _


from datetime import date

from .models import Profile

from pbs.prescription.models import District, Region

class RequestMixin(object):
    def __init__(self,request=None,*args,**kwargs):
        self.request = request
        super(RequestMixin,self).__init__(*args,**kwargs)

class SessionPersistenceMixin(object):
    """
    Use the following logic to initialize instance
    1. If data is not null and also if data contains any key in the checking keys, then the form is bounded and use the data to initialize the form; otherwise continue step 2
    2. Try to load the form status from session, if exist, use that to initialize the form; otherwise continue step 3
    3. If initial is not null, use initial to initialize the form; otherwise continue step 4
    4. If default_initial return a non null object, use that to initialize the form, otherwise continue step 5
    5. Initialize a empty form


    if form is partially persistent, the missing field's value will be read from initial or default_initial

    """
    session_key_prefix = ""
    def __init__(self,prefix="",checking_keys=None,persistent_fields=None,persistent=True,*args,**kwargs):
        if not self.request:
            persistent = False

        if not persistent:
            #persistent disabled
            if not kwargs.get("initial"):
                initial = self.default_initial()
                if initial:
                    #has default form initial status
                    kwargs["initial"] = initial

            super(SessionPersistenceMixin,self).__init__(*args,**kwargs)
            return

        self.session_key = self.get_session_key(prefix)
        self.persistent_fields = persistent_fields or self._meta.fields
        if "data" in kwargs:
            if kwargs["data"]:
                if not checking_keys:
                    checking_keys = self._meta.fields
                if any([key in kwargs["data"] for key in checking_keys]):
                    #bounded
                    super(SessionPersistenceMixin,self).__init__(*args,**kwargs)
                    default_initial = self.default_initial()
                    changed = False
                    for field_name in self.persistent_fields:
                        value = self[field_name].value()
                        if not value and not default_initial.get(field_name):
                            #both none
                            continue
                        elif value == default_initial.get(field_name):
                            #same
                            continue
                        elif str(self[field_name].value()) == str(default_initial.get(field_name)):
                            #same
                            continue
                        else:
                            #field value is different from the value in default initial
                            changed = True
                            break
                    if changed:
                        #form status is different from default initial,save the form status into session for later reference
                        self.save_to_session()
                    else:
                        #form status is same as default initial,save the form status into session for later reference
                        self.delete_from_session()

                    return
            #not bounded
            kwargs.pop("data")

        #persistent is enabled
        initial = self.load_from_session()
        if initial:
            #form status found in session
            if persistent_fields:
                #partial persistent, add missing field value from default_initial
                for key,value in (kwargs.get("initial") or self.default_initial() or {}).iteritems():
                    if key not in initial:
                        initial[key] = value

            kwargs["initial"] = initial
            super(SessionPersistenceMixin,self).__init__(*args,**kwargs)
            return

        if kwargs.get("initial"):
            #has initial form status passed in
            super(SessionPersistenceMixin,self).__init__(*args,**kwargs)
            return

        initial = self.default_initial()
        if initial:
            #has default form initial status
            kwargs["initial"] = initial
            super(SessionPersistenceMixin,self).__init__(*args,**kwargs)
            return

        super(SessionPersistenceMixin,self).__init__(*args,**kwargs)


    def default_initial(self):
        return None

    def to_dict(self):
        """
        Convert form's status into a dictionary object for persistence.
        """
        obj = {}
        for field_name in self.persistent_fields:
            obj[field_name] = self[field_name].value()

        return obj

    @classmethod
    def get_session_key(cls,prefix=""):
        """
        Return the session key to save the form status into session
        """
        prefix = prefix or cls.session_key_prefix
        return "{}:{}.{}".format(prefix,cls.__module__,cls.__name__) if prefix else "{}.{}".format(cls.__module__,cls.__name__)


    def save_to_session(self):
        """
        Save the form data into session as dict object for later reference
        """
        self.request.session[self.session_key] = self.to_dict()

    def delete_from_session(self):
        """
        delete the form data from session if exist
        """
        if self.session_key in self.request.session:
            del self.request.session[self.session_key]

    def load_from_session(self):
        """
        load and return the intial form data from session; if not found, return None
        """
        return self.request.session.get(self.session_key)

class PbsErrorList(forms.utils.ErrorList):
    # custom error classes
    def as_ul(self):
        if not self:
            return ''
        return format_html(
            '<ul class="errorlist alert alert-block alert-error fade in">'
            '{0}</ul>', format_html_join('', '<li>{0}</li>',
                                         ((force_str(e),) for e in self)
                                         )
        )


class PbsModelForm(forms.models.ModelForm):
    # custom error_class for modelforms created by .get_changelist_formset
    def __init__(self, *args, **kwargs):
        kwargs['error_class'] = PbsErrorList
        super(PbsModelForm, self).__init__(*args, **kwargs)

    def has_changed(self):
        """
        The shadow/initial date objects use hidden fields that have no idea
        about dates so their values (unlike the display values) are always in
        the isoformat 'YYYY-MM-DD' as returned by datetime.date.__str__()
        http://docs.python.org/2/library/datetime.html#datetime.date.__str__
        let's help it a little bit and try to convert those shadow/initial
        date strings into the (possibly) custom formatted strings so that our
        untouched forms don't get treated as if they were touched.
        see PBS-913.
        It appears this has been fixed in django 1.6 where the
        widget._has_changed has been deprecated in favour of
        field._has_changed.
        https://code.djangoproject.com/ticket/16612
        which means this could probably be refactored/simplified to use
        field.to_python() instead of datetime.strptime() but I guess we'll
        wait for django 1.6 :)
        """
        self._changed_data=self.changed_data
        if self.changed_data:
            self._changed_data = self.changed_data
            if bool(self._changed_data):
                for index, name in enumerate(self._changed_data):
                    field = self.fields[name]
                    if (field.show_hidden_initial and
                            field.__class__.__name__ == 'DateField'):
                        prefixed_name = self.add_prefix(name)
                        initial_prefixed_name = self.add_initial_prefix(name)
                        data_value = field.widget.value_from_datadict(
                            self.data, self.files, prefixed_name)
                        hidden_widget = field.hidden_widget()
                        initial_value = hidden_widget.value_from_datadict(
                            self.data, self.files, initial_prefixed_name)
                        try:
                            date = datetime.strptime(initial_value,
                                                     "%Y-%m-%d").date()
                        except ValueError:
                            pass
                        else:
                            initial_value = field.widget._format_value(date)

                        if not field._has_changed(initial_value,
                                                         data_value):
                            self._changed_data.pop(index)
        return bool(self._changed_data)


class WideTextarea(forms.Textarea):
    """
    Add span8 class to the stock Textarea widget, to make it full-width.
    """
    def __init__(self, *args, **kwargs):
        self.attrs = {'class': 'span8'}


class BaseFormHelper(FormHelper):
    """
    Base helper class for rendering forms via crispy_forms.
    To remove the default "Save" button from the helper, instantiate it with
    inputs=[]
    E.g. helper = BaseFormHelper(inputs=[])
    """
    def __init__(self, *args, **kwargs):
        super(BaseFormHelper, self).__init__(*args, **kwargs)
        self.form_class = 'form-horizontal'
        self.help_text_inline = True
        self.form_method = 'POST'
        save_btn = Submit('submit', 'Save')
        save_btn.field_classes = 'btn btn-primary'
        self.add_input(save_btn)


class HelperModelForm(forms.ModelForm):
    """
    Stock ModelForm with a property named ``helper`` (used by crispy_forms to
    render in templates).
    """
    @property
    def helper(self):
        helper = BaseFormHelper()
        return helper


class PbsAdminAuthenticationForm(AdminAuthenticationForm):
    """
    A custom authentication form used in the offsets internal application.
    Subclasses the form in django.contrib.admin.forms because that form will
    test is_staff==True for all logins in its clean() method.
    We need to be able to have internal users login to the application without
    manually setting is_staff to True.
    """
    ERROR_MESSAGE = _("Please enter the correct %(username)s and password "
                      "for a staff account. Note that both fields may be "
                      "case-sensitive.")

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        message = self.ERROR_MESSAGE

        if username and password:
            self.user_cache = authenticate(username=username,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError(message % {
                    'username': self.username_field.verbose_name
                })
        self.check_for_test_cookie()
        return self.cleaned_data


class UserForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['is_active'].label = ("Approved User (i.e. enable login "
                                          "for this user?)")
        instance = getattr(self, 'instance', None)
        if instance and instance.pk and not instance.profile.is_fpc_user():
            #self.fields['username'].widget.attrs['readonly'] = True
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['first_name'].widget.attrs['readonly'] = True
            self.fields['last_name'].widget.attrs['readonly'] = True

    class Meta:
        model = User
        fields = ('is_active', 'groups')


class ProfileForm(HelperModelForm):
    class Meta:
        model = Profile
        exclude = ('user',)

    def clean(self):
        """District must be child of Region.
        """
        cleaned_data = super(ProfileForm, self).clean()
        district = cleaned_data.get('district', None)
        if district and district.region != cleaned_data.get('region'):
            self._errors['district'] = self.error_class(
                ['Please choose a valid District for this Region (or leave it blank).'])
        # District may not be chosen if archive_date is set.
        if district and district.archive_date:
            self._errors['district'] = self.error_class(
                ['Please choose a current District for this Region (or leave it blank).'])
        return cleaned_data


class PbsPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        kwargs['error_class'] = PbsErrorList
        super(PbsPasswordResetForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        # ensure this is an FPC email
        email = self.cleaned_data['email']
        if not email.lower().endswith(settings.FPC_EMAIL_EXT):
            raise forms.ValidationError(
                _("This is not a valid FPC email address. " +
                  "Only FPC users can reset their password " +
                  "via this interface"))
        return super(PbsPasswordResetForm, self).clean_email()


class EndorseAuthoriseSummaryForm(forms.Form):
    region = forms.ModelChoiceField(required=False,
        queryset=Region.objects.all())
    district = forms.ModelChoiceField(required=False, queryset=District.objects.all())

    fromDate = forms.DateField(required=False)
    toDate = forms.DateField(required=False)

    def clean_fromDate(self):
        d = self.cleaned_data.get('fromDate')
        if d is None:
            d = date(1970, 1, 1)
        return d

    def clean_toDate(self):
        d = self.cleaned_data.get('toDate')
        if d is None:
            d = date.today()
        return d


class BurnStateSummaryForm(forms.Form):
    region = forms.ModelChoiceField(required=False,
        queryset=Region.objects.all())
    district = forms.ModelChoiceField(required=False, queryset=District.objects.all())


