"""
Various helper classes which aid use of django-flows 
with djang-crispy-forms
"""
from django.core.exceptions import ImproperlyConfigured

try:
    from crispy_forms.layout import Layout, Field
except ImportError:
    raise ImproperlyConfigured('django-crispy-forms is not installed, \
                                so the crispy support cannot be used. \
                                Please install django-crispy-forms.' )


"""
All layouts need to include this one to ensure that the
task ID is preserved
"""
flow_layout = Layout(
    Field('_id')
)


class FlowsLayout(Layout):
    """
    Simple class to use in place of the default crispy-forms Layout
    in order to include the required django-flows state automatically
    """
    
    def __init__(self, *args, **kwargs):
        super(FlowsLayout, self).__init__(flow_layout, *args, **kwargs)
