from django import forms
from myapp.models import Campaign

class CampaignForm (forms.ModelForm):    
    class Meta:
        model = Campaign
        exclude = ['created_on', 'organizer']