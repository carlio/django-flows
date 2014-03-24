# -*- coding: UTF-8 -*-
import urllib
import urlparse
from django.views.generic.edit import FormView
from django.forms.forms import Form
from django.core.exceptions import ImproperlyConfigured
from django import forms
import inspect
from flows import config
from django.shortcuts import redirect
from django.utils.safestring import mark_safe


# The internal constant used to indicate that a flow has completed
# but does not want to influence the further flow state - ie, it absolves
# responsibility for moving to the next Action and assumes that the 
# Transition will take care of this  
COMPLETE = 'complete'




class LazyActionSet(list):
    
    def __getitem__(self, *args, **kwargs):
        return get_by_class_or_name(list.__getitem__(self, *args, **kwargs))
    
    def index(self, obj):
        for idx, elem in enumerate(self):
            if obj is elem:
                return idx
        raise ValueError('%s not in list' % obj)
    
    def __iter__(self):
        iterat = super(LazyActionSet, self).__iter__()
        for class_or_string in iterat:
            yield get_by_class_or_name(class_or_string)


class FlowComponentMeta(type):
    registry = {}

    def __new__(mcs, name, bases, attrs):
        inst = super(FlowComponentMeta, mcs).__new__(mcs, name, bases, attrs)

        parents = [b for b in bases if isinstance(b, FlowComponentMeta)]
        if not parents: 
            return inst

        FlowComponentMeta.registry[inst.__name__] = inst
        
        if hasattr(inst, 'action_set'):
            inst.action_set = LazyActionSet(inst.action_set)
            
        return inst



class FlowComponent(object):
    
    __metaclass__ = FlowComponentMeta
    """
    The metaclass is used to register all possible parts of a flow so
    that they can be looked up by name and added to URL patterns
    """


    preconditions = []
    """
    Preconditions is a list of conditions which must be satisfied before
    the flow is run. They will be executed in the order they are listed
    in this attribute. See the `flows.preconditions` module for built-in
    options and instructions on custom preconditions.
    """

    skip_on_back = False
    """
    Some flow components should not be revisited when going 'backwards'
    in the flow - for example, `Action`s which change global state rather
    than just the flow state, such as a login or registration action,
    should not be shown to the user again once clicking 'back'.
    """


    def set_url_args(self, *args, **kwargs):
        """
        Handles the URL arguments that were used to get to this particular
        instance of the flow component. This is called before the `prepare`
        method when handling an incoming request, and when constructing
        the component in order to reverse lookup a URL.
        """
        self.args = args
        self.kwargs = kwargs
    
    def check_preconditions(self, request):
        """
        Ensures that all of the preconditions for this flow
        component are satisfied. It will return the result of
        the first failing precondition, where order is defined
        by their position in the `preconditions` list.
        """
        for prec in getattr(self, 'preconditions', []):
            ret = prec.process(request, self)
            if ret is not None:
                return ret
    
    def prepare(self, request, *args, **kwargs):
        """
        The `prepare` method is called before the request is handled
        on each flow component in turn from root to leaf, to allow them
        to preprocess things such as request arguments or to populate
        state.

        Note: The *args and **kwargs parameters are deprecated in favour
        of `self.args` and `self.kwargs`, and will be removed in a
        future release.
        """
        pass
    
    def handle_response(self, response):
        """
        The `handle_response` method is called after the request has
        been handled on each component in turn from leaf to root, to
        allow them to override responses from further down the chain.
        """
        return response
    
    def get_url_args(self):
        """
        When constructing a URL, flow components may need to provide some
        of the arguments, for example if they consumed and are responsible
        for some of the arguments dealt with in `prepare`. The default
        behaviour is simply to re-use the arguments which were used when
        creating this component.
        
        This method should return a pair of (args, kwargs) 
        """
        return self.args, self.kwargs
    
    def send_to(self, class_or_name, with_errors=None):
        """
        An action can only 'send_to' a sibling - that is, it can only send
        the user to another action or scaffold which is part of its parent
        scaffold.
        """
        url = self.link_to(class_or_name)
        return redirect(url)

    def link_to(self, class_or_name, additional_url_params=None):
        url = self._flow_position_instance.position_instance_for(class_or_name).get_absolute_url()

        if additional_url_params is not None:
            parts = urlparse.urlparse(url)
            query = urlparse.parse_qs(parts.query)
            query.update(additional_url_params)

            parts = list(parts)
            parts[4] = urllib.urlencode(query, doseq=True)
            return urlparse.urlunparse(parts)

        return url




