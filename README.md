django-flows
============


Concepts
========

Flows, Actions and Scaffolds
----------------------------

State
-----

Preconditions
-------------

Transitions
-----------


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
    
 
- ``FLOWS_TASK_ID_PARAM``

    The ID of the current flow is kept in the URL to differentiate between different flows
    occurring concurrently for the same user in the same browser. The default value is ``_t``.
    
- ``FLOWS_TASK_BINDER``

    Task IDs are appended to every URL. This URL can easily be shared. To prevent a user giving out
    their task state simply by sharing a URL, a task ID is bound to a value specific to the current
    user so that only the user who started a task can continue executing it. 
    
    This setting is a method which will be called to get the value to bind the task to. It is called
    with a single argument, the current request. The default behaviour is to bind the task to the
    session ID.

    
