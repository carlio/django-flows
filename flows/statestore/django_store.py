from flows.statestore.base import StateStoreBase, StateNotFound
from django.db import models
from django.utils import timezone
from flows import config
from datetime import timedelta



class StateModelManager(models.Manager):
    def get_query_set(self):
        timeout = timezone.now() - timedelta(seconds=config.FLOWS_TASK_IDLE_TIMEOUT)
        return super(StateModelManager, self).get_query_set().filter( last_access__gte=timeout )

    def remove_expired_state(self):
        timeout = config.FLOWS_TASK_IDLE_TIMEOUT
        cutoff = timezone.now() - timedelta(seconds=timeout)

        # directly call the superclass's queryset method because
        # in our own we filter out expired state!
        qs = super(StateModelManager, self).get_query_set()

        expired = qs.filter(last_access__lte=cutoff)
        count = expired.count()
        expired.delete()
        return count


class StateModel(models.Model):

    objects = StateModelManager()

    class Meta:
        app_label = 'flows'
        
    task_id = models.CharField(max_length=32, unique=True)
    state = models.TextField(null=True)

    last_access = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return 'State for task %s' % self.task_id
    

class StateStore(StateStoreBase):
    
    def get_state(self, task_id):
        try:
            state_model = StateModel.objects.get(task_id=task_id)
        except StateModel.DoesNotExist:
            raise StateNotFound
        else:
            state_model.last_access = timezone.now()
            state_model.save()
            return self._deserialise(state_model.state)
        
    def put_state(self, task_id, state):
        state_model, _ = StateModel.objects.get_or_create(task_id=task_id)
        state_model.state = self._serialise(state)
        state_model.save()
        
    def delete_state(self, task_id):
        StateModel.objects.filter(task_id=task_id).delete()