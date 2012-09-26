from flows.statestore import state_store
from flows.statestore.base import StateNotFound
from flows.components import FlowComponent, Scaffold, Action, name_for_flow
from flows import config
from django.conf.urls import patterns, url, include
import re
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from flows.history import FlowHistory
import uuid
from django.core.exceptions import ImproperlyConfigured



class FlowHandler(object):
    
    def __init__(self):
        self._entry_points = []
    
    def _get_state(self, task_id, create=False):
        
        if not re.match('^[0-9a-f]{32}$', task_id):
            # someone is messing with the task ID - don't even try
            # to do anything with it
            raise StateNotFound
        
        try:
            return state_store.get_state(task_id)
        except StateNotFound:
            if not create:
                raise
            
        # create a task and some state
        task_id = re.sub('-', '', str(uuid.uuid4()))
        state = {'_id': task_id }
        state_store.put_state(task_id, state)
        
        return state

    
    def _view(self, position):

        def handle_view(request, *args, **kwargs):
            # first get the state for this task, or create state if
            # this is an entry point with no state
            if config.FLOWS_TASK_ID_PARAM in request.REQUEST:
                task_id = request.REQUEST[config.FLOWS_TASK_ID_PARAM]
                create = False
            else:
                task_id = re.sub('-', '', str(uuid.uuid4()))
                create = True
            state = self._get_state(task_id, create=create)

            # create the instances required to handle the request 
            flow_instance = position.create_instance(state)
                
            root_flow = flow_instance.get_root_flow()
            flow_instance.setup(request, *args, **kwargs)

            if request.method == 'POST' and '_go_back' in request.POST:
                response = redirect(flow_instance.get_back_url())

            else:
                response = root_flow.handle(request, *args, **kwargs)
                if isinstance(response, FlowComponent):
                    # this is a flow, so redirect to it
                    url = response.get_absolute_url()
                    response = redirect(url)

            if response == COMPLETE:
                # we are done! we should have an 'on complete' value in 
                # the state to send the user to next
                next_url = state.get('_on_complete', None)
                if next_url is None:
                    # oh, we don't... well, never mind
                    # TODO we could error here, or we could just display a nice message
                    pass
                else:
                    response = redirect(next_url)

                # if we are done, then we should remove the task state
                state_store.delete(task_id)

                return response

            # if this is a GET request, then we displayed something to the user, so
            # we should record this in the history, unless the request returned a 
            # redirect, in which case we haven't displayed anything
            if request.method == 'GET' and not isinstance(response, HttpResponseRedirect):
                history.add_to_history(state)

            state_store.put_state(task_id, state)

            for flow in flows:
                flow.process_response(response)

            return response

        return handle_view

    
    def _urls_for_flow(self, flow_component, flow_position=None):

        urlpatterns = []
        
        if flow_position is None:
            flow_position = FlowPosition(flow_component)
        else:
            flow_position = FlowPosition(flow_component, append_to=flow_position)
        
        if hasattr(flow_component, 'urls'):
            flow_urls = flow_component.urls
        else:
            flow_urls = [flow_component.url]

        if issubclass(flow_component, Scaffold) and hasattr(flow_component, 'action_set'):
            for child in flow_component.action_set:
                for u in flow_urls:
                    urlpatterns += patterns('', url(u, include(self._urls_for_flow(child, flow_position))))

        elif issubclass(flow_component, Action):
            name = flow_position.url_name
            for u in flow_urls:
                urlpatterns += patterns('', url(u, self._view(flow_position), name=name))

        else:
            raise TypeError(str(flow_component))

        return urlpatterns
    
    
    def register_entry_point(self, flow_component):
        self._entry_points.append( flow_component )
        
    @property
    def urls(self):
        urlpatterns = []
        for flow in self._entry_points:
            urlpatterns += self._urls_for_flow(flow)
        return urlpatterns


class FlowPositionInstance(object):
    """
    A FlowInstance represents a concrete instance of a PossibleFlowPosition - 
    that is, a user is currently performing an action as part of a flow
    """
    
    def __init__(self, position, state):
        self._position = position
        self._flow_components = []
        
        for flow_component_class in self._position.flow_component_classes:
            flow_component = flow_component_class()
            flow_component._flow_position_instance = self
            flow_component.state = state
            
            self._flow_components.append( flow_component )
            
        self._history = FlowHistory(state, position, self)    
            
        self._validate()
        
    def _validate(self):
        pass
        # TODO: assert that only the last element is an Action and that the
        # rest are Scaffolds
            
    def get_root_component(self):
        return self._flow_components[0]
    
    def get_action(self):
        return self._flow_components[-1]
    
    def get_back_url(self):
        return self._history.get_back_url()
    
    def setup(self, request, *args, **kwargs):
        # first validate that we can actually run by checking for
        # required state, for example
        for flow_component in self._flow_components:
            flow_component.check_preconditions(request, *args, **kwargs)
            
        # now call each of the prepare methods for the components
        for flow_component in self._flow_components:
            flow_component.prepare(request, *args, **kwargs)
    
class PossibleFlowPosition(object):
    """
    A PossibleFlowPosition represents a possible position in a hierachy of 
    flow components. On startup, all FlowComponents (Scaffolds and Actions)
    are inspected to build up a list of all possible positions within all
    avaiable flows. This class represents one such possibility.
    """

    def __init__(self, flow_component, append_to=None):
        if append_to is not None:
            self.flow_component_classes = append_to.flow_component_classes + [flow_component]
        else:
            self.flow_component_classes = [flow_component]
            
    def construct_instance(self, state):
        return FlowPositionInstance(self, state)
            
    @property
    def url_name(self):
        return 'flow_%s' % '/'.join([name_for_flow(fc) for fc in self.flow_component_classes])
    
    
