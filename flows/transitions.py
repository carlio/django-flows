from django.core.exceptions import ImproperlyConfigured



class NonAutomatic(object):
    """
    The `NonAutomatic` transition does nothing, and will raise an
    exception if called. It is assumed that an `Action` will explicitly
    decide where to go next. 
    
    This is the default transition.
    """
    def choose_next(self, action):
        raise ImproperlyConfigured('The NonAutomatic transition should not be called - this implies an Action incorrectly returned COMPLETE rather than an explicit destination')


class Linear(object):
    """
    The `Linear` transition assumes that once an `Action` has completed,
    the flow should transition to the next `Action` in the relevant
    `Scaffold`'s `action_set`. If there are no more actions left, then
    the parent scaffold's action set will be consulted. When the root
    scaffold is eventually reached, then the flow is considered to be
    complete and the user will be sent to the contents of `_on_complete_url`
    in the state if present. If this is not present, then an exception
    will be raised.
    """
    
    def choose_next(self, action):
        
        action_set = action.scaffold.action_set
        
        pass