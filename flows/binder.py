# -*- coding: UTF-8 -*-
from importlib import import_module
from flows import config


def session_binder(request):
    return request.session.session_key


def _setup():
    binder_path = config.FLOWS_TASK_BINDER
    module_name, attr_name = binder_path.rsplit('.', 1)
    
    mod = import_module(module_name)
    return getattr(mod, attr_name)


binder = _setup()
