from django.core.exceptions import ImproperlyConfigured
from flows.statestore.base import StateStoreBase, StateNotFound
from flows import config

try:
    import redis
except ImportError:
    raise ImproperlyConfigured('The "redis" python client package is required to use Redis as a task state store - get it here http://pypi.python.org/pypi/redis/')


class StateStore(StateStoreBase):
    
    def _get_settings(self):
        host = config.FLOWS_REDIS_STATE_STORE_HOST
        password = config.FLOWS_REDIS_STATE_STORE_PASSWORD
        port = config.FLOWS_REDIS_STATE_STORE_PORT
        db_id = config.FLOWS_REDIS_STATE_STORE_DB

        return {'host': host, 'port': port,
                'password': password, 'db': db_id }
    
    def _get_db(self):
        return redis.Redis(**self._get_settings())
    
    def get_state(self, task_id):
        data = self._get_db().get(task_id)
        if not data:
            raise StateNotFound
        return self._deserialise(data)
    
    def put_state(self, task_id, state):
        ttl = config.FLOWS_TASK_IDLE_TIMEOUT
        data = self._serialise(state)
        self._get_db().setex(task_id, data, ttl)

    def delete_state(self, task_id):
        self._get_db().delete(task_id)