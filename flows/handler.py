# -*- coding: UTF-8 -*-
from weakref import WeakSet
from django.conf.urls import patterns, url, include
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import redirect
from django.conf import settings
from flows import config
from flows.components import Scaffold, Action, name_for_flow, COMPLETE, \
    get_by_class_or_name
from flows.history import FlowHistory
from flows.statestore import state_store as default_state_store
from flows.statestore.base import StateNotFound
import inspect
import logging
import re
import uuid
from flows.binder import binder
import urlparse
import urllib


logger = logging.getLogger(__name__)

try:
    import pydot
    has_pydot = True
except ImportError:
    has_pydot = False
    


class FlowHandlerBase(object):
    registry = WeakSet()

    def __init__(self, *args, **kwargs):
        FlowHandlerBase.registry.add(self)
        super(FlowHandlerBase, self).__init__(*args, **kwargs)

    @staticmethod
    def full_flow_graph(request):
        """
        This is a Django view function that returns a PNG that has all flows
        of all `FlowHandler`s created in a Django shell. It can do that because
        `FlowHandlerBase` keeps track of all `FlowHandler` instances created.
        Basically it combines all .flowgraph debug URLs. To use it, just
        add the handler to your URL config like this:

            if settings.DEBUG:
                urlpatterns += patterns('',
                    url(r'^\.fullflowgraph$', FlowHandlerBase.flow_graph),
                )
        """
        logger.debug('(%s) flow_graphs' % len(FlowHandlerBase.registry))
        if not has_pydot:
            raise ImproperlyConfigured('The pydot library is required to see flowgraph debug output')

        graph = pydot.Dot(graph_type='graph')

        for handler in FlowHandlerBase.registry:
            logger.debug('--- %s' % handler)
            for flow in handler._entry_points:
                handler._add_flow_nodes(graph, flow)

        data = graph.create_png()

        return HttpResponse(data, content_type='image/png')


