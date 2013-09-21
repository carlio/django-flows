# -*- coding: UTF-8 -*-
from __future__ import absolute_imports
from flows.components import Scaffold, Action
from django import forms
from django.http import HttpResponseForbidden

class LoginForm(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(max_length=30)
    

class LoginOrRegister(Action):
    url = '^login$'
    form_class = LoginForm
    
    def form_valid(self, form):
        return Action.form_valid(self, form)



class EnsureLoggedOut(object):
    def process(self, request, component):
        if request.user.is_authenticated():
            return HttpResponseForbidden()

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(max_length=30)
    password_repeat = forms.CharField(max_length=30)
    
class RegisterNewUser(Action):
    form_class = RegisterForm
    preconditions = [ EnsureLoggedOut ]


class GetAuthenticatedUser(Scaffold):
    action_set = [LoginOrRegister, RegisterNewUser]
    
