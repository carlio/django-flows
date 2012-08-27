django-flows
============


Settings
========

For all defaults, see ``flows.config``.

- ``FLOWS_STATE_STORE``

    Default: ``flows.statestore.django_store``

    Flows keep state between requests using a persistant storage mechanism. This 
    mechanism is configurable by changing the ``FLOWS_STATE_STORE`` setting. The
    default is to use django models to store the task state.

    Available options built in:
    
    - ``flows.statestore.django_store``
    
        This will store state on django models.
        
    - ``flows.statestore.redis_store``
    
        This will store state in a redis database. Additional configuration options are
        available here, with sensible defaults:
        
        - ``FLOWS_REDIS_STATE_STORE_DB``
        
            The Redis DB number to use. Defaults to ``0``
            
        - ``FLOWS_REDIS_STATE_STORE_HOST``
        
            The host running the redis server to use. Defaults to ``localhost``
            
        - ``FLOWS_REDIS_STATE_STORE_PORT``
        
            The port to connect to on the redis server. Defaults to ``6379``
            
        - ``FLOWS_REDIS_STATE_STORE_USER``
        
            The user to use when connecting to the redis server. Defaults to empty.
            
        - ``FLOWS_REDIS_STATE_STORE_PASSWORD``
        
            The password to use when connecting to the redis server. Defaults to empty.
        
    You can also create your own method of state storage. Simply create a module with
    a class called ``StateStore`` which extends ``BaseStateStore`` in ``flows.statestore.base``
    and implement the two methods ``get_state(self, task_id)`` and ``put_state(self, task_id, state)``.
    Then change the ``FLOWS_STATE_STORE`` setting to the module you created.
    
- ``FLOWS_TASK_IDLE_TIMEOUT``

    The time to allow a task to idle before it is removed. That is, how long the state will be
    kept without any interaction from the user. This value is in seconds, and defaults to 20 minutes.
    
 