class FlowHandler(FlowHandlerBase):

    def __init__(self, app_namespace=None, state_store=None, *args, **kwargs):
        super(FlowHandler, self).__init__(*args, **kwargs)
        self._entry_points = []
        self.app_namespace = app_namespace
        self.state_store = state_store or default_state_store
        
    
    def _get_state(self, task_id):
        
        if not re.match('^[0-9a-f]{32}$', task_id):
            # someone is messing with the task ID - don't even try
            # to do anything with it
            raise StateNotFound
        
        return self.state_store.get_state(task_id)

    
    def _view(self, position):
        
        def handle_view(request, *args, **kwargs):
            # first get the state for this task, or create state if
            # this is an entry point with no state
            if config.FLOWS_TASK_ID_PARAM in request.REQUEST:
                task_id = request.REQUEST[config.FLOWS_TASK_ID_PARAM]
                
                try:
                    state = self._get_state(task_id)
                except StateNotFound:
                    logger.debug("Could not find task with ID %s" % task_id)
                    raise Http404
                
                bound_to = state.get('_bound_to', None)
                bind_to = binder(request)
                
                if bound_to is None or bind_to is None or bind_to != bound_to:
                    logger.debug('Will not give task %s as it is bound to %s, not %s' % (task_id, bound_to, bind_to))
                    raise Http404
                
            else:
                # are we at an entry point? if so, then create some new state
                # otherwise we're trying to enter the middle of a flow, which
                # is not allowed
                if position.is_entry_point():
                    initial = {}
                    if '_on_complete' in request.REQUEST:
                        initial['_on_complete'] = request.REQUEST['_on_complete']
                    state = self._new_state(request, **initial)
                else:
                    logger.debug('Flow position is not an entry point: %s' % position)
                    raise Http404
                
            # create the instances required to handle the request 
            flow_instance = position.create_instance(state, self.state_store, args, kwargs)
                
            # deal with the request
            return flow_instance.handle(request, *args, **kwargs)

        return handle_view
    
    def _new_state(self, request, **initial_state):
        task_id = re.sub('-', '', str(uuid.uuid4()))
        bind_to = binder(request)
        if bind_to is None:
            raise ImproperlyConfigured('A value is required to bind the task to')
        
        state = {'_id': task_id, '_bound_to': bind_to}
        state.update( initial_state )
        self.state_store.put_state(task_id, state)
        
        return state
    
    def _urls_for_flow(self, flow_namespace, flow_component, flow_position=None):

        urlpatterns = []
                
        if flow_position is None:
            flow_position = PossibleFlowPosition(self.app_namespace, flow_namespace, [flow_component])
        else:
            flow_position = PossibleFlowPosition(self.app_namespace, flow_namespace, flow_position.flow_component_classes + [flow_component])
        
        if hasattr(flow_component, 'urls'):
            flow_urls = flow_component.urls
        else:
            flow_urls = [flow_component.url]
            
        if issubclass(flow_component, Scaffold) and hasattr(flow_component, 'action_set'):
            for child in flow_component.action_set:
                for u in flow_urls:
                    urlpatterns += patterns('', url(u, include(self._urls_for_flow(flow_namespace, child, flow_position))))

        elif issubclass(flow_component, Action):
            name = flow_position.get_url_name(include_app_namespace=False)
            for u in flow_urls:
                urlpatterns += patterns('', url(u, self._view(flow_position), name=name))

        else:
            raise TypeError(str(flow_component))

        return urlpatterns

    def register_entry_point(self, flow_component):
        self._entry_points.append(flow_component)
        
    def _add_flow_nodes(self, graph, component, root=None, depth=0):
        
        name = '%s - %s' % (depth, component.__name__)
        if hasattr(component, 'url'):
            urls = [component.url]
        elif hasattr(component, 'urls'):
            urls = component.urls
            
        urls = ['<empty>' if u is '' else u for u in urls]
        name = "%s\n%s" % (name, '\n'.join(urls))
            
        graph.add_node(pydot.Node(name))
        if root:
            graph.add_edge(pydot.Edge(root, name))
            
        for fc in getattr(component, 'action_set', []):
            self._add_flow_nodes(graph, fc, root=name, depth=depth+1)
        
    def flow_graph(self, request):
        if not has_pydot:
            raise ImproperlyConfigured('The pydot library is required to see flowgraph debug output')
        
        graph = pydot.Dot(graph_type='graph')
        
        for flow in self._entry_points:
            self._add_flow_nodes(graph, flow)
            
        data = graph.create_png()
        
        return HttpResponse(data, content_type='image/png')
        
    def flow_entry_link(self, request, flow_class_or_name, on_complete_url=None,
                        with_state=False, initial_state=None,
                        flow_namespace=None,
                        url_args=None, url_kwargs=None, url_queryargs=None):
        """
        This method is how you create a URL which allows a user to enter a flow.

        There are two main times you will need this, both with different consequences
        for the values you should pass as arguments.

        1) If you display a page to a user including a URL which starts a flow, but which
        the user may not necessarily begin, then you should use a stateless task. That
        is to say, don't include `initial_state`. If the flow needs to behave differently
        based on some context, then include it using `url_args` and `url_kwargs`, and have
        the flow Action or Scaffold handle that in their `url` configuration. As an example,
        you may be on a product page, and want a link for the user should they choose to
        purchase it. In this case, few users may actually click the link, so creating
        task state which will never be used is inefficient. In that case, the product ID
        could be passed into the flow via URL parameters - this is more like a normal Django
        URL

        2) If a user performs an action that enters them into a flow explicitly. If a
        user clicks something and you want the user to immediately enter a flow, you
        can pass in `initial_state`.

        Parameters
        ----------
        request : django.http.HttpRequest
           A request object supplied by Django

        flow_class_or_name : str | Action | Scaffold
          The flow entry point to create a URL for. This can be a string to do a lookup
          by name, or the Action or Scaffold class itself, which is preferred. Note that
          the flow action must have been registered as an entry point with this handler
          via `register_entry_point`

        on_complete_url : str
          The URL to redirect to once the flow is complete, used if the actions do not
          redirect themselves and instead rely on the automatic transitions.

        with_state : bool
          *Deprecated* By default, state is not created until the user begins the flow,
          to avoid creating unnecessary database objects, especially when the link is
          simply created to be displayed in a page. Sometimes, however, when constructing
          a link to redirect to as the result of a user action, it's useful to create the
          state for the flow. This has been deprecated in favour of "initial_state"

        initial_state : dict
          If you want to create a flow with some initial state, you can pass it in here. Note
          this is not suitable for, eg, URLs on an HTML page, since it would create a task
          state object for every pageview regardless of the user's intention. It is much
          better if the user has performed an action, such as submitted a form, which
          implies they want to immediately enter a flow. See also `url_args` and `url_kwargs`.

        flow_namespace : str

        url_args : list | tuple
        url_kwargs : dict
          The arguments to pass in to the URL for the flow, if your actions specify any
          parameters in their URL pattern. This is typically the way to supply "initial
          state" for flow entry URLs generated before a user action has taken place. See
          also `initial_state`.

        url_queryargs : dict
          Query parameters to append to the generated URL. You should probably be using
          `url_args` and `url_kwargs` along with URL patterns, or `initial_state`, instead.
        """

        if initial_state is None:
            initial_state = {}
        else:
            # override the with_state option in the case that
            # we have some initial state to explicitly set
            with_state = True

        flow_class = get_by_class_or_name(flow_class_or_name)
        
        position = PossibleFlowPosition(self.app_namespace, flow_namespace, flow_class.get_initial_action_tree())

        if with_state:
            if on_complete_url is not None:
                initial_state['_on_complete'] = on_complete_url
            state = self._new_state(request, **initial_state)
        else:
            state = {'_id': ''}  # TODO: this is a bit of a hack, but task_id is required...
        instance = position.create_instance(state, self.state_store, url_args=url_args, url_kwargs=url_kwargs)

        # if we have state, then we need to include the task ID in the URL
        # returned, otherwise it'll be seen as a "new entry" and new empty
        # task state will be created
        inst_url = instance.get_absolute_url(include_flow_id=with_state)

        parts = urlparse.urlparse(inst_url)
        query = urlparse.parse_qsl(parts.query)

        if on_complete_url is not None:
            query.append(('_on_complete', on_complete_url))
        if url_queryargs is not None:
            query.update(url_queryargs)

        parts = list(parts)
        parts[4] = urllib.urlencode(query, doseq=True)

        return urlparse.urlunparse(parts)
        
    def list_urls(self, urllist, prefix=''):
        urls = []
        for entry in urllist:
            if hasattr(entry, 'url_patterns'):
                # this has further sub-patterns
                urls += self.list_urls(entry.url_patterns, prefix+entry.regex.pattern)
            else:
                urls.append(prefix + entry.regex.pattern)
        return urls 
        
    def get_urls(self, flow_namespace=None):
        return self._get_url_patterns(flow_namespace)
        
    @property
    def urls(self):
        return self.get_urls(None)
    
    def _get_url_patterns(self, flow_namespace):
        urlpatterns = []
        for flow in self._entry_points:
            urlpatterns += self._urls_for_flow(flow_namespace, flow)
        if settings.DEBUG:
            prefix = flow_namespace if flow_namespace else ''
            urlpatterns += patterns('', url('%s\.flowgraph$' % prefix, self.flow_graph))
            
        # verify that URLs are unique
        url_list = self.list_urls(urlpatterns)
        url_set = set()

        for url_entry in url_list:
            if url_entry in url_set:
                raise ImproperlyConfigured('Url is not unique: %s' % url_entry)
            url_set.add(url_entry)
        
        return urlpatterns


