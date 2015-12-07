
import unittest
from flows.components import Action, Scaffold


class Action1(Action):
    url = '/1$'


class Action2(Action):
    url = '/2$'


class Scaffold1(Scaffold):
    url = '/scaff1'
    action_set = [Action1, 'Action2']


class LazyActionSetTest(unittest.TestCase):
    
    def test_get_by_name(self):
        a1, a2 = Scaffold1().action_set
        self.assertEqual( Action1, a1 )
        self.assertEqual( Action2, a2 )
    
    def test_index_of(self):
        actions = Scaffold1().action_set
        self.assertEqual( 0, actions.index(Action1) )
        self.assertEqual( 1, actions.index(Action2) )
