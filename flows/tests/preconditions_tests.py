
import unittest
from flows.preconditions import RequiredState
from flows.tests.utils import MockFlow
from django.http import HttpResponse

class RequiredStateTest(unittest.TestCase):
    
    def test_all_state_present(self):
        
        check = RequiredState('thing', 'blah')
        
        flow = MockFlow()
        flow.state = {'thing': 1, 'blah': 'cake'}
        
        self.assertTrue(check.process(flow) is None) 
        
    def test_missing_state(self):
        
        check = RequiredState('thing', 'blah')
        
        flow = MockFlow()
        flow.state = {'thing': 1}
        
        response = check.process(flow)
        
        # ensure that we do something with the request rather than
        # just let it pass through
        self.assertTrue( isinstance(response, HttpResponse) )
        