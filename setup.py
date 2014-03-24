# -*- coding: UTF-8 -*-
from distutils.core import setup
from setuptools import find_packages
import time


_version = "1.2"
_packages = find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "example"])
    
# common dependencies
_install_requires = [
            'django>=1.4,<1.7',
       ]

_short_description = "django-flows keeps state and position in complicated flows of logic, allowing optional " \
                     "branches and complicated paths through a series of individual user actions."
_long_description = """
django-flows can best be described as 'wizards on steroids'. Its purpose is to keep state and position
in complicated flows of logic, allowing optional branches and complicated paths through a series of
individual user actions.

django-flows makes it possible to specify subsections of functionality and group them together later.
It recognises that, at the core, there are several user actions such as logging in, or entering a credit
card number, and that the web application needs to group these actions in such a way that all state
required to make a purchase, for example, is obtained. It also seeks to make these actions reusable,
and to group related actions together into larger 'user flows'.
"""



setup( name='django-flows',
       url='https://github.com/carlio/django-flows',
       author='Carl Crowder',
       author_email='django-flows@carlcrowder.com',
       description=_short_description,
       long_description=_long_description,
       version=_version,
       packages=_packages,
       install_requires=_install_requires,
       license='BSD',
       keywords = "django",
       )