class Scaffold(FlowComponent):
    """
    Flows are essentially a tree structure; a `Scaffold` is a node
    in this tree with children. The children can either be further
    `Scaffold`s or `Action`s. 
    
    A `Scaffold`'s intent is to glue together actions into a small
    piece of congruent functionality. For example, a `LoginOrRegister`
    scaffold will enable the user to either log in if they have an
    account, or to register if they do not. While an `Action` is designed
    to process a single piece of user interaction, a `Scaffold` is
    designed to pull several actions together into one set of functionality.
    """
    
    """
    The transition controls what happens when an `Action` on the
    `Scaffold` completes. The default behaviour is to assume that the
    `Action`s will control the behaviour themselves.
    
    See also the `flows.transitions` module for possible values.
    """
    transition = None
    
    """
    The `action_set` is the set of possible `Action`s which can be
    invoked as part of this section of functionality. It represents
    which actions can possibly be used under this 'node' in the flow
    tree. If an `Action` is in this set, it is not necessarily used,
    but if it is not in this set, then it cannot be used directly by
    any other actions in this set.
    """
    action_set = []

    is_action = False
    
    def _get_transition(self):
        transition = self.transition
        if transition is None:
            return None
        
        if inspect.isclass(transition):
            transition = transition()
            
        return transition
    

    @classmethod    
    def get_initial_action_tree(cls):
        first_item = cls.action_set[0]
        return [cls] + first_item.get_initial_action_tree()
        

    def handle_response(self, response):
        if response != COMPLETE:
            # it was already dealt with, just pass it on
            return response
        
        transition = self._get_transition()
        if transition is None:
            # we have no idea what to do as there's no instructions,
            # so return COMPLETE to delegate up the stack
            return COMPLETE
        
        # otherwise the 'lower' scaffold or action is complete
        # and doesn't have any explicit instructions for what to
        # do next. if we can, work out what to do
        next_class = self._get_transition().choose_next(self)
        if next_class is not COMPLETE:
            return self.send_to(next_class)
        return COMPLETE
        
        


class FlowRenderer(object):
    """
    Small helper class to render various useful parts
    of forms or field to enable flows to function.
    """
    def __init__(self, flow_component):
        self.flow_component = flow_component
    
    # TODO: might be nice to make this into a block tag, something
    # like:
    # 
    #   {% flow %}content content{% endflow %}
    
    def render_form_header(self):
        action = self.form_action()
        html = "<form method='POST' action='%s'>%s" % (action, self.flow_support())
        return mark_safe(html)
    
    def form_action(self): 
        return self.flow_component.get_absolute_url()

    def flow_support(self):
        field = "<input type='hidden' name='%s' value='%s'/>" % (config.FLOWS_TASK_ID_PARAM, self.flow_component.task_id)
        return mark_safe(field)
    

class DefaultActionForm(Form):
    """
    All actions are required to have a form object to fulfil the
    expected behaviour (user GETs content, user POSTs to move to
    next step). The default form is essentially a no-op.
    """
    pass



class Action(FlowComponent, FormView):

    """
    The `form_class` attribute controls which form object is used in
    the `Action`. This is used by django's FormView and the associated
    method calls are the same.
    
    See https://docs.djangoproject.com/en/dev/ref/class-based-views/generic-editing/#formview
    """
    form_class = DefaultActionForm
    
    is_action = True
    
    def get_context_data(self, **kwargs):
        ctx = FormView.get_context_data(self, **kwargs)
        ctx.update(self.state)
        ctx['flows_back_url'] = self._flow_position_instance.get_back_url()
        ctx['flow'] = FlowRenderer(self)
        return ctx
    
    def get_absolute_url(self):
        return self._flow_position_instance.get_absolute_url()
    
    @classmethod    
    def get_initial_action_tree(cls):
        return [cls]
    
    def get_form(self, form_class):
        form = FormView.get_form(self, form_class)
        form.fields[config.FLOWS_TASK_ID_PARAM] = forms.CharField(widget=forms.HiddenInput, 
                                                                  initial=self.task_id,
                                                                  required=False)
        if '_with_errors' in self.state:
            errors = self.state.pop('_with_errors')
            form.full_clean()
            for field_name, error_message in errors.iteritems():
                form._errors[field_name] = form.error_class(error_message)
        return form
    
    def form_valid(self, form):
        """
        This is called if the form was submitted via a POST request
        and if all of its validation is complete. The user at this
        point has filled in the form successfully, or simply clicked
        'next' if there is no form. 
        
        An `Action` should process the form data in this method, for
        example by creating database models, then return an indication
        of which action to go to next.
        
        If using a `transition`, then the `Action` can simply return
        `COMPLETE` to allow the transition to be handled automatically.
        
        Otherwise it should return another `Action` class, or a string
        which will be interpreted as the name of an `Action`, or an
        `HttpResponse`.
        """
        return COMPLETE
    
    


# Internal utility methods and classes

def get_by_class_or_name(class_or_string):
    if isinstance( class_or_string, basestring ):
        reg = FlowComponentMeta.registry
        if class_or_string not in reg:
            raise ImproperlyConfigured("No such flow component: '%s'" % class_or_string)
        return reg[class_or_string]
    return class_or_string
    
    
_flow_ids = {}
    
def name_for_flow(flow):
    
    if isinstance(flow, FlowComponent):
        # this is an instance, get the class
        F = flow.__class__
    else:
        F = flow
    
    key = F.__module__ + '.' + F.__name__
    if key in _flow_ids:
        name = _flow_ids[key]
    else:
        name = str(len(_flow_ids))
        _flow_ids[key] = name
    return name
                                        