class FlowPositionInstance(object):
    """
    A FlowPositionInstance represents a concrete instance of a PossibleFlowPosition - 
    that is, a user is currently performing an action as part of a flow
    """
    
    def __init__(self, app_namespace, flow_namespace, position, state, state_store, url_args, url_kwargs):
        self._app_namespace = app_namespace
        self._flow_namespace = flow_namespace
        self._position = position
        self._state = state
        self._flow_components = []
        self.state_store = state_store

        self._url_args = url_args or []
        self._url_kwargs = url_kwargs or {}
        
        for flow_component_class in self._position.flow_component_classes:
            flow_component = flow_component_class()
            flow_component._flow_position_instance = self
            flow_component.set_url_args(*self._url_args, **self._url_kwargs)
            flow_component.state = state
            flow_component.task_id = self.task_id
            flow_component.app_namespace = self._app_namespace
            flow_component.flow_namespace = self._flow_namespace
            
            self._flow_components.append( flow_component )
            
        self._history = FlowHistory(self)    
            
        self._validate()
        
    def _validate(self):
        pass
        # TODO: assert that only the last element is an Action and that the
        # rest are Scaffolds
        
    @property
    def task_id(self):
        return self._state['_id']
            
    def get_root_component(self):
        return self._flow_components[0]
    
    def get_action(self):
        return self._flow_components[-1]
    
    def get_back_url(self):
        return self._history.get_back_url()
    
    def get_absolute_url(self, include_flow_id=True):
        args = []
        kwargs = {}
        for flow_component in self._flow_components:
            flow_args, flow_kwargs = flow_component.get_url_args()
            args += flow_args
            kwargs.update(flow_kwargs)
            
        url_name = self._position.url_name
        url = reverse(url_name, args=args, kwargs=kwargs)
        
        if include_flow_id:
        
            separator = '&' if '?' in url else '?'
            
            return '%(root)s%(url)s%(separator)s%(task_id_param_name)s=%(task_id)s' % { 
                                     'root': config.FLOWS_SITE_ROOT,
                                     'url': url, 'separator': separator,
                                     'task_id_param_name': config.FLOWS_TASK_ID_PARAM,
                                     'task_id': self.task_id  }
        else:
            return '%(root)s%(url)s' % { 'root': config.FLOWS_SITE_ROOT, 'url': url }

    def position_instance_for(self, component_class_or_name):
        # figure out where we're being sent to
        FC = get_by_class_or_name(component_class_or_name)
        
        # it should be a sibling of one of the current items
        # for example, if we are in position [A,B,E]:
        #
        #         A
        #      /  |  \
        #    B    C   D
        #   /  \      |  \
        #  E   F      G   H
        # 
        #  E can send to F (its own sibling) or C (sibling of its parent)

        for fci in self._flow_components[-2::-1]: # go backwards but skip the last element (the action)
            if FC in fci.action_set:
                # we found the relevant action set, which means we know the root
                # part of the tree, and now we can construct the rest
                idx = self._flow_components.index(fci)
                break
        else:
            raise ValueError('Could not figure out how to redirect to %s' % FC)

        # so the new tree is from the root to the parent of the one we just found,
        # coupled with the initial subtree from the component we're tring to redirect
        # to
        tree_root = self._position.flow_component_classes[:idx+1]
        
        # figure out the action tree for the new first component - either
        # we have been given an action, in which case it's just one single
        # item, or we have been given a scaffold, in which case there could
        # be a list of [scaffold, scaffold..., action]
        new_subtree = FC.get_initial_action_tree()
        
        # we use our current tree and replace the current leaf with this new 
        # subtree to get the new position
        new_position = PossibleFlowPosition(self._app_namespace, self._flow_namespace, tree_root + new_subtree)
        
        # now create an instance of the position with the current state
        return new_position.create_instance(self._state, self.state_store, self._url_args, self._url_kwargs)
    
    def handle(self, request, *args, **kwargs):
        # first validate that we can actually run by checking for
        # required state, for example
        response = None
        for flow_component in self._flow_components:
            response = flow_component.check_preconditions(request)
            if response is not None:
                break
        
        if response is None:
            # now call each of the prepare methods for the components
            for flow_component in self._flow_components:
                # TODO: passing in *args and **kwargs to prepare is deprecated
                response = flow_component.prepare(request, *args, **kwargs)
                if response is not None:
                    # we allow prepare methods to give out responses if they
                    # want to, eg, redirect
                    break
                
        if response is None:

            # FIXME: mjtamlyn promises to fix this in Django 1.7, but right now we need
            # to set up the magic attributes usually set up by a closure in View.as_view
            # so we can call dispatch on Django>1.5
            action = self.get_action()
            if hasattr(action, 'request'):
                raise Exception('Action re-use?')
            action.request = request
            action.args = args
            action.kwargs = kwargs

            # now that everything is set up, we can handle the request
            response = self.get_action().dispatch(request, *args, **kwargs)
            
            # if this is a GET request, then we displayed something to the user, so
            # we should record this in the history, unless the request returned a 
            # redirect, in which case we haven't displayed anything
            if request.method == 'GET' and not isinstance(response, HttpResponseRedirect):
                self._history.add_to_history(self)
        
        # now we have a response, we need to decide what to do with it
        for flow_component in self._flow_components[::-1]: # go from leaf to root, ie, backwards
            response = flow_component.handle_response(response)
            
        # now we have some kind of response, figure out what it is exactly
        if response == COMPLETE:
            # this means that the entire flow finished - we should redirect
            # to the on_complete url if we have one, or get upset if we don't
            next_url = self._state.get('_on_complete', None)
            if next_url is None:
                # oh, we don't know where to go...
                raise ImproperlyConfigured('Flow completed without an _on_complete URL or an explicit redirect - %s' % self.__repr__())
            else:
                response = redirect(next_url)

            # if we are done, then we should remove the task state
            self.state_store.delete_state(self.task_id)
            
        else:
            # update the state if necessary
            self.state_store.put_state(self.task_id, self._state)
            
            if inspect.isclass(response):
                # we got given a class, which implies the code should redirect
                # to this new (presumably Action) class
                response = redirect(self.position_instance_for(response).get_absolute_url()) 
            
            elif isinstance(response, Action):
                # this is a new action for the user, so redirect to it
                absurl = response.get_absolute_url()
                response = redirect(absurl)
               
            elif isinstance(response, basestring):
                # this is a string which should be the name of an action
                # which couldn't be referenced as a class for some reason
                flow_component = get_by_class_or_name(response)
                response = redirect(flow_component.get_absolute_url()) 

        return response
    
    def __repr__(self):
        return 'Instance of %s' % self._position.__repr__()
        
    
