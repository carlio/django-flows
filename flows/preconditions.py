from django.http import HttpResponse



class RequiredState(object):
    """
    This precondition ensures that the current flow state contains
    the given arguments before processing is allowed to continue.
    This can therefore prevent Actions being run before previous
    Actions have had a chance to prepare the state correctly.
    """
    
    def __init__(self, *args):
        self.required_state = args
    
    def process(self, component):
        state = component.state
        for varname in self.required_state:
            if varname not in state:
                return HttpResponse('Incorrect state', status=424)
    
    def __str__(self):
        return 'RequiredState: %s' % (''.join(self.required_state))