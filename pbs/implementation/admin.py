from django.contrib import admin
from django.template.defaultfilters import date, time
from django.utils.safestring import mark_safe

from pbs.admin import BaseAdmin
from pbs.implementation.models import Prescription
from pbs.implementation.forms import EdgingPlanForm, LightingSequenceForm
from pbs.implementation.utils import field_range
from pbs.prescription.admin import (PrescriptionMixin,
                                    SavePrescriptionMixin)

from chosen.widgets import ChosenSelectMultiple
from django.conf import settings
import json


class OperationalOverviewAdmin(PrescriptionMixin, SavePrescriptionMixin,
                               BaseAdmin):
    list_display = ("overview",)
    list_editable = ("overview",)
    list_empty_form = True
    list_display_links = (None,)
    actions = None
    lock_after = "endorsement"


class BurningPrescriptionAdmin(PrescriptionMixin, SavePrescriptionMixin,
                               BaseAdmin):
    list_display = ("fuel_type", "scorch", "area", "ros", "ffdi", "grassland_curing",
                    "gfdi", "temp", "rh", "sdi", "smc", "pmc", "wind", "wind_dir")
    actions = None
    can_delete = True
    lock_after = 'endorsement'

    fieldsets = (
        (None, {
            "fields": ('fuel_type', 'scorch', ('min_area', 'max_area'),
                ('ros_min', 'ros_max'), ('ffdi_min', 'ffdi_max'),
                ('grassland_curing_min', 'grassland_curing_max'),
                ('gfdi_min', 'gfdi_max'), ('temp_min', 'temp_max'),
                ('rh_min', 'rh_max'), 'sdi', ('smc_min', 'smc_max'),
                ('pmc_min', 'pmc_max'), ('wind_min', 'wind_max'),
                'wind_dir')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if self.prescription.is_draft or request.user.has_perm('prescription.can_admin'):
            return (None,)
        else:
            return ('fuel_type', 'scorch', 'min_area', 'max_area', 'ros_min',
                    'ros_max', 'ffdi_min', 'ffdi_max', 'gfdi_min', 'gfdi_max',
                    'temp_min', 'temp_max', 'rh_min', 'rh_max',
                    'sdi', 'smc_min', 'smc_max',
                    'pmc_min', 'pmc_max', 'wind_min', 'wind_max', 'wind_dir',
                    'grassland_curing_min', 'grassland_curing_max')


class EdgingPlanAdmin(PrescriptionMixin, SavePrescriptionMixin,
                      BaseAdmin):
    list_display = ("location_text", "fuel_type", "desirable_season", "strategies",
                    "ffdi", "gfdi", "ros", "sdi", "grassland_curing", "wind_dir", "wind")
    #filter_horizontal = ("fuel_types",)
    list_empty_form = True
    list_display_links = ("location_text",)
    actions = None
    form = EdgingPlanForm
    can_delete = True
    lock_after = 'endorsement'

    fieldsets = (
        (None, {
            "fields": ('location', 'fuel_type', 'desirable_season', 'strategies',
                       ('ffdi_min', 'ffdi_max'), ('gfdi_min', 'gfdi_max'),
                       ('ros_min', 'ros_max'), 'sdi',
                       ('grassland_curing_min', 'grassland_curing_max'),
                       'wind_dir', ('wind_min', 'wind_max'))
        }),
    )

    def ffdi(self, obj):
        return field_range(obj.ffdi_min, obj.ffdi_max)
    ffdi.short_description = mark_safe('<abbr title="Forest fire danger '
                                       'index">FFDI</abbr> range')
    ffdi.admin_order_field = 'ffdi_min'

    def gfdi(self, obj):
        return field_range(obj.gfdi_min, obj.gfdi_max)
    gfdi.short_description = mark_safe('<abbr title="Grassland fire danger '
                                       'index">GFDI</abbr> range')
    gfdi.admin_order_field = 'gfdi_min'

    def grassland_curing(self, obj):
        return field_range(obj.grassland_curing_min, obj.grassland_curing_max)
    grassland_curing.short_description = mark_safe('<abbr title="Grassland Curing Percent '
                                       'index">Grassland Curing</abbr> range')
    grassland_curing.admin_order_field = 'grassland_curing_min'

    def wind(self, obj):
        return field_range(obj.wind_min, obj.wind_max)
    wind.short_description = "Wind speed range (km/h)"
    wind.admin_order_field = 'wind_min'

    def ros(self, obj):
        return field_range(obj.ros_min, obj.ros_max)
    ros.short_description = mark_safe('<abbr title="Rate of spread '
                                      '">ROS</abbr> range (m/h)')
    ros.admin_order_field = 'ros_min'

    def location_text(self, obj):
        if obj.location:
            return obj.location
        else:
            return "Not entered"
    location_text.admin_order_field = 'location'


class LightingSequenceAdmin(PrescriptionMixin, SavePrescriptionMixin,
                            BaseAdmin):
    list_display = ("seqno", "cellname", "strategies", "fuel_description",
        "display_fuel_age", "display_ignition_types", "ffdi",
        "grassland_curing", "gfdi", "ros", "wind", "wind_dir", "resources")

    fieldsets = (
        (None, {
            "fields": (('seqno', 'cellname'), 'strategies', 'fuel_description',
                       ('fuel_age', 'fuel_age_unknown'), 'ignition_types',
                       ('ffdi_min', 'ffdi_max'),
                       ('grassland_curing_min', 'grassland_curing_max'),
                       ('gfdi_min', 'gfdi_max'), ('ros_min', 'ros_max'),
                       ('wind_min', 'wind_max'), 'wind_dir', 'resources')
        }),
    )

    actions = None
    form = LightingSequenceForm
    can_delete = True
    lock_after = 'endorsement'

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        kwargs['widget'] = ChosenSelectMultiple()
        return super(LightingSequenceAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs)

    def display_ignition_types(self, obj):
        output = "<ul>"
        for ignition_type in obj.ignition_types.all():
            output += "<li>%s</li>" % ignition_type
        output += "</ul>"
        return output
    display_ignition_types.short_description = "Planned Core Ignition Types"
    display_ignition_types.admin_order_field = 'ignition_types'
    display_ignition_types.allow_tags = True

    def display_fuel_age(self, obj):
        if obj.fuel_age_unknown:
            return "Unknown"
        else:
            return obj.fuel_age
    display_fuel_age.short_description = "Fuel Age (years)"
    display_fuel_age.admin_order_field = 'fuel_age'

    def ros(self, obj):
        return field_range(obj.ros_min, obj.ros_max)
    ros.short_description = mark_safe('<abbr title="Rate of spread">ROS</abbr>'
                                      ' range (m/h)')
    ros.admin_order_field = 'ros_min'

    def ffdi(self, obj):
        return field_range(obj.ffdi_min, obj.ffdi_max)
    ffdi.short_description = mark_safe('<abbr title="Forest fire danger '
                                       'index">FFDI</abbr> range')
    ffdi.admin_order_field = 'ffdi_min'

    def gfdi(self, obj):
        return field_range(obj.gfdi_min, obj.gfdi_max)
    gfdi.short_description = mark_safe('<abbr title="Grassland fire danger '
                                       'index">GFDI</abbr> range')
    gfdi.admin_order_field = 'gfdi_min'

    def grassland_curing(self, obj):
        return field_range(obj.grassland_curing_min, obj.grassland_curing_max)
    grassland_curing.short_description = mark_safe('<abbr title="Grassland Curing Percent '
                                       'index">Grassland Curing</abbr> range')
    grassland_curing.admin_order_field = 'grassland_curing_min'

    def wind(self, obj):
        return field_range(obj.wind_min, obj.wind_max)
    wind.short_description = "Wind speed range (km/h)"
    wind.admin_order_field = 'wind_min'


class ExclusionAreaAdmin(PrescriptionMixin, SavePrescriptionMixin,
                         BaseAdmin):
    list_display = ("location", "description", "detail")
    list_editable = ("location", "description", "detail")
    list_empty_form = True
    list_display_links = (None,)
    actions = None
    can_delete = True
    lock_after = "endorsement"


class SignInspectionAdmin(PrescriptionMixin, SavePrescriptionMixin,
                          BaseAdmin):
    prescription_filter_field = "way__prescription"
    list_display = ("date_inspected", "way", "time_inspected", "comments",
                    "inspector")
    list_editable = ("way", "comments", "inspector")
    list_empty_form = True
    list_display_links = (None,)
    actions = None
    can_delete = True
    lock_after = 'endorsement'

    def date_inspected(self, obj):
        return date(obj.inspected)
    date_inspected.short_description = "Date Inspected"

    def time_inspected(self, obj):
        return time(obj.inspected)
    time_inspected.short_description = "Time of Inspection"


class RoadSegmentAdmin(PrescriptionMixin, SavePrescriptionMixin,
                       BaseAdmin):
    list_display = ("name", "road_type", "traffic_considerations",
                    "traffic_diagram", "signs_installed", "signs_removed")
    list_editable = ("name", "road_type", "traffic_considerations",
                     "traffic_diagram", "signs_installed", "signs_removed")
    list_empty_form = True
    list_display_links = (None,)
    actions = None
    can_delete = True
    lock_after = "endorsement"

    def get_list_editable(self, request):
        """
        OVERWRITE SavePrescriptions Version!!!
        ======================================
        Restrict editing when the ePFP reaches certain stages of completion.
        If the user is part of the ePFP Application Administrator, allow them to edit
        anyway.
        """
        current = self.prescription
        if request.user.has_perm('prescription.can_admin') or self.lock_after == 'never':
            return self.list_editable

        if (current.is_closed):
            return ('id',)

        if (not current.is_draft):
            return ('id','signs_installed','signs_removed')
        else:
            return self.list_editable

    def get_readonly_fields(self, request, obj=None):
        #import ipdb; ipdb.set_trace()
        if self.prescription.is_draft or request.user.has_perm('prescription.can_admin'):
            return self.readonly_fields
        else:
            return ("name", "road_type", "traffic_considerations",
                   "traffic_diagram")

    def changelist_view(self, request, prescription_id, extra_context=None):
        """ Add exclusions to the context """
        prescription = Prescription.objects.get(id = int(prescription_id))
        tcd_exclusions = None
        for tcd_exclusion in settings.TCD_EXCLUSIONS:
            if not tcd_exclusion[0] or (tcd_exclusion[0] and prescription.created and prescription.created >= tcd_exclusion[0]):
                tcd_exclusions = tcd_exclusion[1]
                break
        context = {
            'tcd_exclusions': tcd_exclusions or "[]"
        }
        context.update(extra_context or {})

        return super(RoadSegmentAdmin, self).changelist_view(
            request, prescription_id, extra_context=context)


class TrailSegmentAdmin(PrescriptionMixin, SavePrescriptionMixin,
                        BaseAdmin):
    list_display = ("name", "diversion", "start", "start_signage", "stop",
                    "stop_signage", "signs_installed", "signs_removed")
    list_editable = ("name", "diversion", "start", "start_signage",
                     "stop", "stop_signage", "signs_installed",
                     "signs_removed")
    list_empty_form = True
    list_display_links = (None,)
    actions = None
    can_delete = True
    lock_after = "endorsement"

    def get_readonly_fields(self, request, obj=None):
        if self.prescription.is_draft or request.user.has_perm('prescription.can_admin'):
            return self.readonly_fields
        else:
            return ("name", "diversion", "start", "start_signage",
                    "stop", "stop_signage")
    def get_list_editable(self, request):
        """
        OVERWRITE SavePrescriptions Version!!!
        ======================================
        Restrict editing when the ePFP reaches certain stages of completion.
        If the user is part of the ePFP Application Administrator, allow them to edit
        anyway.
        """
        current = self.prescription
        if request.user.has_perm('prescription.can_admin') or self.lock_after == 'never':
            return self.list_editable

        if (current.is_closed):
            return ('id',)

        if (not current.is_draft):
            return ('id','signs_installed','signs_removed')
        else:
            return self.list_editable
