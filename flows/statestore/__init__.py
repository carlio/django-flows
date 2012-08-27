from django.utils.importlib import import_module
from django.conf import settings

def _get_state_store():
    store_module_name = getattr(settings, 'FLOW_STATE_STORE', 'flows.statestore.django_store')
    store_module = import_module(store_module_name)
    return store_module.StateStore()

state_store = _get_state_store()