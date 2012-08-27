from django.core.exceptions import ImproperlyConfigured

try:
    import redis
except ImportError:
    raise ImproperlyConfigured('The "redis" python client package is required to use Redis as a task state store - get it here http://pypi.python.org/pypi/redis/')
