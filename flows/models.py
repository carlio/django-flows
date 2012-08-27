
# Note: this is mainly required because using the Django test runner
# requires that apps under test have a 'models' module, even if it's
# just empty.

# TODO: make this dependent on the state store setting
from flows.statestore.django_store import StateModel #@UnusedImport only used to registed with django ORM