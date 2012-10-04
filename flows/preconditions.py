# -*- coding: UTF-8 -*-
from django.http import HttpResponse
from django.shortcuts import redirect


class RequiredState(object):
    """
    This precondition ensures that the current flow state contains
    the given arguments before processing is allowed to continue.
    This can therefore prevent Actions being run before previous
    Actions have had a chance to prepare the state correctly.
    """
    
    def __init__(self, *args):
        self.required_state = args
    
    def process(self, request, component):
        state = component.state
        for varname in self.required_state:
            if varname not in state:
                return HttpResponse('State is missing', status=422)
    
    def __repr__(self):
        return 'RequiredState: %s' % (''.join(self.required_state))
    
    
class EnsureAuthenticated(object):
    
    def __init__(self, error_url=None):
        self.error_url = error_url

    def process(self, request, component):
        if not request.user.is_authenticated():
            if self.error_url is not None:
                return redirect(self.error_url)
            return HttpResponse(status=401)
        
