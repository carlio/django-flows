# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'StateModel.last_access'
        db.add_column('flows_statemodel', 'last_access',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime.now(), blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'StateModel.last_access'
        db.delete_column('flows_statemodel', 'last_access')


    models = {
        'flows.statemodel': {
            'Meta': {'object_name': 'StateModel'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_access': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'task_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'})
        }
    }

    complete_apps = ['flows']