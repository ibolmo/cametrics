# -*- coding: utf-8 -*-
from django import forms
from ragendja.auth.models import UserTraits
from ragendja.forms import FormWithSets, FormSetField
from ragendja.auth.hybrid_models import User
from myapp.models import *

class CampaignForm (forms.ModelForm):    
    class Meta:
        model = Campaign
        exclude = ['created_on', 'owner']