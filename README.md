django-flows
============

[![Build Status](https://secure.travis-ci.org/carlio/django-flows.png)](http://travis-ci.org/carlio/django-flows)

``django-flows`` can best be described as 'wizards on steroids'. Its purpose is to keep state and position in complicated flows of logic, allowing optional branches and complicated paths through a series of individual user actions.

``django-flows`` makes it possible to specify subsections of functionality and group them together later. It recognises that, at the core, there are several user actions such as logging in, or entering a credit card number, and that the web application needs to group these actions in such a way that all state required to make a purchase, for example, is obtained. It also seeks to make these actions reusable, and to group related actions together into larger 'user flows'.

Example
=======

The actual use case which caused this library to be written is the following: say you want to sell something to the user. This requires showing the user what they are buying, how much it costs etc. If the user chooses to purchase, then they have to be logged in. However if they have no account, they have to register. Or, perhaps they forgot their password. Either way, once that is done, then you need the user to choose a method of paying. Either they have already saved a credit card, for example, or they need to enter a new method of payment. This could take various forms - required credit card information is different to bank account information. Once that is collected, then a final confirmation step is required.

The overall process is quite straightforward to explain:

  * Do you want to buy this?
  * Tell us who you are
  * Tell us how you want to pay
  * Confirm everything
  
However each of those steps have various substeps. The actual tree of possible interaction looks something like this:

    +-- Do you want to buy this?
    |
    +-+ Tell us who you are
    | |
    | +-- Log in to existing account OR
    | |
    | +-- Create new account OR
    | |
    | +-+ I forgot my password
    |   |
    |   +-- Enter your email address
    |   |
    |   +-- Enter your confirmation code
    |   |
    |   +-- Reset your password
    |
    +-+ Choose how to pay
    | |
    | +-- Choose a payment method I already saved OR
    | |
    | +-+ Enter a new payment method
    |   |
    |   +-- Credit card number OR
    |   |
    |   +-+ Bank account details
    |   | |
    |   | + Account address
    |   | 
    |   +-- PayPal
    |
    +-- Confirm and pay
    
At each point, there are several options, each of which could branch into more options, which could have sub-options, and so on.

Each of these branches are subsets of functionality which standalone, too. Entering your credit card information is a piece of functionality, just as 'choose a payment method' is. `django-flows` seeks to decouple these pieces so that they are reusable, and enable these pieces to be interchanged, reordered and mixed together in flows at will. 


Concepts
========

Flows
---
A 'flow' is considered to be a series of user actions required to perform some functionality.

Actions
---

At its heart, any flow is just a series of actions taken by the user. These can be as simple as clicking 'next' after reading something informational, to entering large amounts of details to register a new user account.

In `django-flows`, an `Action` is basically identical to a Django `FormView` (and in fact, inherits from it). It will be shown to the user on a `GET` request, and the form will be processed on `POST`. If the form validates, then the `Action` is complete.

When an action is complete, it can either explicitly send the user to another action, or it can simply return `COMPLETE` to allow the flows framework to figure out where to send the user next.

Scaffolds
---

A flow is a set of actions, which can branch at various points. Scaffolds group actions into logical collections (eg, 'Get the user account' has possible actions of 'login' and 'register'). These scaffolds can then be used themselves inside other scaffolds, leading to the tree-like structure which gives `django-flows` its benefit over regular Django wizards.

    class GetUserAccount(Scaffold):
        action_set = [LoginOrRegister, Register, ForgotPassword]
    
In the example above, the `GetUserAccount` scaffold groups the actions which encapsulate all ways a user can become authenticated. `LoginOrRegister` is an action with a login form, with a link to register for users who don't have an account. `Register` is an action which  allows the user to register. `ForgotPassword` is itself a scaffold, which contains the actions required to reset the user's password if they have forgotten it.


Tasks and State
---

The main difficulty with simply using standard views is keeping the state between them. When user intentions can branch or loop back on themselves, trying to use URL parameters or session data can become tedious or even impossible. Additionally, if a user has multiple tabs or browser windows open, then using sessions will cause their interactions between tabs to interfere with each other, leading to unpredictable results.

`django-flows` has the concept of 'tasks'. This is basically an isolated set of state which allows multiple concurrent tasks to run. The specific task which the user is currently doing is kept using an `id` parameter, which is automatically added to URLs and forms generated.

This identifier is used to retrieve state for the particular flow the user is currently working through.

Preconditions
---

Preconditions are various requirements of the current flow state which are checked before the current action is executed. These include things like ensuring that a field is present in the state. For example, if an action requires a 'purchase item' to have been set by a previous action, then a `RequiredState` precondition to check its presence. Another example is `LoginRequired`, which ensures the `Action` will not be available to users who are not authenticated.

Transitions
---
A `Scaffold` is made up of a list of `Action`s which represent some larger functionality. These can sometimes be several steps in a long signup process, or can be several possible branches the user can choose. 

An `Action` can either explicitly send the user, or, for maximum reusability, can simply return `COMPLETE` and let the parent `Scaffold` decide where to send the user next. The decision of where to go next is handled by the `Transition` object.

The default behaviour is to expect the actions to handle their next destination themselves. However sometimes the steps are predictable - moving from step 1 to 2 to 3 - and in this case, using a `Linear` transition will cause the flow to move between `Action`s in the order specified in the `action_set` attribute of the `Scaffold`.


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
            
        - ``FLOWS_REDIS_STATE_STORE_PASSWORD``
        
            The password to use when connecting to the redis server. Defaults to empty.
            
    - ``flows.statestore.tmpfile_store``
        
        This stores state in temporary files on disk. It is not recommended for production use, because state timeout cannot be implemented, leading to stale task state. It can be useful in development however.
        
    You can also create your own method of state storage. Simply create a module with
    a class called ``StateStore`` which extends ``BaseStateStore`` in ``flows.statestore.base``
    and implement the two methods ``get_state(self, task_id)`` and ``put_state(self, task_id, state)``.
    Then change the ``FLOWS_STATE_STORE`` setting to the module you created.
    
- ``FLOWS_TASK_IDLE_TIMEOUT``

    The time to allow a task to idle before it is removed. That is, how long the state will be
    kept without any interaction from the user. This value is in seconds, and defaults to 20 minutes.
    
 
- ``FLOWS_TASK_ID_PARAM``

    The ID of the current flow is kept in the URL as a parameter to differentiate between different flows occurring concurrently for the same user in the same browser. This setting changes the name of the parameter. The default value is ``_id``.
    
- ``FLOWS_TASK_BINDER``

    Task IDs are appended to every URL. This URL can easily be shared. To prevent a user giving out
    their task state simply by sharing a URL, a task ID is bound to a value specific to the current
    user so that only the user who started a task can continue executing it. 
    
    This setting is a method which will be called to get the value to bind the task to. It is called
    with a single argument, the current request. The default behaviour is to bind the task to the
    session ID.

Misc
===

Flow Graph Visualisation
---

If `settings.DEBUG` is `True`, then the flow graph visualization is enabled. Under the root of a flow handler, use `.flowgraph` as the path to see a graph of the actions and paths between them in the flows. This requires that the PyDot library is installed.

Eg: if a flow handler is installed under `/some/path/` then navigating to `/some/path/.flowgraph` will show the layout of the flows of that hander. 

Cleaning up expired task state in the database
---
If you are using the `DjangoStateStore` backend (which is the default), then the task state will be stored as rows in the database. Although stale tasks will not be returned, the state will stay in the database and not be deleted. To clean it up, you have several options:

- `django-admin.py cleanupflows`

   This is a command which will delete the expired state from the database. You can run it manually or as part of a cronjob.
   
- `flows.additional.celery.cleanup_task`
   
   If you are using [Celery](http://celeryproject.org/) then you can use this provided task to clean up old task state every 5 minutes.
