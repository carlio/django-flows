
import unittest
from flows.statestore.django_store import StateStore
from flows.statestore.tests.utils import store_state_works
    

class DjangoStateStoreTest(unittest.TestCase):
    
    def test_django_store_state(self):
        store = StateStore()
        store_state_works(self, store)
