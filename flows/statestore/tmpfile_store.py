from flows.statestore.base import StateStoreBase, StateNotFound
import os

class StateStore(StateStoreBase):
    
    def _get_file_name(self, task_id):
        return '/tmp/%s.task' % task_id
    
    def get_state(self, task_id):
        # TODO: use os.tempfile, i didn't have internet access when writing this initially
        # so i couldn't lookup the API
        fname = self._get_file_name(task_id)
        if not os.path.exists(fname):
            raise StateNotFound
        with open(fname) as f:
            return self._deserialise(f.read())
        
    def put_state(self, task_id, state):
        with open(self._get_file_name(task_id), 'w') as f:
            f.write(self._serialise(state)) 
        
    def delete_state(self, task_id):
        os.remove(self._get_file_name(task_id))
