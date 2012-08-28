from flows.statestore import state_store
from flows.statestore.base import StateNotFound
from flows.components import FlowComponent, Scaffold, Action, url_name_for_hierarchy,\
    COMPLETE
from flows import config
from django.conf.urls import patterns, url, include
import re
from django.http import Http404
from django.shortcuts import redirect

class FlowHandler(object):
    
    def __init__(self):
        self._entry_points = []
    
    def _get_state(self, task_id, create=False):
        pass
    
    def _view(self, hierarchy):

        def handle_view(request, *args, **kwargs):

            if config.FLOWS_TASK_ID_PARAM in request.REQUEST:
                task_id = request.REQUEST[config.FLOWS_TASK_ID_PARAM]
                if not re.match('^[0-9a-f]{32}$', task_id):
                    # someone is messing with the task ID - don't even try
                    # to do anything with it
                    raise Http404

                state = state_store.get_task(task_id)
                if state is None:
                    raise Http404
            else:
                state = self._prepare_flow(request, hierarchy[0])
                task_id = state['_id']


            flows = [F(self, state) for F in hierarchy]

            history = FlowHistory(state, hierarchy, flows)

            for i, flow in enumerate(flows):
                parent = flows[i - 1] if i > 0 else None
                child = flows[i + 1] if i + 1 < len(flows) else None
                flow.set_relations(parent, child)
                flow.history = history

            root_flow = flows[0]
            root_flow.preverify_state()

            if request.method == 'POST' and '_go_back' in request.POST:
                response = redirect(history.get_back_url())

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
                    response = HttpResponseRedirect(next_url)

                # if we are done, then we should remove the task state
                _taskloader.delete(task_id, _get_invoice_id(request))

                return response

            # if this is a GET request, then we displayed something to the user, so
            # we should record this in the history, unless the request returned a 
            # redirect, in which case we haven't displayed anything
            if request.method == 'GET' and not isinstance(response, HttpResponseRedirect):
                history.add_to_history(state)

            _taskloader.save(task_id, _get_invoice_id(request), state)

            for flow in flows:
                flow.process_response(response)

            return response

        return handle_view

    
    def _check_preconditions(self, flow_component):
        for prec in getattr(flow_component, 'preconditions', []):
            ret = prec.process(flow_component)
            if ret is not None:
                return ret
    
    def register_entry_point(self, flow_component):
        self._entry_points.append( flow_component )
    
    def _urls_for_flow(self, flow_component, hierarchy=None):

        urlpatterns = []
        hierarchy = list(hierarchy) if hierarchy else []
        hierarchy.append(flow_component)

        if hasattr(flow_component, 'urls'):
            flow_urls = flow_component.urls
        else:
            flow_urls = [flow_component.url]

        if issubclass(flow_component, Scaffold) and hasattr(flow_component, 'action_set'):
            for child in flow_component.action_set:
                for u in flow_urls:
                    urlpatterns += patterns('', url(u, include(self._urls_for_flow(child, hierarchy))))

        elif issubclass(flow_component, Action):
            name = url_name_for_hierarchy(hierarchy)
            for u in flow_urls:
                urlpatterns += patterns('', url(u, self._view(hierarchy), name=name))

        else:
            raise TypeError(str(flow_component))

        return urlpatterns
    
    
    @property
    def urls(self):
        urlpatterns = []
        for flow in self._entry_points:
            urlpatterns += self._urls_for_flow(flow)
        return urlpatterns