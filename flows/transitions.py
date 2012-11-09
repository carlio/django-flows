# -*- coding: UTF-8 -*-
import random
from flows.components import COMPLETE


class Linear(object):
    """
    The `Linear` transition assumes that once an `Action` has completed,
    the flow should transition to the next `Action` in the relevant
    `Scaffold`'s `action_set`. If there are no more actions left, then
    `FlowComponent.COMPLETE` is returned and it is assumed that the next
    `Scaffold` up the tree will deal with where to go next.
    """
    
    def choose_next(self, scaffold):
        # first figure out where we are in the current position
        # so that we know which of our action_set is in the current
        # path
        position = scaffold._flow_position_instance._position
        
        idx = -1
        for idx, ffc in enumerate(position.flow_component_classes):
            if scaffold.__class__ == ffc:
                # we have found where we are
                break
            
        # idx == -1 implies we didn't find ourselves, which should be
        # impossible
        if idx == -1:
            raise ValueError
        
        # now work out which of our children is in the active path
        if idx+1 >= len(position.flow_component_classes):
            # this means that we are trying to choose the next item
            # from an action, which is impossible as they don't have
            # action sets!
            raise ValueError
        
        active_child = position.flow_component_classes[idx+1]
        action_set = scaffold.action_set
        child_idx = action_set.index(active_child)
        
        # so, we know where we are in our action set, and we are linear,
        # so next is simply the next one in our action set, or COMPLETE
        # if there are no more options
        if child_idx+1 >= len(action_set):
            return COMPLETE
    
        return action_set[child_idx+1]
        
        
        
class Chaos(object):
    """
    Don't use this transition.
    """
    def choose_next(self, scaffold):
        return random.choice(scaffold.action_set)
    

