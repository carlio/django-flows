
import pickle
import base64

class StateNotFound(Exception):
    pass

class StateStoreBase(object):
    
    def _serialise(self, state):
        data = pickle.dumps(state)
        return base64.b64encode(data)
    
    def _deserialise(self, data):
        return pickle.loads(base64.b64decode(data))
    
    def get_state(self, task_id):
        raise NotImplementedError
    
    def put_state(self, task_id, state):
        raise NotImplementedError
    
    def delete_state(self, task_id):
        raise NotImplementedError