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
        # Adding model 'RiskCategory'
        db.create_table(u'risk_riskcategory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'risk', ['RiskCategory'])

        # Adding model 'Risk'
        db.create_table(u'risk_risk', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_risk_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_risk_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['risk.RiskCategory'])),
            ('risk', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('custom', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'risk', ['Risk'])

        # Adding model 'ContextCategory'
        db.create_table(u'risk_contextcategory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal(u'risk', ['ContextCategory'])

        # Adding model 'Context'
        db.create_table(u'risk_context', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_context_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_context_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
            ('statement', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'risk', ['Context'])

        # Adding M2M table for field categories on 'Context'
        db.create_table(u'risk_context_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('context', models.ForeignKey(orm[u'risk.context'], null=False)),
            ('contextcategory', models.ForeignKey(orm[u'risk.contextcategory'], null=False))
        ))
        db.create_unique(u'risk_context_categories', ['context_id', 'contextcategory_id'])

        # Adding model 'Action'
        db.create_table(u'risk_action', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_action_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_action_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('risk', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['risk.Risk'])),
            ('relevant', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('pre_burn', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('details', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('pre_burn_resolved', self.gf('django.db.models.fields.CharField')(default=u'No', max_length=200, blank=True)),
            ('pre_burn_completer', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('pre_burn_completed', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('pre_burn_explanation', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('day_of_burn', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('day_of_burn_completer', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('day_of_burn_completed', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('day_of_burn_include', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('day_of_burn_situation', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('day_of_burn_mission', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('day_of_burn_execution', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('day_of_burn_administration', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('day_of_burn_command', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('post_burn', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('post_burn_completer', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('post_burn_completed', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('context_statement', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('index', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('total', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
        ))
        db.send_create_signal(u'risk', ['Action'])

        # Adding model 'ContextRelevantAction'
        db.create_table(u'risk_contextrelevantaction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_contextrelevantaction_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_contextrelevantaction_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('action', self.gf('django.db.models.fields.related.OneToOneField')(related_name=u'context_considered', unique=True, to=orm['risk.Action'])),
            ('considered', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'risk', ['ContextRelevantAction'])

        # Adding model 'Register'
        db.create_table(u'risk_register', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_register_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_register_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('draft_consequence', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=6, blank=True)),
            ('draft_likelihood', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=5, blank=True)),
            ('draft_risk_level', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=5)),
            ('alarp', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('final_consequence', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=3, blank=True)),
            ('final_likelihood', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=5, blank=True)),
            ('final_risk_level', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=5)),
        ))
        db.send_create_signal(u'risk', ['Register'])

        # Adding model 'TreatmentLocation'
        db.create_table(u'risk_treatmentlocation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'risk', ['TreatmentLocation'])

        # Adding model 'Treatment'
        db.create_table(u'risk_treatment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_treatment_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_treatment_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('register', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['risk.Register'])),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['risk.TreatmentLocation'])),
            ('complete', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'risk', ['Treatment'])

        # Adding model 'Contingency'
        db.create_table(u'risk_contingency', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_contingency_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_contingency_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'])),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('trigger', self.gf('django.db.models.fields.TextField')()),
            ('action', self.gf('django.db.models.fields.TextField')()),
            ('notify_name', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('location', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('organisation', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('contact_number', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'risk', ['Contingency'])

        # Adding model 'Complexity'
        db.create_table(u'risk_complexity', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_complexity_created', to=orm['auth.User'])),
            ('modifier', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'risk_complexity_modified', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('prescription', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['prescription.Prescription'], null=True, blank=True)),
            ('factor', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('sub_factor', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            ('rating', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            ('rationale', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'risk', ['Complexity'])


    def backwards(self, orm):
        # Deleting model 'RiskCategory'
        db.delete_table(u'risk_riskcategory')

        # Deleting model 'Risk'
        db.delete_table(u'risk_risk')

        # Deleting model 'ContextCategory'
        db.delete_table(u'risk_contextcategory')

        # Deleting model 'Context'
        db.delete_table(u'risk_context')

        # Removing M2M table for field categories on 'Context'
        db.delete_table('risk_context_categories')

        # Deleting model 'Action'
        db.delete_table(u'risk_action')

        # Deleting model 'ContextRelevantAction'
        db.delete_table(u'risk_contextrelevantaction')

        # Deleting model 'Register'
        db.delete_table(u'risk_register')

        # Deleting model 'TreatmentLocation'
        db.delete_table(u'risk_treatmentlocation')

        # Deleting model 'Treatment'
        db.delete_table(u'risk_treatment')

        # Deleting model 'Contingency'
        db.delete_table(u'risk_contingency')

        # Deleting model 'Complexity'
        db.delete_table(u'risk_complexity')


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
        u'risk.complexity': {
            'Meta': {'ordering': "[u'order']", 'object_name': 'Complexity'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_complexity_created'", 'to': u"orm['auth.User']"}),
            'factor': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_complexity_modified'", 'to': u"orm['auth.User']"}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']", 'null': 'True', 'blank': 'True'}),
            'rating': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'rationale': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sub_factor': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'risk.context': {
            'Meta': {'ordering': "[u'pk']", 'object_name': 'Context'},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['risk.ContextCategory']", 'symmetrical': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_context_created'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_context_modified'", 'to': u"orm['auth.User']"}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"}),
            'statement': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        u'risk.contextcategory': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'ContextCategory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        u'risk.contextrelevantaction': {
            'Meta': {'object_name': 'ContextRelevantAction'},
            'action': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "u'context_considered'", 'unique': 'True', 'to': u"orm['risk.Action']"}),
            'considered': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_contextrelevantaction_created'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_contextrelevantaction_modified'", 'to': u"orm['auth.User']"})
        },
        u'risk.contingency': {
            'Meta': {'ordering': "[u'id']", 'object_name': 'Contingency'},
            'action': ('django.db.models.fields.TextField', [], {}),
            'contact_number': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_contingency_created'", 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_contingency_modified'", 'to': u"orm['auth.User']"}),
            'notify_name': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'organisation': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"}),
            'trigger': ('django.db.models.fields.TextField', [], {})
        },
        u'risk.register': {
            'Meta': {'ordering': "(u'pk',)", 'object_name': 'Register'},
            'alarp': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_register_created'", 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'draft_consequence': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '6', 'blank': 'True'}),
            'draft_likelihood': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '5', 'blank': 'True'}),
            'draft_risk_level': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '5'}),
            'final_consequence': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3', 'blank': 'True'}),
            'final_likelihood': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '5', 'blank': 'True'}),
            'final_risk_level': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '5'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_register_modified'", 'to': u"orm['auth.User']"}),
            'prescription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['prescription.Prescription']"})
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
        u'risk.treatment': {
            'Meta': {'object_name': 'Treatment'},
            'complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_treatment_created'", 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['risk.TreatmentLocation']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modifier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'risk_treatment_modified'", 'to': u"orm['auth.User']"}),
            'register': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['risk.Register']"})
        },
        u'risk.treatmentlocation': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'TreatmentLocation'},
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

    complete_apps = ['risk']