class PossibleFlowPosition(object):
    all_positions = {}
    
    """
    A PossibleFlowPosition represents a possible position in a hierachy of 
    flow components. On startup, all FlowComponents (Scaffolds and Actions)
    are inspected to build up a list of all possible positions within all
    avaiable flows. This class represents one such possibility.
    """

    def __init__(self, app_namespace, flow_namespace, flow_components):
        self.app_namespace = app_namespace
        self.flow_namespace = flow_namespace
        self.flow_component_classes = flow_components

        PossibleFlowPosition.all_positions[self.url_name] = self
            
    def create_instance(self, state, state_store, url_args, url_kwargs):
        return FlowPositionInstance(self.app_namespace, self.flow_namespace, self, state,
                                    state_store, url_args, url_kwargs)
    
    def _url_name_from_components(self, components, include_app_namespace=True):
        if self.flow_namespace is None:
            prefix = 'flow_'
        else:
            prefix = 'flow_%s_' % self.flow_namespace
        if self.app_namespace and include_app_namespace:
            prefix = '%s:%s' % (self.app_namespace, prefix)
        return '%s%s' % (prefix, '/'.join([name_for_flow(fc) for fc in components]))
    
    def is_entry_point(self):
        root_tree = self.flow_component_classes[0].get_initial_action_tree()
        my_tree = self.flow_component_classes
        return root_tree == my_tree
    
    @property
    def url_name(self):
        return self.get_url_name(include_app_namespace=True)
    
    def get_url_name(self, include_app_namespace=True):
        return self._url_name_from_components(self.flow_component_classes, include_app_namespace)
    
    
    def __repr__(self):
        classes = ' / '.join( map(str, self.flow_component_classes) )
        return '%s (%s)' % (classes, self.url_name)
    
