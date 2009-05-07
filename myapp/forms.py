# -*- coding: utf-8 -*-
from django import forms
from ragendja.auth.models import UserTraits
from ragendja.forms import FormWithSets, FormSetField
from ragendja.auth.hybrid_models import User
from myapp.models import *

class CampaignForm (forms.ModelForm):    
    def save(self, domain_override = ""):
        return super(CampaignForm, self).save()
    
    class Meta:
        model = Campaign
        exclude = ['created_on']
        
CampaignForm = FormWithSets(CampaignForm)