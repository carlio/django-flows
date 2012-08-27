from django.utils.importlib import import_module
from flows import config


def _get_state_store():
    store_module_name = config.FLOWS_STATE_STORE
    store_module = import_module(store_module_name)
    return store_module.StateStore()

state_store = _get_state_store()