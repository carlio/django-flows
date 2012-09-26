#
#import unittest
#from flows.components import Scaffold, Action
#from flows.transitions import Linear
#
#
##            ScaffoldRoot
##           /     |      \
## ActionRoot1     |      ActionRoot2
##                 |
##            ScaffoldMiddle
##             /         \
##     ActionMiddle1    ActionMiddle2
#
#
#class ScaffoldRoot(Scaffold):
#    parent = None
#    action_set = ["ActionRoot1", "ScaffoldMiddle", "ActionRoot2"]
#
#class ActionRoot1(Action):
#    scaffold = ScaffoldRoot() # this would normally be set automatically by the handler, but is mocked for this test
#
#class ActionRoot2(Action):
#    scaffold = ScaffoldRoot() # this would normally be set automatically by the handler, but is mocked for this test
#    state = {'_on_complete_url': 'http://done.com'}
#    
#    
#    
#class ScaffoldMiddle(Scaffold):
#    action_set = ["ActionMiddle1", "ActionMiddle2"]
#    parent = ScaffoldRoot() # this would normally be set automatically by the handler, but is mocked for this test
#    
#class ActionMiddle1(Action):
#    scaffold = ScaffoldMiddle() # this would normally be set automatically by the handler, but is mocked for this test
#
#class ActionMiddle2(Action):
#    scaffold = ScaffoldMiddle() # this would normally be set automatically by the handler, but is mocked for this test
#
#
#class LinearTransitionTest(unittest.TestCase):
#    
#    def test_linear_transition(self):
#        transition = Linear()
#        
#        self.assertEqual( ActionMiddle1, transition.choose_next(ActionRoot1))
#        self.assertEqual( ActionMiddle2, transition.choose_next(ActionMiddle1))
#        self.assertEqual( ActionRoot2, transition.choose_next(ActionMiddle2))
#        
#        # we should end up with a redirect to the _on_complete_url
#        resp = transition.choose_next(ActionRoot2)
#        self.assertEqual(302, resp.status_code)
#        
#        