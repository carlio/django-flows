
import unittest
from flows.preconditions import RequiredState
from flows.tests.utils import MockFlow

class RequiredStateTest(unittest.TestCase):
    
    def test_all_state_present(self):
        
        check = RequiredState('thing', 'blah')
        
        flow = MockFlow()
        flow.state = {'thing': 1, 'blah': 'cake'}
        
        self.assertTrue(check.process(flow)) 