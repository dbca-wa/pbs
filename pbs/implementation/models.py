from __future__ import (division, print_function, unicode_literals,
                        absolute_import)
import logging
logger = logging.getLogger("log." + __name__)

import os
import subprocess
from swingers.models.auth import Audit
from swingers import models
from django.conf import settings
from django.forms import ValidationError
from django.utils import timezone
from django.template.defaultfilters import date
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.files.storage import FileSystemStorage
from django.utils.safestring import mark_safe

from pbs.prescription.models import Prescription, Season, FuelType
from pbs.implementation.utils import field_range
from pbs.document.utils import get_dimensions       #PWM PDF work

trafficdiagram_storage = FileSystemStorage(
    location=os.path.join(settings.STATIC_ROOT, "pbs", "traffic-control-diagrams"),
    #location=os.path.join(settings.STATIC_ROOT, "traffic-control-diagrams"),
    base_url=settings.STATIC_URL + "pbs/traffic-control-diagrams/")



class OperationalOverview(Audit):
    prescription = models.ForeignKey(Prescription, on_delete=models.PROTECT)
    overview = models.TextField(blank=True, null=True)

    def __str__(self):
        # return self.overview
        return str(self.overview)

    class Meta:
        get_latest_by = 'id'



class IgnitionTypeManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)



class IgnitionType(models.Model):
    """
    """
    name = models.CharField(max_length=64, unique=True)
    objects = IgnitionTypeManager()

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)


class TrafficControlDiagramManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)

    def get_query_set(self):
        qs = super(TrafficControlDiagramManager, self).get_query_set()
        qs = qs.filter(display_order__gte=0, archive_date__isnull=True).order_by('display_order', 'name')
        return qs


class TrafficControlDiagram(models.Model):
    """
    """
    name = models.CharField(max_length=64, unique=True)
    path = models.FileField(storage=trafficdiagram_storage, upload_to=".")
    display_order = models.IntegerField(default=1)
    archive_date = models.DateField(null=True, blank=True)
    objects = TrafficControlDiagramManager()

    @property
    def dimensions(self):
        """width, height = subprocess.check_output([
            "identify", "-format", "%Wx%H,",
            self.document.path
        ]).split(",")[0].strip().split("x")
        return {"width": width, "height": height}
        """
        dimensions_info = get_dimensions(self.document.path)
        logger.info(str( {"width": dimensions_info.width, "height": dimensions_info.height}))
        return {"width": dimensions_info.width, "height": dimensions_info.height}

    @property
    def document(self):
        return self.path

    @property
    def descriptor(self):
        return self.name

    @property
    def modified(self):
        return False

    @property
    def filename(self):
        return os.path.basename(self.path.path)

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    class Meta:
        ordering = ['id']
        verbose_name = "Traffic Control Diagram"
        verbose_name_plural = "Traffic Control Diagrams"



class Way(Audit):
    prescription = models.ForeignKey(
        Prescription, help_text="Prescription this belongs to.", on_delete=models.PROTECT)
    name = models.CharField(max_length=300)
    signs_installed = models.DateField(
        verbose_name="Signs Installed", null=True, blank=True)
    signs_removed = models.DateField(
        verbose_name="Signs Removed", null=True, blank=True)

    def __str__(self):
        return self.name

    def clean_signs_removed(self):
        if ((self.signs_removed and self.signs_installed and
             self.signs_removed < self.signs_installed)):
            raise ValidationError('Signs cannot be removed earlier than the '
                                  'install date.')



class RoadSegment(Way):
    road_type = models.TextField(
        verbose_name="Road Type",
        blank=True)
    traffic_considerations = models.TextField(
        blank=True, verbose_name="Special Traffic Considerations")
    traffic_diagram = models.ForeignKey(
        TrafficControlDiagram, null=True, blank=True,
        verbose_name="Select Traffic Control Diagram", on_delete=models.PROTECT)

    _required_fields = ('name', 'road_type',)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = "Road"
        verbose_name_plural = "Roads"



