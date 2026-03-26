# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ("implementation", "0001_initial"),
    )

    def forwards(self, orm):
        # Adding model 'SummaryCompletionState'
        db.create_table(u'report_summarycompletionstate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_summarycompletionstate_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_summarycompletionstate_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.OneToOneField')(related_name=u'pre_state', unique=True, to=orm['prescription.Prescription'])),
            ('summary', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('context_statement', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('context_map', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('objectives', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('success_criteria', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('priority_justification', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('complexity_analysis', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('risk_register', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'report', ['SummaryCompletionState'])

        # Adding model 'BurnImplementationState'
        db.create_table(u'report_burnimplementationstate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_burnimplementationstate_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_burnimplementationstate_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.OneToOneField')(related_name=u'day_state', unique=True, to=orm['prescription.Prescription'])),
            ('pre_actions', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('actions', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('roads', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('traffic', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('tracks', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('burning_prescription', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('edging_plan', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('contingency_plan', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('lighting_sequence', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('exclusion_areas', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('organisational_structure', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('briefing', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('operation_maps', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('aerial_maps', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
        ))
        db.send_create_signal(u'report', ['BurnImplementationState'])

        # Adding model 'PostBurnChecklist'
        db.create_table(u'report_postburnchecklist', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_postburnchecklist_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_postburnchecklist_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'], null=True, blank=True)),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=320)),
            ('relevant', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('completed_on', self.gf('django.db.models.fields.DateField')(default=datetime.datetime.now, null=True, blank=True)),
            ('completed_by', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'report', ['PostBurnChecklist'])

        # Adding model 'BurnClosureState'
        db.create_table(u'report_burnclosurestate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_burnclosurestate_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_burnclosurestate_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.OneToOneField')(related_name=u'post_state', unique=True, to=orm['prescription.Prescription'])),
            ('post_actions', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('evaluation_summary', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('evaluation', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('post_ignitions', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('aerial_intensity', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('satellite_intensity', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('other', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
            ('post_burn_checklist', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('closure_declaration', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('signage', self.gf('django.db.models.fields.NullBooleanField')(default=False, null=True, blank=True)),
        ))
        db.send_create_signal(u'report', ['BurnClosureState'])

        # Adding model 'AreaAchievement'
        db.create_table(u'report_areaachievement', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_areaachievement_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_areaachievement_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
            ('ignition', self.gf('django.db.models.fields.DateField')(default=datetime.datetime(2013, 9, 3, 0, 0))),
            ('area_treated', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=12, decimal_places=1)),
            ('area_estimate', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=12, decimal_places=1)),
            ('edging_length', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=12, decimal_places=1)),
            ('edging_depth_estimate', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=12, decimal_places=1)),
            ('dpaw_fire_no', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('dfes_fire_no', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('date_escaped', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'report', ['AreaAchievement'])

        # Adding M2M table for field ignition_types on 'AreaAchievement'
        db.create_table(u'report_areaachievement_ignition_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('areaachievement', models.ForeignKey(orm[u'report.areaachievement'], null=False)),
            ('ignitiontype', models.ForeignKey(orm[u'implementation.ignitiontype'], null=False))
        ))
        db.create_unique(u'report_areaachievement_ignition_types', ['areaachievement_id', 'ignitiontype_id'])

        # Adding model 'Evaluation'
        db.create_table(u'report_evaluation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_evaluation_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_evaluation_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('criteria', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['prescription.SuccessCriteria'], unique=True)),
            ('achieved', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('summary', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'report', ['Evaluation'])

        # Adding model 'ProposedAction'
        db.create_table(u'report_proposedaction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_proposedaction_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_proposedaction_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
            ('observations', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('action', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'report', ['ProposedAction'])

        # Adding model 'ClosureDeclaration'
        db.create_table(u'report_closuredeclaration', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_closuredeclaration_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'report_closuredeclaration_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['prescription.Prescription'], unique=True)),
            ('closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'report', ['ClosureDeclaration'])


    def backwards(self, orm):
        # Deleting model 'SummaryCompletionState'
        db.delete_table(u'report_summarycompletionstate')

        # Deleting model 'BurnImplementationState'
        db.delete_table(u'report_burnimplementationstate')

        # Deleting model 'PostBurnChecklist'
        db.delete_table(u'report_postburnchecklist')

        # Deleting model 'BurnClosureState'
        db.delete_table(u'report_burnclosurestate')

        # Deleting model 'AreaAchievement'
        db.delete_table(u'report_areaachievement')

        # Removing M2M table for field ignition_types on 'AreaAchievement'
        db.delete_table('report_areaachievement_ignition_types')

        # Deleting model 'Evaluation'
        db.delete_table(u'report_evaluation')

        # Deleting model 'ProposedAction'
        db.delete_table(u'report_proposedaction')

        # Deleting model 'ClosureDeclaration'
        db.delete_table(u'report_closuredeclaration')


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
        u'implementation.ignitiontype': {
            'Meta': {'object_name': 'IgnitionType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
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
        u'report.areaachievement': {
            'Meta': {'ordering': "[u'-ignition']", 'object_name': 'AreaAchievement'},
            'area_estimate': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '1'}),
            'area_treated': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '1'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_areaachievement_created'", 'to': u"orm['auth.User']"}),
            'date_escaped': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'dfes_fire_no': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'dpaw_fire_no': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'edging_depth_estimate': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '1'}),
            'edging_length': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '12', 'decimal_places': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignition': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 9, 3, 0, 0)'}),
            'ignition_types': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['implementation.IgnitionType']", 'symmetrical': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_areaachievement_modified'", 'to': u"orm['auth.User']"}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"})
        },
        u'report.burnclosurestate': {
            'Meta': {'object_name': 'BurnClosureState'},
            'aerial_intensity': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'closure_declaration': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_burnclosurestate_created'", 'to': u"orm['auth.User']"}),
            'evaluation': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'evaluation_summary': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_burnclosurestate_modified'", 'to': u"orm['auth.User']"}),
            'other': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'post_actions': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'post_burn_checklist': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'post_ignitions': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'prescription': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "u'post_state'", 'unique': 'True', 'to': u"orm['prescription.Prescription']"}),
            'satellite_intensity': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'signage': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
        },
        u'report.burnimplementationstate': {
            'Meta': {'object_name': 'BurnImplementationState'},
            'actions': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'aerial_maps': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'briefing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'burning_prescription': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'contingency_plan': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_burnimplementationstate_created'", 'to': u"orm['auth.User']"}),
            'edging_plan': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'exclusion_areas': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lighting_sequence': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_burnimplementationstate_modified'", 'to': u"orm['auth.User']"}),
            'operation_maps': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'organisational_structure': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pre_actions': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'prescription': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "u'day_state'", 'unique': 'True', 'to': u"orm['prescription.Prescription']"}),
            'roads': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'tracks': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            'traffic': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
        },
        u'report.closuredeclaration': {
            'Meta': {'object_name': 'ClosureDeclaration'},
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_closuredeclaration_created'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_closuredeclaration_modified'", 'to': u"orm['auth.User']"}),
            'prescription': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['prescription.Prescription']", 'unique': 'True'})
        },
        u'report.evaluation': {
            'Meta': {'object_name': 'Evaluation'},
            'achieved': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_evaluation_created'", 'to': u"orm['auth.User']"}),
            'criteria': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['prescription.SuccessCriteria']", 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_evaluation_modified'", 'to': u"orm['auth.User']"}),
            'summary': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        u'report.postburnchecklist': {
            'Meta': {'ordering': "[u'pk']", 'object_name': 'PostBurnChecklist'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '320'}),
            'completed_by': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'completed_on': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_postburnchecklist_created'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_postburnchecklist_modified'", 'to': u"orm['auth.User']"}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']", 'null': 'True', 'blank': 'True'}),
            'relevant': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'report.proposedaction': {
            'Meta': {'object_name': 'ProposedAction'},
            'action': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_proposedaction_created'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_proposedaction_modified'", 'to': u"orm['auth.User']"}),
            'observations': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"})
        },
        u'report.summarycompletionstate': {
            'Meta': {'object_name': 'SummaryCompletionState'},
            'complexity_analysis': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'context_map': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'context_statement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_summarycompletionstate_created'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'report_summarycompletionstate_modified'", 'to': u"orm['auth.User']"}),
            'objectives': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'prescription': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "u'pre_state'", 'unique': 'True', 'to': u"orm['prescription.Prescription']"}),
            'priority_justification': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'risk_register': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'success_criteria': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'summary': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
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

    complete_apps = ['report']
