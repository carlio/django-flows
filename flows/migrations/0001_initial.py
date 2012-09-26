# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StateModel'
        db.create_table('flows_statemodel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
            ('state', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('flows', ['StateModel'])


    def backwards(self, orm):
        # Deleting model 'StateModel'
        db.delete_table('flows_statemodel')


    models = {
        'flows.statemodel': {
            'Meta': {'object_name': 'StateModel'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'state': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'task_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'})
        }
    }

    complete_apps = ['flows']