class TrailSegment(Way):
    start = models.TextField(
        blank=True, verbose_name="Start Location")
    start_signage = models.TextField(
        blank=True, verbose_name="Description of Start Signage")
    stop = models.TextField(
        blank=True, verbose_name="Stop Location")
    stop_signage = models.TextField(
        blank=True, verbose_name="Description of Stop Signage")
    diversion = models.BooleanField(
        verbose_name="Is there a Diversion Map?", default=False)

    _required_fields = ('name', )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = "Track/Trail"
        verbose_name_plural = "Tracks/Trails"



class SignInspection(Audit):
    way = models.ForeignKey(
        Way, verbose_name="Road/Track/Trail Name", on_delete=models.PROTECT)
    inspected = models.DateTimeField(
        default=timezone.now, verbose_name="Date Inspected")
    comments = models.TextField()
    inspector = models.TextField(verbose_name="Inspecting Officer")

    def __str__(self):
        return "%s (%s)" % (self.way.name, date(self.inspected))

    @property
    def prescription(self):
        return self.way.prescription

    class Meta:
        ordering = ['id']
        verbose_name = "Sign Inspection"
        verbose_name_plural = "Sign Inspections"



class BurningPrescription(Audit):
    prescription = models.ForeignKey(
        Prescription, help_text="Prescription this fuel schedule belongs to.", on_delete=models.PROTECT)
    # NOTE: the fuel_type field will be deprecated in favour of a reference to
    # the VegetationType model in the prescription app.

    fuel_type = models.ForeignKey(FuelType,
        verbose_name="Fuel Type", blank=True, null=True, on_delete=models.PROTECT)
    scorch = models.PositiveIntegerField(
        help_text="Maximum Scorch Height (m)",
        verbose_name="Scorch Height",
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        blank=True, null=True)
    min_area = models.PositiveIntegerField(
        verbose_name="Min Area to be Burnt (%)",
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        blank=True, null=True)
    max_area = models.PositiveIntegerField(
        verbose_name="Max Area to be Burnt (%)",
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        blank=True, null=True)
    ros_min = models.PositiveIntegerField(
        verbose_name="Min ROS (m/h)",
        validators=[MinValueValidator(0), MaxValueValidator(10000)],
        blank=True, null=True)
    ros_max = models.PositiveIntegerField(
        verbose_name="Max ROS (m/h)",
        validators=[MinValueValidator(0), MaxValueValidator(10000)],
        blank=True, null=True)
    ffdi_min = models.PositiveIntegerField(
        verbose_name="Min FFDI",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True)
    ffdi_max = models.PositiveIntegerField(
        verbose_name="Max FFDI",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True)
    gfdi_min = models.PositiveIntegerField(
        verbose_name="Min GFDI",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True)
    gfdi_max = models.PositiveIntegerField(
        verbose_name="Max GFDI",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True)
    temp_min = models.PositiveIntegerField(
        verbose_name="Min Temp (degrees C)",
        validators=[MinValueValidator(0), MaxValueValidator(60)],
        blank=True, null=True)
    temp_max = models.PositiveIntegerField(
        verbose_name="Max Temp (degress C)",
        validators=[MinValueValidator(0), MaxValueValidator(60)],
        blank=True, null=True)
    rh_min = models.PositiveIntegerField(
        verbose_name="Min Relative Humidity (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True)
    rh_max = models.PositiveIntegerField(
        verbose_name="Max Relative Humidity (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True)
    sdi = models.TextField(verbose_name="SDI", blank=True, null=True)
    smc_min = models.PositiveIntegerField(
        verbose_name="Min Surface Moisture Content (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True)
    smc_max = models.PositiveIntegerField(
        verbose_name="Max Surface Moisture Content (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True)
    pmc_min = models.PositiveIntegerField(
        verbose_name="Min Profile Moisture Content (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True)
    pmc_max = models.PositiveIntegerField(
        verbose_name="Max Profile Moisture Content (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        blank=True, null=True)
    wind_min = models.PositiveIntegerField(
        verbose_name="Min Wind Speed (km/h)", blank=True, null=True,
        validators=[MinValueValidator(0), MaxValueValidator(200)])
    wind_max = models.PositiveIntegerField(
        verbose_name="Max Wind Speed (km/h)",
        validators=[MinValueValidator(0), MaxValueValidator(200)],
        blank=True, null=True)
    wind_dir = models.TextField(verbose_name="Wind Direction",
        blank=True, null=True)
    grassland_curing_min = models.PositiveIntegerField(
        verbose_name="Grassland Curing % Min",
        validators=[MinValueValidator(0), MaxValueValidator(200)],
        blank=True, null=True)
    grassland_curing_max = models.PositiveIntegerField(
        verbose_name="Grassland Curing % Max",
        validators=[MinValueValidator(0), MaxValueValidator(200)],
        blank=True, null=True)

    def area(self):
        return field_range(self.min_area, self.max_area, True)
    area.short_description = "Area to be Burnt (%)"
    area.admin_order_field = "area_max"

    def ros(self):
        return field_range(self.ros_min, self.ros_max)
    ros.short_description = mark_safe(
        '<abbr title="Rate of Spread">ROS</abbr> Range')
    ros.admin_order_field = "ros_max"

    def ffdi(self):
        return field_range(self.ffdi_min, self.ffdi_max)
    ffdi.short_description = mark_safe(
        '<abbr title="Forecast Fire Danger Index">FFDI</abbr> Range')
    ffdi.admin_order_field = "ffdi_max"

    def gfdi(self):
        return field_range(self.gfdi_min, self.gfdi_max)
    gfdi.short_description = mark_safe(
        '<abbr title="Global Fire Danger Index">GFDI</abbr> Range')
    gfdi.admin_order_field = "gfdi_max"

    def temp(self):
        return field_range(self.temp_min, self.temp_max)
    temp.short_description = "Temperature Range"
    temp.admin_order_field = "temp_max"

    def rh(self):
        return field_range(self.rh_min, self.rh_max, True)
    rh.short_description = mark_safe(
        '<abbr title="Relative Humidity">RH</abbr> Range (%)')
    temp.admin_order_field = "temp_max"

    sdi.short_description = mark_safe(
        '<abbr title="Soil Dryness Index">SDI</abbr> Range')

    def smc(self):
        return field_range(self.smc_min, self.smc_max)
    smc.short_description = mark_safe(
        '<abbr title="Surface Moisture Content">SMC</abbr> Range')
    smc.admin_order_field = "smc_max"

    def pmc(self):
        return field_range(self.pmc_min, self.pmc_max)
    pmc.short_description = mark_safe(
        '<abbr title="Profile Moisture Content">PMC</abbr> Range')
    pmc.admin_order_field = "pmc_max"

    def wind(self):
        return field_range(self.wind_min, self.wind_max)
    wind.short_description = "Wind Speed Range (km/h)"
    wind.admin_order_field = "wind_max"

    def grassland_curing(self):
        return field_range(self.grassland_curing_min, self.grassland_curing_max)
    grassland_curing.short_description = mark_safe(
        '<abbr title="Grassland Curing Percent">GLC</abbr> Range')
    grassland_curing.admin_order_field = "grassland_curing_max"

    def clean_sdi(self):
        if self.sdi == '':
            self.sdi = "N/A"

    def __str__(self):
        return self.fuel_type.name

    class Meta:
        verbose_name = "Burning Prescription"
        verbose_name_plural = "Burning Prescriptions"



class EdgingPlan(Audit):
    prescription = models.ForeignKey(
        Prescription, help_text="Prescription this edging plan belongs to.", on_delete=models.PROTECT)
    location = models.TextField(
        verbose_name="Edge Location", blank=True, null=True,
        help_text="Textual description of edge & its location")
    desirable_season = models.PositiveSmallIntegerField(
        verbose_name="Desirable Season",
        max_length=64, choices=Season.SEASON_CHOICES, blank=True, null=True)
    strategies = models.TextField(
        help_text="Textual description of strategies for this plan",
        blank=True, null=True)
    # NOTE: the fuel_type field will be deprecated in favour of a reference to
    # the VegetationType model in the prescription app.

    fuel_type = models.ForeignKey(FuelType,
        verbose_name="Fuel Type", blank=True, null=True, on_delete=models.SET_NULL)
    ffdi_min = models.PositiveIntegerField(
        verbose_name="Min FFDI", blank=True, null=True)
    ffdi_max = models.PositiveIntegerField(
        verbose_name="Max FFDI", blank=True, null=True)
    gfdi_min = models.PositiveIntegerField(
        verbose_name="Min GFDI", blank=True, null=True)
    gfdi_max = models.PositiveIntegerField(
        verbose_name="Max GFDI", blank=True, null=True)
    sdi = models.TextField(verbose_name="SDI", blank=True, null=True)
    wind_min = models.PositiveIntegerField(
        verbose_name="Min Wind Speed (km/h)", blank=True, null=True)
    wind_max = models.PositiveIntegerField(
        verbose_name="Max Wind speed (km/h)", blank=True, null=True)
    wind_dir = models.TextField(verbose_name="Wind Direction",
        blank=True, null=True)
    ros_min = models.PositiveIntegerField(
        verbose_name="Min ROS (m/h)", blank=True, null=True)
    ros_max = models.PositiveIntegerField(
        verbose_name="Max ROS (m/h)", blank=True, null=True)
    grassland_curing_min = models.PositiveIntegerField(
        verbose_name="Grassland Curing % Min", blank=True, null=True)
    grassland_curing_max = models.PositiveIntegerField(
        verbose_name="Grassland Curing % Max", blank=True, null=True)

    def ffdi(self):
        return field_range(self.ffdi_min, self.ffdi_max)
    ffdi.short_description = mark_safe(
        '<abbr title="Forecast Fire Danger Index">FFDI</abbr> Range')
    ffdi.admin_order_field = 'ffdi_min'

    def gfdi(self):
        return field_range(self.gfdi_min, self.gfdi_max)
    gfdi.short_description = mark_safe(
        '<abbr title="Grassland Fire Danger Index">FFDI</abbr> Range')
    gfdi.admin_order_field = "gfdi_max"

    def wind(self):
        return "%d-%d" % (self.wind_min, self.wind_max)
    wind.short_description = "Wind Speed Range (km/h)"

    def grassland_curing(self):
        return field_range(self.grassland_curing_min, self.grassland_curing_max)
    grassland_curing.short_description = mark_safe(
        '<abbr title="Grassland Curing Percent</abbr> Range')
    grassland_curing.admin_order_field = "grassland_curing_max"

    def ros(self):
        return field_range(self.ros_min, self.ros_max)
    ros.short_description = mark_safe(
        '<abbr title="Rate of Spread">ROS</abbr> Range')

    def clean_sdi(self):
        if self.sdi == '':
            self.sdi = "N/A"

    def __str__(self):
        return self.location

    class Meta:
        verbose_name = "Edging Plan"
        verbose_name_plural = "Edging Plans"
        ordering = ['created']



class LightingSequence(Audit):
    prescription = models.ForeignKey(
        Prescription,
        help_text="Prescription this lighting sequence belongs to.", on_delete=models.PROTECT)
    seqno = models.PositiveSmallIntegerField(
        verbose_name="Lighting Sequence Number",
        choices=Prescription.INT_CHOICES)
    cellname = models.TextField(verbose_name="Cell Name")
    strategies = models.TextField(
        help_text="Textual description of strategies for this sequence")
    wind_min = models.PositiveIntegerField(
        verbose_name="Min Wind Speed (km/h)", validators=[MaxValueValidator(200)], blank=True)
    wind_max = models.PositiveIntegerField(
        verbose_name="Max Wind Speed (km/h)",
        validators=[MinValueValidator(0), MaxValueValidator(200)], blank=True)
    wind_dir = models.TextField(verbose_name="Wind Direction")
    fuel_description = models.TextField(
        help_text="Textual description of the fuel for this sequence")
    fuel_age = models.PositiveSmallIntegerField(
        verbose_name="Fuel Age",
        help_text="Fuel Age in years",
        null=True, blank=True)
    fuel_age_unknown = models.BooleanField(
        verbose_name="Fuel Age Unknown?",
        default=False)
    ignition_types = models.ManyToManyField(
        IgnitionType, verbose_name="Planned Core Ignition Type")
    ffdi_min = models.PositiveIntegerField(verbose_name="FFDI Min", blank=True)
    ffdi_max = models.PositiveIntegerField(verbose_name="FFDI Max", blank=True)
    gfdi_min = models.PositiveIntegerField(verbose_name="GFDI Min", blank=True)
    gfdi_max = models.PositiveIntegerField(verbose_name="GFDI Max", blank=True)
    grassland_curing_min = models.PositiveIntegerField(
        verbose_name="Grassland Curing Min", blank=True)
    grassland_curing_max = models.PositiveIntegerField(
        verbose_name="Grassland Curing Max", blank=True)
    ros_min = models.PositiveIntegerField(verbose_name="ROS Min (m/h)", blank=True)
    ros_max = models.PositiveIntegerField(verbose_name="ROS Max (m/h)", blank=True)
    resources = models.TextField(
        verbose_name="Specialist Resources", blank=True)

    _required_fields = ('seqno', 'cellname', 'strategies',
                        'fuel_description', 'fuel_age', 'fuel_age_unknown',
                        'ignition_types', 'ffdi_min', 'ffdi_max',
                        'ros_min', 'ros_max', 'wind_min', 'wind_max',
                        'wind_dir')

    class Meta:
        verbose_name = "Lighting Sequence"
        verbose_name_plural = "Lighting Sequences"
        ordering = ['id']

    def wind_speed(self):
        return field_range(self.wind_min, self.wind_max)
    wind_speed.short_description = mark_safe(
        '<abbr title="Wind Speed">Wind Speed</abbr> Range')

    def ffdi(self):
        return field_range(self.ffdi_min, self.ffdi_max)
    ffdi.short_description = mark_safe(
        '<abbr title="Forecast Fire Danger Index">FFDI</abbr> Range')

    def gfdi(self):
        return field_range(self.gfdi_min, self.gfdi_max)
    gfdi.short_description = mark_safe(
        '<abbr title="Grassland Fire Danger Index">FFDI</abbr> Range')
    gfdi.admin_order_field = "gfdi_max"

    def grassland_curing(self):
        return field_range(self.grassland_curing_min, self.grassland_curing_max)
    grassland_curing.short_description = mark_safe(
        '<abbr title="Grassland Curing Percent</abbr> Range')
    grassland_curing.admin_order_field = "grassland_curing_max"

    def ros(self):
        return field_range(self.ros_min, self.ros_max)
    ros.short_description = mark_safe(
        '<abbr title="Rate of Spread">ROS</abbr> Range')

    def clean_fuel_age(self):
        if self.fuel_age_unknown and self.fuel_age:
            raise ValidationError("You must either enter a fuel age or tick "
                                  "Fuel Age Unknown.")
        if not (self.fuel_age_unknown or self.fuel_age):
            raise ValidationError("You must enter a fuel age or tick Fuel Age "
                                  "Unknown.")

    def clean_ffdi_min(self):
        if self.ffdi_min is None:
            self.ffdi_min = 0

    def clean_ffdi_max(self):
        if self.ffdi_max is None:
            self.ffdi_max = 0

    def clean_gfdi_min(self):
        if self.gfdi_min is None:
            self.gfdi_min = 0

    def clean_gfdi_max(self):
        if self.gfdi_max is None:
            self.gfdi_max = 0

    def clean_grassland_curing_min(self):
        if self.grassland_curing_min is None:
            self.grassland_curing_min = 0

    def clean_grassland_curing_max(self):
        if self.grassland_curing_max is None:
            self.grassland_curing_max = 0

    def clean_ros_min(self):
        if self.ros_min is None:
            self.ros_min = 0

    def clean_ros_max(self):
        if self.ros_max is None:
            self.ros_max = 0

    def clean_wind_min(self):
        if self.wind_min is None:
            self.wind_min = 0

    def clean_wind_max(self):
        if self.wind_max is None:
            self.wind_max = 0

    def __str__(self):
        return "{0}. {1}".format(self.seqno, self.cellname)



class ExclusionArea(Audit):
    prescription = models.ForeignKey(
        Prescription, help_text="Prescription this exclusion area belongs to.", on_delete=models.PROTECT)
    description = models.TextField()
    location = models.TextField()
    detail = models.TextField(verbose_name="How will fire be excluded?")

    _required_fields = ('location', 'description',
                        'detail')

    def __str__(self):
        return "{0} - {1}".format(self.location, self.description)

import reversion
reversion.register(OperationalOverview)
reversion.register(BurningPrescription)
reversion.register(EdgingPlan)
reversion.register(LightingSequence)
reversion.register(ExclusionArea)