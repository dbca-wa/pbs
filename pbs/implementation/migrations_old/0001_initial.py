# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ("prescription", "0001_initial"),
    )

    def forwards(self, orm):
        # Adding model 'FuelType'
        db.create_table(u'implementation_fueltype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_fueltype_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_fueltype_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
        ))
        db.send_create_signal(u'implementation', ['FuelType'])

        # Adding model 'IgnitionType'
        db.create_table(u'implementation_ignitiontype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
        ))
        db.send_create_signal(u'implementation', ['IgnitionType'])

        # Adding model 'TrafficControlDiagram'
        db.create_table(u'implementation_trafficcontroldiagram', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('path', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal(u'implementation', ['TrafficControlDiagram'])

        # Adding model 'Way'
        db.create_table(u'implementation_way', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_way_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_way_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('signs_installed', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('signs_removed', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'implementation', ['Way'])

        # Adding model 'RoadSegment'
        db.create_table(u'implementation_roadsegment', (
            (u'way_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['implementation.Way'], unique=True, primary_key=True)),
            ('road_type', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('traffic_considerations', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('traffic_diagram', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['implementation.TrafficControlDiagram'], null=True, blank=True)),
        ))
        db.send_create_signal(u'implementation', ['RoadSegment'])

        # Adding model 'TrailSegment'
        db.create_table(u'implementation_trailsegment', (
            (u'way_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['implementation.Way'], unique=True, primary_key=True)),
            ('start', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('start_signage', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('stop', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('stop_signage', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('diversion', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'implementation', ['TrailSegment'])

        # Adding model 'SignInspection'
        db.create_table(u'implementation_signinspection', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_signinspection_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_signinspection_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('way', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['implementation.Way'])),
            ('inspected', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('comments', self.gf('django.db.models.fields.TextField')()),
            ('inspector', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'implementation', ['SignInspection'])

        # Adding model 'BurningPrescription'
        db.create_table(u'implementation_burningprescription', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_burningprescription_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_burningprescription_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
            ('fuel_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['implementation.FuelType'])),
            ('scorch', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('min_area', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('max_area', self.gf('django.db.models.fields.PositiveIntegerField')(default=100)),
            ('ros_min', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('ros_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('ffdi_min', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('ffdi_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('temp_min', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('temp_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('rh_min', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('rh_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('glc_pct', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('sdi', self.gf('django.db.models.fields.TextField')()),
            ('smc_min', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('smc_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('pmc_min', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('pmc_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('wind_min', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('wind_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('wind_dir', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'implementation', ['BurningPrescription'])

        # Adding model 'EdgingPlan'
        db.create_table(u'implementation_edgingplan', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_edgingplan_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_edgingplan_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
            ('location', self.gf('django.db.models.fields.TextField')()),
            ('desirable_season', self.gf('django.db.models.fields.PositiveSmallIntegerField')(max_length=64)),
            ('strategies', self.gf('django.db.models.fields.TextField')()),
            ('fuel_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['implementation.FuelType'], null=True, blank=True)),
            ('ffdi_min', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('ffdi_max', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('sdi', self.gf('django.db.models.fields.TextField')()),
            ('wind_min', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('wind_max', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('wind_dir', self.gf('django.db.models.fields.TextField')()),
            ('ros_min', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('ros_max', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'implementation', ['EdgingPlan'])

        # Adding model 'LightingSequence'
        db.create_table(u'implementation_lightingsequence', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_lightingsequence_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_lightingsequence_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
            ('seqno', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('cellname', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('strategies', self.gf('django.db.models.fields.TextField')()),
            ('wind_min', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('wind_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('wind_dir', self.gf('django.db.models.fields.TextField')()),
            ('fuel_description', self.gf('django.db.models.fields.TextField')()),
            ('fuel_age', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('fuel_age_unknown', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('ffdi_min', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('ffdi_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('ros_min', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('ros_max', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('resources', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'implementation', ['LightingSequence'])

        # Adding unique constraint on 'LightingSequence', fields ['prescription', 'seqno']
        db.create_unique(u'implementation_lightingsequence', ['prescription_id', 'seqno'])

        # Adding M2M table for field ignition_types on 'LightingSequence'
        db.create_table(u'implementation_lightingsequence_ignition_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('lightingsequence', models.ForeignKey(orm[u'implementation.lightingsequence'], null=False)),
            ('ignitiontype', models.ForeignKey(orm[u'implementation.ignitiontype'], null=False))
        ))
        db.create_unique(u'implementation_lightingsequence_ignition_types', ['lightingsequence_id', 'ignitiontype_id'])

        # Adding model 'ExclusionArea'
        db.create_table(u'implementation_exclusionarea', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_exclusionarea_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'implementation_exclusionarea_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('location', self.gf('django.db.models.fields.TextField')()),
            ('detail', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'implementation', ['ExclusionArea'])


    def backwards(self, orm):
        # Removing unique constraint on 'LightingSequence', fields ['prescription', 'seqno']
        db.delete_unique(u'implementation_lightingsequence', ['prescription_id', 'seqno'])

        # Deleting model 'FuelType'
        db.delete_table(u'implementation_fueltype')

        # Deleting model 'IgnitionType'
        db.delete_table(u'implementation_ignitiontype')

        # Deleting model 'TrafficControlDiagram'
        db.delete_table(u'implementation_trafficcontroldiagram')

        # Deleting model 'Way'
        db.delete_table(u'implementation_way')

        # Deleting model 'RoadSegment'
        db.delete_table(u'implementation_roadsegment')

        # Deleting model 'TrailSegment'
        db.delete_table(u'implementation_trailsegment')

        # Deleting model 'SignInspection'
        db.delete_table(u'implementation_signinspection')

        # Deleting model 'BurningPrescription'
        db.delete_table(u'implementation_burningprescription')

        # Deleting model 'EdgingPlan'
        db.delete_table(u'implementation_edgingplan')

        # Deleting model 'LightingSequence'
        db.delete_table(u'implementation_lightingsequence')

        # Removing M2M table for field ignition_types on 'LightingSequence'
        db.delete_table('implementation_lightingsequence_ignition_types')

        # Deleting model 'ExclusionArea'
        db.delete_table(u'implementation_exclusionarea')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'implementation.burningprescription': {
            'Meta': {'object_name': 'BurningPrescription'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_burningprescription_created'", 'to': u"orm['auth.User']"}),
            'ffdi_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ffdi_min': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'fuel_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['implementation.FuelType']"}),
            'glc_pct': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_area': ('django.db.models.fields.PositiveIntegerField', [], {'default': '100'}),
            'min_area': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_burningprescription_modified'", 'to': u"orm['auth.User']"}),
            'pmc_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'pmc_min': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"}),
            'rh_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'rh_min': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ros_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ros_min': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'scorch': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'sdi': ('django.db.models.fields.TextField', [], {}),
            'smc_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'smc_min': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'temp_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'temp_min': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'wind_dir': ('django.db.models.fields.TextField', [], {}),
            'wind_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'wind_min': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        u'implementation.edgingplan': {
            'Meta': {'object_name': 'EdgingPlan'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_edgingplan_created'", 'to': u"orm['auth.User']"}),
            'desirable_season': ('django.db.models.fields.PositiveSmallIntegerField', [], {'max_length': '64'}),
            'ffdi_max': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'ffdi_min': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'fuel_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['implementation.FuelType']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.TextField', [], {}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_edgingplan_modified'", 'to': u"orm['auth.User']"}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"}),
            'ros_max': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'ros_min': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'sdi': ('django.db.models.fields.TextField', [], {}),
            'strategies': ('django.db.models.fields.TextField', [], {}),
            'wind_dir': ('django.db.models.fields.TextField', [], {}),
            'wind_max': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'wind_min': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'implementation.exclusionarea': {
            'Meta': {'object_name': 'ExclusionArea'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_exclusionarea_created'", 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'detail': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.TextField', [], {}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_exclusionarea_modified'", 'to': u"orm['auth.User']"}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"})
        },
        u'implementation.fueltype': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'FuelType'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_fueltype_created'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_fueltype_modified'", 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        u'implementation.ignitiontype': {
            'Meta': {'object_name': 'IgnitionType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        u'implementation.lightingsequence': {
            'Meta': {'unique_together': "((u'prescription', u'seqno'),)", 'object_name': 'LightingSequence'},
            'cellname': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_lightingsequence_created'", 'to': u"orm['auth.User']"}),
            'ffdi_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ffdi_min': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'fuel_age': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fuel_age_unknown': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'fuel_description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignition_types': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['implementation.IgnitionType']", 'symmetrical': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_lightingsequence_modified'", 'to': u"orm['auth.User']"}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"}),
            'resources': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'ros_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ros_min': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'seqno': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'strategies': ('django.db.models.fields.TextField', [], {}),
            'wind_dir': ('django.db.models.fields.TextField', [], {}),
            'wind_max': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'wind_min': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        u'implementation.roadsegment': {
            'Meta': {'ordering': "[u'id']", 'object_name': 'RoadSegment', '_ormbases': [u'implementation.Way']},
            'road_type': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'traffic_considerations': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'traffic_diagram': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['implementation.TrafficControlDiagram']", 'null': 'True', 'blank': 'True'}),
            u'way_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['implementation.Way']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'implementation.signinspection': {
            'Meta': {'ordering': "[u'id']", 'object_name': 'SignInspection'},
            'comments': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_signinspection_created'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inspected': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'inspector': ('django.db.models.fields.TextField', [], {}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_signinspection_modified'", 'to': u"orm['auth.User']"}),
            'way': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['implementation.Way']"})
        },
        u'implementation.trafficcontroldiagram': {
            'Meta': {'ordering': "[u'id']", 'object_name': 'TrafficControlDiagram'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'path': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        u'implementation.trailsegment': {
            'Meta': {'ordering': "[u'id']", 'object_name': 'TrailSegment', '_ormbases': [u'implementation.Way']},
            'diversion': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'start_signage': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'stop': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'stop_signage': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'way_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['implementation.Way']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'implementation.way': {
            'Meta': {'object_name': 'Way'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_way_created'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'implementation_way_modified'", 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"}),
            'signs_installed': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'signs_removed': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        u'prescription.district': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'District'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Region']"})
        },
        u'prescription.endorsingrole': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'EndorsingRole'},
            'disclaimer': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '320'})
        },
        u'prescription.forecastarea': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'ForecastArea'},
            'districts': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['prescription.District']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'prescription.prescription': {
            'Meta': {'object_name': 'Prescription'},
            'aircraft_burn': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'allocation': ('django.db.models.fields.PositiveSmallIntegerField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'approval_status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'approval_status_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'area': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'max_digits': '12', 'decimal_places': '1'}),
            'biodiversity_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'biodiversity_text_additional': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'burn_id': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'bushfire_act_zone': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'bushfire_risk_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'contentious': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'contentious_rationale': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_prescription_created'", 'to': u"orm['auth.User']"}),
            'critical_stakeholders': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'prescriptions_critical'", 'symmetrical': 'False', 'to': u"orm['stakeholder.CriticalStakeholder']"}),
            'district': ('smart_selects.db_fields.ChainedForeignKey', [], {'to': u"orm['prescription.District']", 'null': 'True', 'blank': 'True'}),
            'endorsement_status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'endorsement_status_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'endorsing_roles': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['prescription.EndorsingRole']", 'symmetrical': 'False'}),
            'endorsing_roles_determined': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'forecast_areas': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['prescription.ForecastArea']", 'null': 'True', 'blank': 'True'}),
            'forest_blocks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignition_completed_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'ignition_status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'ignition_status_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'last_season': ('django.db.models.fields.PositiveSmallIntegerField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'last_season_unknown': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_year': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'last_year_unknown': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': "u'320'", 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_prescription_modified'", 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'perimeter': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'max_digits': '12', 'decimal_places': '1'}),
            'planned_season': ('django.db.models.fields.PositiveSmallIntegerField', [], {'max_length': '64'}),
            'planned_year': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '4'}),
            'planning_status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'planning_status_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'prescribing_officer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'prohibited_period': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'public_contacts': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "u'prescriptions_public_contact'", 'symmetrical': 'False', 'through': u"orm['stakeholder.PublicContact']", 'to': u"orm['stakeholder.Stakeholder']"}),
            'purposes': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['prescription.Purpose']", 'symmetrical': 'False'}),
            'rationale': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Region']"}),
            'regional_objectives': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['prescription.RegionalObjective']", 'null': 'True', 'blank': 'True'}),
            'remote_sensing_priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '4'}),
            'shires': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['prescription.Shire']", 'null': 'True', 'blank': 'True'}),
            'short_code': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'status_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'tenures': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['prescription.Tenure']", 'symmetrical': 'False', 'blank': 'True'}),
            'treatment_percentage': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'vegetation_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'vegetation_types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['prescription.VegetationType']", 'null': 'True', 'blank': 'True'})
        },
        u'prescription.purpose': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'Purpose'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'prescription.region': {
            'Meta': {'object_name': 'Region'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        u'prescription.regionalobjective': {
            'Meta': {'object_name': 'RegionalObjective'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_regionalobjective_created'", 'to': u"orm['auth.User']"}),
            'fma_names': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'impact': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_regionalobjective_modified'", 'to': u"orm['auth.User']"}),
            'objectives': ('django.db.models.fields.TextField', [], {}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Region']"})
        },
        u'prescription.shire': {
            'Meta': {'ordering': "[u'name']", 'unique_together': "((u'name', u'district'),)", 'object_name': 'Shire'},
            'district': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.District']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'prescription.tenure': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'Tenure'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'prescription.vegetationtype': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'VegetationType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'stakeholder.criticalstakeholder': {
            'Meta': {'ordering': "[u'id']", 'object_name': 'CriticalStakeholder'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'stakeholder_criticalstakeholder_created'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interest': ('django.db.models.fields.TextField', [], {}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'stakeholder_criticalstakeholder_modified'", 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '320'}),
            'organisation': ('django.db.models.fields.CharField', [], {'max_length': '320'}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"})
        },
        u'stakeholder.publiccontact': {
            'Meta': {'object_name': 'PublicContact'},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'stakeholder_publiccontact_created'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'stakeholder_publiccontact_modified'", 'to': u"orm['auth.User']"}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"}),
            'stakeholder': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['stakeholder.Stakeholder']"})
        },
        u'stakeholder.stakeholder': {
            'Meta': {'object_name': 'Stakeholder'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '320', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'stakeholder_stakeholder_created'", 'to': u"orm['auth.User']"}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '320', 'blank': 'True'}),
            'expired': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'stakeholder_stakeholder_modified'", 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '320'}),
            'organisation': ('django.db.models.fields.CharField', [], {'max_length': '320'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '320', 'blank': 'True'})
        }
    }

    complete_apps = ['implementation']
