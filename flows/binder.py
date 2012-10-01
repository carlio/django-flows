# -*- coding: UTF-8 -*-
from django.utils.importlib import import_module

def _setup(full_class):
    idx = full_class.rindex('.')
    module_name, class_name = full_class[:idx], full_class[idx+1:]
    mod = import_module(module_name)
    clz = getattr(mod, class_name)
    return clz()

