

class StateStoreBase(object):
    
    def get_state(self, task_id):
        raise NotImplementedError
    
    def put_state(self, task_id):
        raise NotImplementedError