# -*- coding: UTF-8 -*-

'''
Created on Mar 4, 2012

@author: carl
'''

from django.core.urlresolvers import reverse
from django.views.generic.edit import FormView
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.conf import settings 
from django.http import HttpResponse
from django.core.exceptions import ImproperlyConfigured


class InvalidFlowState(Exception):
    pass


def url_name_for_hierarchy(hierarchy):
    return 'flow_%s' % '/'.join([name_for_flow(h) for h in hierarchy])



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



class FlowComponentMeta(type):
    registry = {}

    def __new__(cls, name, bases, attrs):
        inst = super(FlowComponentMeta, cls).__new__(cls, name, bases, attrs)

        parents = [b for b in bases if isinstance(b, FlowComponentMeta)]
        if not parents: 
            return inst

        FlowComponentMeta.registry[inst.__name__] = inst
        
        if hasattr(inst, 'children'):
            inst.children = LazyChildList(inst.children)

        return inst


class LazyChildList(list):
    
    def _get_child_class(self, class_or_string):
        if isinstance( class_or_string, (str, unicode) ):
            reg = FlowComponentMeta.registry
            if class_or_string not in reg:
                raise ImproperlyConfigured("No such flow: '%s'" % class_or_string)
            return reg[class_or_string]
        return class_or_string
    
    def __getitem__(self, *args, **kwargs):
        return self._get_child_class(list.__getitem__(self, *args, **kwargs))
    
    def __iter__(self):
        iter = super(LazyChildList, self).__iter__()
        for class_or_string in iter:
            yield self._get_child_class(class_or_string)
            



class FlowComponent(object):
        
    __metaclass__ = FlowComponentMeta
    
    COMPLETE = HttpResponse('complete')
    TASK_ID_PARAM = '_id'
    required_state = ()

    def __init__(self, handler, state, parent=None, child=None):
        self.handler = handler
        self.set_relations(parent, child)
        self.state = state
        self._cookies_to_set = []
        self.history = None
    
    @property
    def task_id(self):
        return self.state['_id']
        
    def set_relations(self, parent, child):
        self.parent = parent
        self.child = child
        
    def _construct(self, F, parent=None, child=None):
        return F(self.handler, self.state, parent=parent or self.parent, child=child)
        
    def preverify_state(self):
        if self.child is not None:
            self.child.preverify_state()
        for name in self.required_state:
            if name not in self.state:
                raise InvalidFlowState("Missing state: %s" % name)
        
    def get_next(self):
        if self.child is None:
            return FlowComponent.COMPLETE
        
        if hasattr(self, 'children'):
            for i, Child in enumerate(self.children):
                if isinstance(self.child, Child):
                    if i+1 < len(self.children):
                        next = self._construct(self.children[i+1], parent=self).get_initial_flow()
                        self.child = next
                        return next
                    else:
                        return FlowComponent.COMPLETE
                  
        return FlowComponent.COMPLETE


    def handle(self, request, *args, **kwargs):
        # the default behaviour is simply to delegate, then find the next guy in our children
        response = self.child.handle(request, *args, **kwargs)
        
        if response == FlowComponent.COMPLETE:
            return self.get_next()
        
        return response

    def process_response(self, response):
        for args, kwargs in self._cookies_to_set:
            response.set_cookie(*args, **kwargs)

    
    def set_cookie(self, *args, **kwargs):
        self._cookies_to_set.append( (args, kwargs) )

    
    def get_absolute_url(self, hierarchy=None, *args, **kwargs):
        # insert ourself into the hierarchy
        hierarchy = hierarchy or []
        hierarchy.insert(0, self)
        
        # include any url arguments
        my_args, my_kwargs = self.url_args()
        args = my_args + list(args)
        kwargs.update(my_kwargs)
        
        if self.parent is not None:
            # keep moving up the chain if we are not the 'root'
            return self.parent.get_absolute_url(hierarchy, *args, **kwargs)
        
        # otherwise we are the root, so we can now construct the URL
        name = url_name_for_hierarchy(hierarchy)
        url = reverse(name, args=args, kwargs=kwargs)
        separator = '&' if '?' in url else '?'
        root = settings.SITE_ROOT
        return "%s%s%s%s=%s" % (root, url, separator, FlowComponent.TASK_ID_PARAM, self.task_id) 


    def url_args(self):
        return [], {}
    
    def get_initial_flow(self):
        return self._construct(self.children[0], parent=self).get_initial_flow()
    
    def send_to(self, Segment, new_flow=False, with_errors=None):
        if isinstance(Segment, (str, unicode)):
            Segment = self.handler.get_by_name(Segment)
            
        if with_errors is not None:
            self.state['_with_errors'] = with_errors
        
        if not hasattr(self, 'children') or (Segment not in self.children and Segment.__name__ not in self.children):
            # we can't create a child if we are not a flow with children, so
            # delegate to our parent, if we have one
            if self.parent is not None:
                return self.parent.send_to(Segment, new_flow=new_flow)
            
        if new_flow:
            segment = Segment(self.handler, self.state).get_initial_flow()
        else:
            segment = self._construct(Segment, parent=self)
        return segment.get_initial_flow()
    
    def link_to(self, Segment, parent=None):
        if isinstance(Segment, (str, unicode)):
            Segment = self.handler.get_by_name(Segment)
            
        return self.send_to(Segment, parent).get_absolute_url()


class Flow(FlowComponent):
    segment = False


class BranchingFlow(Flow):
    def get_next(self):
        return self.child.get_next()


class FlowForm(forms.Form):
    pass


class FlowSegment(FlowComponent, FormView):
    
    exclude_from_history = False
    form_class = FlowForm
    segment = True
    
    def get_context_data(self, **kwargs):
        ctx = FormView.get_context_data(self, **kwargs)
        ctx.update(self.state)
        ctx['flow'] = self
        return ctx
    
    def get_initial_flow(self):
        return self
    
    def handle(self, request, *args, **kwargs):
        return self.dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        return FlowComponent.COMPLETE
    
    def get_form(self, form_class):
        form = FormView.get_form(self, form_class)
        form.fields[FlowComponent.TASK_ID_PARAM] = forms.CharField(widget=forms.HiddenInput, initial=self.task_id)
        if '_with_errors' in self.state:
            errors = self.state.pop('_with_errors')
            form.full_clean()
            for field_name, error_message in errors.iteritems():
                form._errors[field_name] = form.error_class(error_message)
        return form
    
    @property
    def id_field(self):
        field = "<input type='hidden' name='%s' value='%s'/>" % (FlowComponent.TASK_ID_PARAM, self.task_id)
        return mark_safe(field)

    def back_button(self, label=None):
        url = self.history.get_back_url()
        if not url:
            return ''
        label = label or _('Back')
        link = "<a href='%s' class='lp_back'>%s</a>" % (url, label)
        return mark_safe(link)

