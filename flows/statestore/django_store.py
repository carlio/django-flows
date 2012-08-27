from flows.statestore.base import StateStoreBase, StateNotFound
from django.db import models


class StateModel(models.Model):
    
    class Meta:
        app_label = 'flows'
        
    task_id = models.CharField(max_length=32, unique=True)
    state = models.TextField(null=True)
    
    def __unicode__(self):
        return 'State for task %s' % self.task_id
    

class StateStore(StateStoreBase):
    
    def get_state(self, task_id):
        try:
            state_model = StateModel.objects.get(task_id=task_id)
        except StateModel.DoesNotExist:
            raise StateNotFound
        else:
            return self._deserialise(state_model.state)
        
    def put_state(self, task_id, state):
        state_model, _ = StateModel.objects.get_or_create(task_id=task_id)
        state_model.state = self._serialise(state)
        state_model.save()