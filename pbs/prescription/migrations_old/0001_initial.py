# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Season'
        db.create_table(u'prescription_season', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_season_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_season_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=3)),
            ('start', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal(u'prescription', ['Season'])

        # Adding model 'Region'
        db.create_table(u'prescription_region', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
        ))
        db.send_create_signal(u'prescription', ['Region'])

        # Adding model 'District'
        db.create_table(u'prescription_district', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Region'])),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=3)),
        ))
        db.send_create_signal(u'prescription', ['District'])

        # Adding model 'Shire'
        db.create_table(u'prescription_shire', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('district', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.District'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'prescription', ['Shire'])

        # Adding unique constraint on 'Shire', fields ['name', 'district']
        db.create_unique(u'prescription_shire', ['name', 'district_id'])

        # Adding model 'VegetationType'
        db.create_table(u'prescription_vegetationtype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'prescription', ['VegetationType'])

        # Adding model 'Tenure'
        db.create_table(u'prescription_tenure', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'prescription', ['Tenure'])

        # Adding model 'Purpose'
        db.create_table(u'prescription_purpose', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'prescription', ['Purpose'])

        # Adding model 'ForecastArea'
        db.create_table(u'prescription_forecastarea', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'prescription', ['ForecastArea'])

        # Adding M2M table for field districts on 'ForecastArea'
        db.create_table(u'prescription_forecastarea_districts', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('forecastarea', models.ForeignKey(orm[u'prescription.forecastarea'], null=False)),
            ('district', models.ForeignKey(orm[u'prescription.district'], null=False))
        ))
        db.create_unique(u'prescription_forecastarea_districts', ['forecastarea_id', 'district_id'])

        # Adding model 'EndorsingRole'
        db.create_table(u'prescription_endorsingrole', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=320)),
            ('disclaimer', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'prescription', ['EndorsingRole'])

        # Adding model 'Prescription'
        db.create_table(u'prescription_prescription', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_prescription_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_prescription_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('burn_id', self.gf('django.db.models.fields.CharField')(max_length=7)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Region'])),
            ('district', self.gf('smart_selects.db_fields.ChainedForeignKey')(to=orm['prescription.District'], null=True, blank=True)),
            ('planned_year', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=4)),
            ('planned_season', self.gf('django.db.models.fields.PositiveSmallIntegerField')(max_length=64)),
            ('last_year', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=4, null=True, blank=True)),
            ('last_season', self.gf('django.db.models.fields.PositiveSmallIntegerField')(max_length=64, null=True, blank=True)),
            ('last_season_unknown', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('last_year_unknown', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('contentious', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('contentious_rationale', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('aircraft_burn', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('allocation', self.gf('django.db.models.fields.PositiveSmallIntegerField')(max_length=64, null=True, blank=True)),
            ('priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            ('rationale', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('remote_sensing_priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=4)),
            ('treatment_percentage', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=u'320', null=True, blank=True)),
            ('area', self.gf('django.db.models.fields.DecimalField')(default=0.0, max_digits=12, decimal_places=1)),
            ('perimeter', self.gf('django.db.models.fields.DecimalField')(default=0.0, max_digits=12, decimal_places=1)),
            ('bushfire_act_zone', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('prohibited_period', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('prescribing_officer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('short_code', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('planning_status', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('planning_status_modified', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('endorsing_roles_determined', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('endorsement_status', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('endorsement_status_modified', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('approval_status', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('approval_status_modified', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('ignition_status', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('ignition_status_modified', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('status', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('status_modified', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('biodiversity_text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('biodiversity_text_additional', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('bushfire_risk_text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('vegetation_text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('ignition_completed_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('forest_blocks', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'prescription', ['Prescription'])

        # Adding M2M table for field shires on 'Prescription'
        db.create_table(u'prescription_prescription_shires', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('prescription', models.ForeignKey(orm[u'prescription.prescription'], null=False)),
            ('shire', models.ForeignKey(orm[u'prescription.shire'], null=False))
        ))
        db.create_unique(u'prescription_prescription_shires', ['prescription_id', 'shire_id'])

        # Adding M2M table for field regional_objectives on 'Prescription'
        db.create_table(u'prescription_prescription_regional_objectives', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('prescription', models.ForeignKey(orm[u'prescription.prescription'], null=False)),
            ('regionalobjective', models.ForeignKey(orm[u'prescription.regionalobjective'], null=False))
        ))
        db.create_unique(u'prescription_prescription_regional_objectives', ['prescription_id', 'regionalobjective_id'])

        # Adding M2M table for field vegetation_types on 'Prescription'
        db.create_table(u'prescription_prescription_vegetation_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('prescription', models.ForeignKey(orm[u'prescription.prescription'], null=False)),
            ('vegetationtype', models.ForeignKey(orm[u'prescription.vegetationtype'], null=False))
        ))
        db.create_unique(u'prescription_prescription_vegetation_types', ['prescription_id', 'vegetationtype_id'])

        # Adding M2M table for field tenures on 'Prescription'
        db.create_table(u'prescription_prescription_tenures', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('prescription', models.ForeignKey(orm[u'prescription.prescription'], null=False)),
            ('tenure', models.ForeignKey(orm[u'prescription.tenure'], null=False))
        ))
        db.create_unique(u'prescription_prescription_tenures', ['prescription_id', 'tenure_id'])

        # Adding M2M table for field forecast_areas on 'Prescription'
        db.create_table(u'prescription_prescription_forecast_areas', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('prescription', models.ForeignKey(orm[u'prescription.prescription'], null=False)),
            ('forecastarea', models.ForeignKey(orm[u'prescription.forecastarea'], null=False))
        ))
        db.create_unique(u'prescription_prescription_forecast_areas', ['prescription_id', 'forecastarea_id'])

        # Adding M2M table for field purposes on 'Prescription'
        db.create_table(u'prescription_prescription_purposes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('prescription', models.ForeignKey(orm[u'prescription.prescription'], null=False)),
            ('purpose', models.ForeignKey(orm[u'prescription.purpose'], null=False))
        ))
        db.create_unique(u'prescription_prescription_purposes', ['prescription_id', 'purpose_id'])

        # Adding M2M table for field endorsing_roles on 'Prescription'
        db.create_table(u'prescription_prescription_endorsing_roles', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('prescription', models.ForeignKey(orm[u'prescription.prescription'], null=False)),
            ('endorsingrole', models.ForeignKey(orm[u'prescription.endorsingrole'], null=False))
        ))
        db.create_unique(u'prescription_prescription_endorsing_roles', ['prescription_id', 'endorsingrole_id'])

        # Adding model 'PriorityJustification'
        db.create_table(u'prescription_priorityjustification', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_priorityjustification_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_priorityjustification_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'], null=True)),
            ('purpose', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Purpose'])),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            ('criteria', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('rationale', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            ('relevant', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'prescription', ['PriorityJustification'])

        # Adding unique constraint on 'PriorityJustification', fields ['purpose', 'prescription']
        db.create_unique(u'prescription_priorityjustification', ['purpose_id', 'prescription_id'])

        # Adding model 'RegionalObjective'
        db.create_table(u'prescription_regionalobjective', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_regionalobjective_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_regionalobjective_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Region'])),
            ('impact', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('fma_names', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('objectives', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'prescription', ['RegionalObjective'])

        # Adding model 'Objective'
        db.create_table(u'prescription_objective', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_objective_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_objective_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('objectives', self.gf('django.db.models.fields.TextField')()),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
        ))
        db.send_create_signal(u'prescription', ['Objective'])

        # Adding model 'SuccessCriteria'
        db.create_table(u'prescription_successcriteria', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_successcriteria_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_successcriteria_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('criteria', self.gf('django.db.models.fields.TextField')()),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
        ))
        db.send_create_signal(u'prescription', ['SuccessCriteria'])

        # Adding M2M table for field objectives on 'SuccessCriteria'
        db.create_table(u'prescription_successcriteria_objectives', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('successcriteria', models.ForeignKey(orm[u'prescription.successcriteria'], null=False)),
            ('objective', models.ForeignKey(orm[u'prescription.objective'], null=False))
        ))
        db.create_unique(u'prescription_successcriteria_objectives', ['successcriteria_id', 'objective_id'])

        # Adding model 'SMEAC'
        db.create_table(u'prescription_smeac', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'prescription', ['SMEAC'])

        # Adding model 'DefaultBriefingChecklist'
        db.create_table(u'prescription_defaultbriefingchecklist', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('smeac', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.SMEAC'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'prescription', ['DefaultBriefingChecklist'])

        # Adding model 'BriefingChecklist'
        db.create_table(u'prescription_briefingchecklist', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_briefingchecklist_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_briefingchecklist_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
            ('smeac', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.SMEAC'])),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'prescription', ['BriefingChecklist'])

        # Adding model 'Endorsement'
        db.create_table(u'prescription_endorsement', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_endorsement_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_endorsement_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.EndorsingRole'])),
            ('endorsed', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal(u'prescription', ['Endorsement'])

        # Adding model 'Approval'
        db.create_table(u'prescription_approval', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_approval_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'prescription_approval_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
            ('initial_valid_to', self.gf('django.db.models.fields.DateField')(default=datetime.datetime.now)),
            ('valid_to', self.gf('django.db.models.fields.DateField')(default=datetime.datetime.now)),
            ('extension_count', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
        ))
        db.send_create_signal(u'prescription', ['Approval'])


    def backwards(self, orm):
        # Removing unique constraint on 'PriorityJustification', fields ['purpose', 'prescription']
        db.delete_unique(u'prescription_priorityjustification', ['purpose_id', 'prescription_id'])

        # Removing unique constraint on 'Shire', fields ['name', 'district']
        db.delete_unique(u'prescription_shire', ['name', 'district_id'])

        # Deleting model 'Season'
        db.delete_table(u'prescription_season')

        # Deleting model 'Region'
        db.delete_table(u'prescription_region')

        # Deleting model 'District'
        db.delete_table(u'prescription_district')

        # Deleting model 'Shire'
        db.delete_table(u'prescription_shire')

        # Deleting model 'VegetationType'
        db.delete_table(u'prescription_vegetationtype')

        # Deleting model 'Tenure'
        db.delete_table(u'prescription_tenure')

        # Deleting model 'Purpose'
        db.delete_table(u'prescription_purpose')

        # Deleting model 'ForecastArea'
        db.delete_table(u'prescription_forecastarea')

        # Removing M2M table for field districts on 'ForecastArea'
        db.delete_table('prescription_forecastarea_districts')

        # Deleting model 'EndorsingRole'
        db.delete_table(u'prescription_endorsingrole')

        # Deleting model 'Prescription'
        db.delete_table(u'prescription_prescription')

        # Removing M2M table for field shires on 'Prescription'
        db.delete_table('prescription_prescription_shires')

        # Removing M2M table for field regional_objectives on 'Prescription'
        db.delete_table('prescription_prescription_regional_objectives')

        # Removing M2M table for field vegetation_types on 'Prescription'
        db.delete_table('prescription_prescription_vegetation_types')

        # Removing M2M table for field tenures on 'Prescription'
        db.delete_table('prescription_prescription_tenures')

        # Removing M2M table for field forecast_areas on 'Prescription'
        db.delete_table('prescription_prescription_forecast_areas')

        # Removing M2M table for field purposes on 'Prescription'
        db.delete_table('prescription_prescription_purposes')

        # Removing M2M table for field endorsing_roles on 'Prescription'
        db.delete_table('prescription_prescription_endorsing_roles')

        # Removing M2M table for field critical_stakeholders on 'Prescription'
        db.delete_table('prescription_prescription_critical_stakeholders')

        # Deleting model 'PriorityJustification'
        db.delete_table(u'prescription_priorityjustification')

        # Deleting model 'RegionalObjective'
        db.delete_table(u'prescription_regionalobjective')

        # Deleting model 'Objective'
        db.delete_table(u'prescription_objective')

        # Deleting model 'SuccessCriteria'
        db.delete_table(u'prescription_successcriteria')

        # Removing M2M table for field objectives on 'SuccessCriteria'
        db.delete_table('prescription_successcriteria_objectives')

        # Deleting model 'SMEAC'
        db.delete_table(u'prescription_smeac')

        # Deleting model 'DefaultBriefingChecklist'
        db.delete_table(u'prescription_defaultbriefingchecklist')

        # Deleting model 'BriefingChecklist'
        db.delete_table(u'prescription_briefingchecklist')

        # Deleting model 'Endorsement'
        db.delete_table(u'prescription_endorsement')

        # Deleting model 'Approval'
        db.delete_table(u'prescription_approval')


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
        u'prescription.approval': {
            'Meta': {'ordering': "[u'-id']", 'object_name': 'Approval'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_approval_created'", 'to': u"orm['auth.User']"}),
            'extension_count': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_valid_to': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_approval_modified'", 'to': u"orm['auth.User']"}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"}),
            'valid_to': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'})
        },
        u'prescription.briefingchecklist': {
            'Meta': {'ordering': "[u'smeac__id', u'id']", 'object_name': 'BriefingChecklist'},
            'action': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['risk.Action']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_briefingchecklist_created'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_briefingchecklist_modified'", 'to': u"orm['auth.User']"}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"}),
            'smeac': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.SMEAC']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'prescription.defaultbriefingchecklist': {
            'Meta': {'object_name': 'DefaultBriefingChecklist'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'smeac': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.SMEAC']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'prescription.district': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'District'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Region']"})
        },
        u'prescription.endorsement': {
            'Meta': {'object_name': 'Endorsement'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_endorsement_created'", 'to': u"orm['auth.User']"}),
            'endorsed': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_endorsement_modified'", 'to': u"orm['auth.User']"}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.EndorsingRole']"})
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
        u'prescription.objective': {
            'Meta': {'ordering': "[u'created']", 'object_name': 'Objective'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_objective_created'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_objective_modified'", 'to': u"orm['auth.User']"}),
            'objectives': ('django.db.models.fields.TextField', [], {}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"})
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
        u'prescription.priorityjustification': {
            'Meta': {'ordering': "[u'order']", 'unique_together': "((u'purpose', u'prescription'),)", 'object_name': 'PriorityJustification'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_priorityjustification_created'", 'to': u"orm['auth.User']"}),
            'criteria': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_priorityjustification_modified'", 'to': u"orm['auth.User']"}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']", 'null': 'True'}),
            'priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'purpose': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Purpose']"}),
            'rationale': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'relevant': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
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
        u'prescription.season': {
            'Meta': {'ordering': "[u'-start']", 'object_name': 'Season'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_season_created'", 'to': u"orm['auth.User']"}),
            'end': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_season_modified'", 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        u'prescription.shire': {
            'Meta': {'ordering': "[u'name']", 'unique_together': "((u'name', u'district'),)", 'object_name': 'Shire'},
            'district': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.District']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'prescription.smeac': {
            'Meta': {'object_name': 'SMEAC'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'prescription.successcriteria': {
            'Meta': {'ordering': "[u'created']", 'object_name': 'SuccessCriteria'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_successcriteria_created'", 'to': u"orm['auth.User']"}),
            'criteria': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'prescription_successcriteria_modified'", 'to': u"orm['auth.User']"}),
            'objectives': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['prescription.Objective']", 'symmetrical': 'False'}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"})
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
        u'risk.action': {
            'Meta': {'ordering': "[u'risk__category', u'-relevant', u'risk__name', u'pk']", 'object_name': 'Action'},
            'context_statement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_action_created'", 'to': u"orm['auth.User']"}),
            'day_of_burn': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'day_of_burn_administration': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'day_of_burn_command': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'day_of_burn_completed': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'day_of_burn_completer': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'day_of_burn_execution': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'day_of_burn_include': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'day_of_burn_mission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'day_of_burn_situation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'details': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_action_modified'", 'to': u"orm['auth.User']"}),
            'post_burn': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'post_burn_completed': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'post_burn_completer': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'pre_burn': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pre_burn_completed': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'pre_burn_completer': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'pre_burn_explanation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'pre_burn_resolved': ('django.db.models.fields.CharField', [], {'default': "u'No'", 'max_length': '200', 'blank': 'True'}),
            'relevant': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'risk': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['risk.Risk']"}),
            'total': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'})
        },
        u'risk.risk': {
            'Meta': {'ordering': "[u'category', u'name']", 'object_name': 'Risk'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['risk.RiskCategory']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_risk_created'", 'to': u"orm['auth.User']"}),
            'custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_risk_modified'", 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']", 'null': 'True', 'blank': 'True'}),
            'risk': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'})
        },
        u'risk.riskcategory': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'RiskCategory'},
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

    complete_apps = ['prescription']
