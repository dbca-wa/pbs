from datetime import datetime, timedelta, date
import requests
import os

from django import forms
from datetime import datetime, timedelta, date
from django.conf import settings
from django.forms import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Field, Div
import requests


from pbs.prescription.models import Prescription, Region, District
from pbs.review.models import PrescribedBurn, AircraftBurn
from pbs.forms import RequestMixin,SessionPersistenceMixin

def check_date(dt):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    if dt < today or dt > tomorrow:
        raise ValidationError("You must enter burn plans for today or tomorrow's date only.")


class BurnStateSummaryForm(forms.Form):
    region = forms.ModelChoiceField(required=False, queryset=Region.objects.all())
    district = forms.ModelChoiceField(required=False, queryset=District.objects.all())


class PrescribedBurnForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PrescribedBurnForm, self).__init__(*args, **kwargs)

#        prescriptions = self.fields['prescription'].queryset
#        self.fields['prescription'].queryset = prescriptions.filter(
#            burnstate__review_type__in=['FMSB'], planning_status=Prescription.PLANNING_APPROVED).filter(burnstate__review_type__in=['DRFMS']).distinct().order_by('burn_id')
        self.fields['region'].required = True
        self.fields['prescription'].required = True
        self.fields['location'].required = True
        self.fields['location'].widget.attrs.update({'placeholder': 'eg. 2 kms SouthEast of CBD'})

        self.fields['planned_area'].widget.attrs.update({'placeholder': 'Enter hectares to 1 dec place'})
        self.fields['planned_distance'].widget.attrs.update({'placeholder': 'Enter kilometres to 1 dec place'})
        self.fields['latitude'].widget.attrs.update({'placeholder': 'Enter Latitude to 5 dec places'})
        self.fields['longitude'].widget.attrs.update({'placeholder': 'Enter Longitude to 5 dec places'})

        now = datetime.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        time_now = now.time()
        date_str = tomorrow.strftime('%Y-%m-%d') if time_now.hour > settings.DAY_ROLLOVER_HOUR else today.strftime('%Y-%m-%d')
        self.fields['date'].widget.attrs.update({'value': date_str})
        self.fields['est_start'].required = True
        self.initial['status'] = 1

    def clean(self):

        if not 'prescription' in self.cleaned_data:
            raise ValidationError("Prescription is Required")

        if not (self.cleaned_data['planned_area'] or self.cleaned_data['planned_distance']):
            raise ValidationError("Must input at least one of Area or Distance")

        if not 'location' in self.cleaned_data:
            raise ValidationError("Must input location")

        if 'prescription' in self.cleaned_data and 'date' in self.cleaned_data and 'location' in self.cleaned_data:
            # check for integrity constraint - duplicate keys
            prescription = self.cleaned_data['prescription']
            dt = self.cleaned_data['date']
            location = self.cleaned_data['location']

            if hasattr(prescription, "current_approval") and dt > prescription.current_approval.valid_to:
                raise ValidationError("Date Error: Burn ID  {} is valid to {}".format(prescription.burn_id, prescription.current_approval.valid_to))

            if not self.current_user.is_superuser:
                check_date(dt)

            objects = PrescribedBurn.objects.filter(prescription=prescription, date=dt, form_name=PrescribedBurn.FORM_268A, location=location)
            if objects:
                raise ValidationError("Burn ID  {}  already exists on this date, with this location".format(objects[0].prescription.burn_id))
            else:
                return self.cleaned_data

    class Meta:
        model = PrescribedBurn
        fields = ('region', 'prescription', 'date', 'planned_area',
                  'planned_distance', 'tenures', 'location', 'est_start', 'conditions',
                  'latitude', 'longitude',
                 )


class PrescribedBurnEditForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(PrescribedBurnEditForm, self).__init__(*args, **kwargs)
        prescribed_burn = kwargs.get('instance')

        # hack to get the instance choices (region and prescription) to display read-only/disabled
        region = self.fields['region']
        region_idx = [i[0] for i in region.choices if prescribed_burn.get_region_display()==i[1]][0]
        region.choices = [region.choices[region_idx]]
        self.fields['region'].widget.attrs['disabled'] = 'disabled'

        prescription = self.fields['prescription']
        self.fields['prescription'].queryset = prescription.queryset.filter(burn_id=prescribed_burn.fire_idd)
        self.fields['prescription'].widget.attrs['readonly'] = True

        self.fields['location'].required = True
        self.fields['location'].widget.attrs.update({'placeholder': 'eg. 2 kms NorthEast of CBD'})

        self.fields['planned_area'].widget.attrs.update({'placeholder': 'Enter hectares to 1 dec place'})
        self.fields['planned_distance'].widget.attrs.update({'placeholder': 'Enter kilometres to 1 dec place'})
        self.fields['latitude'].widget.attrs.update({'placeholder': 'Enter Latitude to 5 dec places'})
        self.fields['longitude'].widget.attrs.update({'placeholder': 'Enter Longitude to 5 dec places'})

    def clean_prescription(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.prescription
        else:
            return self.cleaned_data['prescription']

    def clean_region(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.region
        else:
            return self.cleaned_data['region']

    def clean_location(self):

        if 'prescription' in self.cleaned_data and 'date' in self.cleaned_data:
            # check for integrity constraint - duplicate keys
            prescription = self.cleaned_data['prescription']
            dt = self.cleaned_data['date']
            location = self.cleaned_data['location']

            if hasattr(prescription, "current_approval") and dt > prescription.current_approval.valid_to:
                raise ValidationError("Date Error: Burn ID  {} is valid to {}".format(prescription.burn_id, prescription.current_approval.valid_to))

            objects = PrescribedBurn.objects.filter(prescription=prescription, date=dt, form_name=PrescribedBurn.FORM_268A, location=location)
            if objects and objects[0] != getattr(self, 'instance', None):
                raise ValidationError("Burn ID  {}  already exists with this date or location".format(objects[0].prescription.burn_id))
            else:
                return self.cleaned_data['location']

    def clean_date(self):
        if not self.current_user.is_superuser:
            dt = self.cleaned_data['date']
            check_date(dt)
        return self.cleaned_data['date']

    class Meta:
        model = PrescribedBurn
        fields = ('region', 'prescription', 'date', 'planned_area',
                  'planned_distance', 'tenures', 'location', 'est_start', 'conditions',
                  'latitude', 'longitude',
                 )


class PrescribedBurnActiveForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PrescribedBurnActiveForm, self).__init__(*args, **kwargs)

#        prescriptions = self.fields['prescription'].queryset
#        self.fields['prescription'].queryset = prescriptions.filter(
#            burnstate__review_type__in=['FMSB'], planning_status=Prescription.PLANNING_APPROVED).filter(burnstate__review_type__in=['DRFMS']).distinct().order_by('burn_id')

        now = datetime.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        time_now = now.time()
        date_str = tomorrow.strftime('%Y-%m-%d') if time_now.hour > settings.DAY_ROLLOVER_HOUR else today.strftime('%Y-%m-%d')
        self.fields['date'].widget.attrs.update({'value': date_str})
        #self.initial['status'] = 1

        self.fields['region'].required = True
        self.fields['prescription'].required = True
        self.fields['status'].required = True

        self.fields['location'].required = True
        self.fields['location'].widget.attrs.update({'placeholder': 'eg. 3 kms NorthEast of CBD'})

        self.fields['area'].widget.attrs.update({'placeholder': 'Enter hectares to 1 dec place'})
        self.fields['distance'].widget.attrs.update({'placeholder': 'Enter kilometres to 1 dec place'})
        self.fields['latitude'].widget.attrs.update({'placeholder': 'Enter Latitude to 5 dec places'})
        self.fields['longitude'].widget.attrs.update({'placeholder': 'Enter Longitude to 5 dec places'})

    def clean(self):
        if self.cleaned_data['area']==None and self.cleaned_data['distance']==None:
            raise ValidationError("Must input at least one of Area or Distance")

        if 'prescription' in self.cleaned_data and 'date' in self.cleaned_data:
            # check for integrity constraint - duplicate keys
            prescription = self.cleaned_data['prescription']
            dt = self.cleaned_data['date']
            location = self.cleaned_data['location']

            if not self.current_user.is_superuser:
                check_date(dt)

            objects = PrescribedBurn.objects.filter(prescription=prescription, date=dt, form_name=PrescribedBurn.FORM_268B, location=location)
            #objects = PrescribedBurn.objects.filter(prescription=prescription, date=dt, form_name=PrescribedBurn.FORM_268B)
            if objects:
                raise ValidationError("Burn ID  {}  already exists with this date or location".format(objects[0].prescription.burn_id))
            else:
                return self.cleaned_data

    class Meta:
        model = PrescribedBurn
        fields = ('region', 'prescription', 'date', 'status', 'ignition_status', 'area', 'distance', 'tenures', 'location',
                  'latitude', 'longitude',
            )


class PrescribedBurnEditActiveForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PrescribedBurnEditActiveForm, self).__init__(*args, **kwargs)
        prescribed_burn = kwargs.get('instance')

        # hack to get the instance choices (region and prescription) to display read-only/disabled
        region = self.fields['region']
        region_idx = [i[0] for i in region.choices if prescribed_burn.get_region_display()==i[1]][0]
        region.choices = [region.choices[region_idx]]
        self.fields['region'].widget.attrs['disabled'] = 'disabled'

        self.fields['location'].required = True
        self.fields['location'].widget.attrs.update({'placeholder': 'eg. 2 kms NorthEast of CBD'})

        prescription = self.fields['prescription']
        self.fields['prescription'].queryset = prescription.queryset.filter(burn_id=prescribed_burn.fire_idd)
        self.fields['prescription'].widget.attrs['readonly'] = True

        #status = self.fields['status']
        #status.choices = status.choices[1:]
        self.initial['status'] = 0

        now = datetime.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        time_now = now.time()
        date_str = tomorrow.strftime('%Y-%m-%d') if time_now.hour > settings.DAY_ROLLOVER_HOUR else today.strftime('%Y-%m-%d')
        self.fields['date'].widget.attrs.update({'value': date_str})

        self.fields['status'].required = True

        self.fields['area'].widget.attrs.update({'placeholder': 'Enter hectares to 1 dec place'})
        self.fields['distance'].widget.attrs.update({'placeholder': 'Enter kilometres to 1 dec place'})
        self.fields['latitude'].widget.attrs.update({'placeholder': 'Enter Latitude to 5 dec places'})
        self.fields['longitude'].widget.attrs.update({'placeholder': 'Enter Longitude to 5 dec places'})

    def clean_prescription(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.prescription
        else:
            return self.cleaned_data['prescription']

    def clean_location(self):

        if 'prescription' in self.cleaned_data and 'date' in self.cleaned_data:
            # check for integrity constraint - duplicate keys
            prescription = self.cleaned_data['prescription']
            dt = self.cleaned_data['date']
            location = self.cleaned_data['location']

            if hasattr(prescription, "current_approval") and dt > prescription.current_approval.valid_to and not 'status' in self.cleaned_data:
                raise ValidationError("Date Error: Burn ID  {} is valid to {}".format(prescription.burn_id, prescription.current_approval.valid_to))

            objects = PrescribedBurn.objects.filter(prescription=prescription, date=dt, form_name=PrescribedBurn.FORM_268B, location=location)
            if objects and objects[0] != getattr(self, 'instance', None):
                raise ValidationError("Burn ID  {}  already exists with this date or location".format(objects[0].prescription.burn_id))
            else:
                return self.cleaned_data['location']

    def clean_date(self):
        if not self.current_user.is_superuser:
            dt = self.cleaned_data['date']
            check_date(dt)
        return self.cleaned_data['date']

    class Meta:
        model = PrescribedBurn
        fields = ('region', 'prescription', 'date', 'status', 'ignition_status', 'area', 'distance', 'tenures', 'location',
                  'latitude', 'longitude',
            )


class ChoiceFieldNoValidation(forms.ChoiceField):
    """ Because the Choice field declared is empty, and populated by jscript, validation fails - so remove validation """
    def validate(self, value):
        pass

class FireForm(forms.ModelForm):
    fire_number = ChoiceFieldNoValidation(required=False)
    year = forms.ChoiceField(required=False)
    include_final_report = forms.BooleanField(label="Show Final Authorised Bushfire Report", required=False)
    #year = forms.ChoiceField(choices=((0, '--------'), (1, 2016), (2, 2017)) )

    def __init__(self, *args, **kwargs):
        super(FireForm, self).__init__(*args, **kwargs)

        self.fields['year'].choices = self.year_choices
        self.fields['region'].required = True
        self.fields['district'].required = True
        self.fields['fire_id'].widget = forms.HiddenInput()
        self.fields['fire_name'].widget = forms.HiddenInput()
        self.fields['tenures'].widget = forms.HiddenInput()
        self.fields['status'].required = True
        self.fields['area'].required = True
        self.fields['area'].label = 'Area Burnt (ha)'
        now = datetime.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        time_now = now.time()
        date_str = tomorrow.strftime('%Y-%m-%d') if time_now.hour > settings.DAY_ROLLOVER_HOUR else today.strftime('%Y-%m-%d')
        self.fields['date'].widget.attrs.update({'value': date_str})

        self.fields['area'].widget.attrs.update({'placeholder': 'Enter hectares to 1 dec place'})

    @property
    def year_choices(self):
        """ Returns tuple eg. ((0,'--------'), (1,2017)) """
        choices = [[0, '--------']]
        bfrs_url = settings.BFRS_URL if settings.BFRS_URL.endswith('/') else settings.BFRS_URL + os.sep
        years = ['--------'] + requests.get(url=bfrs_url + 'api/v1/bushfire/fields/year/?format=json', auth=requests.auth.HTTPBasicAuth(settings.USER_SSO, settings.PASS_SSO), verify=False).json()
        return tuple([(years.index(i), i) for i in years])

    def clean(self):
        fire_id = self.cleaned_data['fire_id']
        if not fire_id or not len(fire_id)==15:
            raise ValidationError("You must select a fire number")

        dt = self.cleaned_data['date']
        if not self.current_user.is_superuser:
            check_date(dt)

        pb = PrescribedBurn.objects.filter(fire_id=fire_id, date=dt)
        if pb:
            raise ValidationError("{} already exists for date {}".format(fire_id, dt))

        return self.cleaned_data

    class Meta:
        model = PrescribedBurn
        #fields = ('region', 'district', 'year', 'fire_number', 'fire_id','date', 'status', 'area', 'fire_tenures', 'fire_name',)
        fields = ('region', 'district', 'year','include_final_report', 'fire_number', 'fire_id','date', 'status', 'area', 'fire_name', 'tenures',)


class FireEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FireEditForm, self).__init__(*args, **kwargs)
        prescribed_burn = kwargs.get('instance')
        #self.initial['fire_id'] = self.initial['fire_id'][-3:]

        #self.fields['fire_name'].required = True
        self.fields['status'].required = True
        self.fields['area'].required = True
        self.fields['area'].label = 'Area Burnt (ha)'
        self.fields['tenures'].required = False
        self.fields['tenures'].label = 'Tenure of Ignition Point'

        # hack to get the instance choices (region and district) to display read-only/disabled
        region = self.fields['region']
        region_idx = [i[0] for i in region.choices if prescribed_burn.get_region_display()==i[1]][0]
        region.choices = [region.choices[region_idx]]
        self.fields['region'].widget.attrs['disabled'] = 'disabled'

        self.initial['district'] = prescribed_burn.district.id
        self.fields['district'].widget.attrs['disabled'] = 'disabled'

        self.fields['fire_id'].widget.attrs['readonly'] = True
        self.fields['fire_name'].widget.attrs['readonly'] = True
        self.fields['tenures'].widget.attrs['readonly'] = True

        status = self.fields['status']
        status.choices = status.choices[1:]

        self.fields['area'].widget.attrs.update({'placeholder': 'Enter hectares to 1 dec place'})

    def clean_region(self):
        """
        need this when widget is disabled
        """
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.region
        else:
            return self.cleaned_data['region']

    def clean_district(self):
        """
        need this when widget is disabled
        """
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.district
        else:
            return self.cleaned_data['district']

    def clean_fire_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.fire_id
        else:
            return self.cleaned_data['fire_id']

    def clean_date(self):
        if not self.current_user.is_superuser:
            dt = self.cleaned_data['date']
            check_date(dt)
        return self.cleaned_data['date']

    class Meta:
        model = PrescribedBurn
        #fields = ('region', 'district', 'fire_id', 'fire_name', 'date', 'status', 'area', 'fire_tenures',)
        fields = ('region', 'district', 'fire_id', 'fire_name', 'tenures', 'date', 'status', 'area',)


