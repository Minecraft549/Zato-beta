# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

# Django
from django import forms

# ################################################################################################################################

ACCESS_TYPE_CHOICES = [
    ('publisher', 'Publisher'),
    ('subscriber', 'Subscriber'),
    ('publisher-subscriber', 'Publisher & Subscriber')
]

# ################################################################################################################################

class CreateForm(forms.Form):
    sec_base_id = forms.ChoiceField(widget=forms.Select(attrs={'class':'required', 'style':'width:50%'}))
    access_type = forms.ChoiceField(widget=forms.Select(attrs={'class':'required', 'style':'width:50%'}))

    def __init__(self, sec_base_choices=None, *args, **kwargs):
        super(CreateForm, self).__init__(*args, **kwargs)
        self.fields['access_type'].choices = ACCESS_TYPE_CHOICES
        # Security definitions will be populated via AJAX
        self.fields['sec_base_id'].choices = []

# ################################################################################################################################

class EditForm(CreateForm):
    id = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, sec_base_choices=None, *args, **kwargs):
        super(EditForm, self).__init__(sec_base_choices, *args, **kwargs)

# ################################################################################################################################
