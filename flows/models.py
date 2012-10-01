# -*- coding: UTF-8 -*-

# Note: this is mainly required because using the Django test runner
# requires that apps under test have a 'models' module, even if it's
# just empty.


from flows import config
if config.FLOWS_STATE_STORE == 'flows.statestore.django_store':
    from flows.statestore.django_store import StateModel #@UnusedImport only used to registed with django ORM