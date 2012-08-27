from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect



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
    
    def _get_first_action(self, flow_component):
        if flow_component.is_action:
            # if it's an action, then we've found what comes next
            return flow_component
        
        # otherwise it is a scaffold, and we have to recurse into it to get the first action
        return self._get_first_action(flow_component.action_set[0])
    
    def _get_next_action(self, scaffold):
        
        parent = scaffold.parent
        if parent == None:
            # we don't know what to do!
            return None
        
        scaffold_idx = parent.action_set.index(scaffold.__class__)
        next_fc_idx = scaffold_idx+1
        if next_fc_idx == len(parent.action_set):
            # we are at the end! move up!
            return self._get_next_action(parent)
        
        next_fc = parent.action_set[next_fc_idx]
        if next_fc.is_action:
            return next_fc
        
        # otherwise it's a scaffold
        return self._get_next_action(next_fc)
        
    
    def choose_next(self, action):
        
        action_set = action.scaffold.action_set
        idx = action_set.index(action)
        
        if idx + 1 == len(action_set):
            # this was the last action in this particular set, so figure 
            # out what to do next from the scaffold
            where_to = self._get_next_action(action.scaffold)
            if where_to:
                # we have somewhere to go!
                return where_to
            
            # this means that we've fallen off the end of 
            # the list of actions, so we should redirect to the
            # _on_complete_url if it exists
            complete_url = action.state.get('_on_complete_url', None)
            if complete_url:
                return HttpResponseRedirect(complete_url)
            else:
                raise ImproperlyConfigured('Flow does not have an _on_complete_url, so it should handle flow completion itself rather than rely on the transition class')
            
        
        # otherwise move on to the next item in the list
        return self._get_first_action(action_set[idx+1])
    