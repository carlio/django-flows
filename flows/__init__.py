# -*- coding: UTF-8 -*-

from django.conf import settings
from django.conf.urls.defaults import url, patterns, include
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import redirect
from django.utils.importlib import import_module
from lpconfig.web import SECURECARD_ROOT, WEBUI_ROOT
from webshared.flows.flows import url_name_for_hierarchy, FlowComponent, Flow, \
    FlowSegment, name_for_flow, FlowComponentMeta
import re
import uuid
from django.core.exceptions import ImproperlyConfigured


_taskloader = import_module(settings.TASK_LOADER)

def _get_invoice_id(request):
    return request.lpinvoice.get_device_invoice_id()


class FlowHistory(object):

    def __init__(self, state, hierarchy, flows):
        self._hierarchy = hierarchy
        self._flows = flows
        self._history = state['_history'] if '_history' in state else []

        url_name = url_name_for_hierarchy(self._hierarchy)

        # if we have moved back in the history, throw away the 'future' parts
        for i, pair in enumerate(self._history):
            if url_name == pair[0]:
                # found the current flow in the history, so reset to its position
                self._history = self._history[:i]
                break

        self._back_url = self._history[-1][1] if len(self._history) > 0 else None


    def add_to_history(self, state):
        url_name = url_name_for_hierarchy(self._hierarchy)

        current_flow = self._flows[-1]
        url = current_flow.get_absolute_url()
        skip_on_back = getattr(current_flow, 'skip_on_back', False)

        self._history.append((url_name, url, skip_on_back))
        state['_history'] = self._history


    def get_back_url(self):
        return self._back_url


class FlowHandler(object):

    def __init__(self):
        self._flows = {}
        self._flows_by_classname = {}

    def _view(self, hierarchy):

        def handle_view(request, *args, **kwargs):

            if FlowComponent.TASK_ID_PARAM in request.REQUEST:
                task_id = request.REQUEST[FlowComponent.TASK_ID_PARAM]
                if not re.match('^[0-9a-f]{32}$', task_id):
                    # someone is messing with the task ID - don't even try
                    # to do anything with it
                    raise Http404

                state = _taskloader.load(task_id, _get_invoice_id(request))
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
                    server_id = getattr(response, 'only_on', None)
                    if server_id == 'securecard':
                        url = "%s%s" % (SECURECARD_ROOT, url)
                    elif server_id == 'webui':
                        url = "%s%s" % (WEBUI_ROOT, url)
                    response = redirect(url)

            if response == FlowComponent.COMPLETE:
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

    def _urls_for_flow(self, flow, hierarchy=None):

        urlpatterns = []
        hierarchy = list(hierarchy) if hierarchy else []
        hierarchy.append(flow)

        if hasattr(flow, 'urls'):
            flow_urls = flow.urls
        else:
            flow_urls = [flow.url]

        if issubclass(flow, Flow) and hasattr(flow, 'children'):
            for child in flow.children:
                for u in flow_urls:
                    urlpatterns += patterns('', url(u, include(self._urls_for_flow(child, hierarchy))))

        elif issubclass(flow, FlowSegment):
            name = url_name_for_hierarchy(hierarchy)
            for u in flow_urls:
                urlpatterns += patterns('', url(u, self._view(hierarchy), name=name))

        else:
            raise TypeError(str(flow))

        return urlpatterns


    def register(self, FlowClass):
        name = name_for_flow(FlowClass)
        self._flows[name] = FlowClass

    def get_by_name(self, name):
        reg = FlowComponentMeta.registry
        if name not in reg:
            raise ImproperlyConfigured("No such flow: '%s'" % name)
        return reg[name]

    def get_by_class_or_name(self, flow_class_or_name):
        if isinstance(flow_class_or_name, (str, unicode)):
            flow_class_or_name = self.get_by_name(flow_class_or_name)
        return flow_class_or_name

    def _prepare_flow(self, request, flow_class_or_name, extra_state=None):
        FlowClass = self.get_by_class_or_name(flow_class_or_name)

        name = name_for_flow(FlowClass)
        if name not in self._flows:
            # TODO: real exception
            raise Exception('Flow %s is not registered' % flow_class_or_name)

        # create a task and some state
        task_id = re.sub('-', '', str(uuid.uuid4()))
        state = {'_id': task_id }
        if extra_state is not None:
            state.update(extra_state)

        _taskloader.save(task_id, _get_invoice_id(request), state)
        return state

    def start_flow(self, request, flow_class_or_name, args=None, kwargs=None, on_complete_url=None):
        # get the class in case we were given a name
        FlowClass = self.get_by_class_or_name(flow_class_or_name)

        # set up some state
        state = self._prepare_flow(request, flow_class_or_name, extra_state={ '_on_complete': on_complete_url })

        # construct the class and get the first flow
        flow = FlowClass(self, state).get_initial_flow()

        # figure out the URL for the flow
        args = args or []
        kwargs = kwargs or {}
        url = flow.get_absolute_url(*args, **kwargs)

        return HttpResponseRedirect(url)

    @property
    def urls(self):
        urlpatterns = []
        for flow in self._flows.values():
            urlpatterns += self._urls_for_flow(flow)
        return urlpatterns

