
from django.conf import settings

def _get_setting(name, default):
    return getattr( settings, name, default )


# General settings
FLOWS_STATE_STORE = _get_setting('FLOWS_STATE_STORE', 'flows.statestore.django_store')
FLOWS_TASK_IDLE_TIMEOUT = _get_setting('FLOWS_TASK_IDLE_TIMEOUT', 20 * 60) # 20 minutes

# Redis state store settings
FLOWS_REDIS_STATE_STORE_HOST = _get_setting( 'FLOWS_REDIS_STATE_STORE_HOST', 'localhost' )
FLOWS_REDIS_STATE_STORE_USER = _get_setting( 'FLOWS_REDIS_STATE_STORE_USER', '' )
FLOWS_REDIS_STATE_STORE_PASSWORD = _get_setting( 'FLOWS_REDIS_STATE_STORE_PASSWORD', '' )
FLOWS_REDIS_STATE_STORE_PORT = _get_setting( 'FLOWS_REDIS_STATE_STORE_PORT', 6379)
FLOWS_REDIS_STATE_STORE_DB = _get_setting( 'FLOWS_REDIS_STATE_STORE_DB', 0 )