class PrescribedBurnFilterForm(RequestMixin,SessionPersistenceMixin,forms.ModelForm):
    approval_status = forms.MultipleChoiceField(required=False, choices=PrescribedBurn.APPROVAL_CHOICES)

    def default_initial(self):
        return {
            'region':self.request.user.profile.region.id if self.request and self.request.user.profile.region else None,
            'district':self.request.user.profile.district.id if self.request and self.request.user.profile.district else None,
            'approval_status': [c[0] for c in PrescribedBurn.APPROVAL_CHOICES]
        }

    class Meta:
        fields = ('region', 'district', 'approval_status')
        model = PrescribedBurn

class FireSummaryFilterForm(RequestMixin,SessionPersistenceMixin,forms.ModelForm):

    def default_initial(self):
        return {
            'region':self.request.user.profile.region.id if self.request and self.request.user.profile.region else None,
            'district':self.request.user.profile.district.id if self.request and self.request.user.profile.district else None,
        }

    class Meta:
        fields = ('region', 'district')
        model = PrescribedBurn



class FireLoadFilterForm(RequestMixin,SessionPersistenceMixin,forms.ModelForm):
    fire_type = forms.TypedChoiceField(required=False, choices=[(0, '------'), (1, 'Burns'), (2, 'Bushfires')],coerce=lambda val:int(val))
    approval_status = forms.MultipleChoiceField(required=False, choices=PrescribedBurn.APPROVAL_CHOICES)

    def default_initial(self):
        return {
            'region':self.request.user.profile.region.id if self.request and self.request.user.profile.region else None,
            'district':self.request.user.profile.district.id if self.request and self.request.user.profile.district else None,
            'approval_status': [c[0] for c in PrescribedBurn.APPROVAL_CHOICES],
            'fire_type':0
        }

    class Meta:
        fields = ('region', 'district', 'fire_type', 'approval_status')
        model = PrescribedBurn


class CsvForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(CsvForm, self).__init__(*args, **kwargs)
        self.fields['fromDate'].label = 'ha)'

        now = datetime.now()
        toDate = now.date().strftime('%Y-%m-%d')
        fromDate = (now - timedelta(days=14)).strftime('%Y-%m-%d')
        self.fields['fromDate'].widget.attrs.update({'value': fromDate})
        self.fields['toDate'].widget.attrs.update({'value': toDate})

    fromDate = forms.DateField(required=False)
    toDate = forms.DateField(required=True)


class AircraftBurnFilterForm(forms.ModelForm):
    region = forms.ModelChoiceField(required=False, queryset=Region.objects.all())
    approval_status = forms.ChoiceField(required=False, choices=AircraftBurn.APPROVAL_CHOICES)

    class Meta:
        fields = ('region', 'approval_status')
        model = AircraftBurn


class AircraftBurnForm(forms.ModelForm):
    region = forms.ModelChoiceField(required=True, queryset=Region.objects.all())

    def __init__(self, *args, **kwargs):
        super(AircraftBurnForm, self).__init__(*args, **kwargs)

        self.fields['region'].required = True
        self.fields['prescription'].required = True
        self.fields['date'].required = True
        self.fields['area'].required = True
        self.fields['est_start'].required = True
        self.fields['bombing_duration'].required = True
        now = datetime.now()
        today = now.date()
        date_str = today.strftime('%Y-%m-%d')
        self.fields['date'].widget.attrs.update({'value': date_str})

        self.fields['area'].widget.attrs.update({'placeholder': 'Enter hectares to 1 dec place'})

    class Meta:
        #exlude = ('flight_seq', 'aircraft_rego', 'arrival_time', 'program',)
        fields = ('region', 'prescription', 'date', 'area', 'est_start', 'bombing_duration', 'min_smc', 'max_fdi', 'sdi_per_day', 'aircrew')
        model = AircraftBurn


class AircraftBurnEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AircraftBurnEditForm, self).__init__(*args, **kwargs)

    class Meta:
        fields = ('prescription', 'date', 'area', 'est_start', 'bombing_duration', 'min_smc', 'max_fdi', 'sdi_per_day',
                  'flight_seq', 'aircraft_rego', 'arrival_time', 'program', 'aircrew'
            )
        model = AircraftBurn


