
from django.test import TestCase
from flows.statestore.django_store import StateStore
from flows.statestore.tests.utils import test_store_state
    

class DjangoStateStoreTest(TestCase):
    
    def test_django_store_state(self):
        store = StateStore()
        test_store_state(self, store)
        