from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, update_object, redirect

from ragendja.template import render_to_response

import logging, renderer
from forms import CampaignForm
from models import Campaign, TaskModel

from django.contrib.auth.decorators import login_required

@login_required
def list_campaigns(request):
  return object_list(request, Campaign.all().filter('organizer =', request.user), paginate_by = 10, template_name = 'campaign_list.html')

@login_required
def show_campaign(request, key):
  return object_detail(request, Campaign.all().filter('organizer =', request.user), key, template_name = 'campaign_detail.html')

@login_required
def add_campaign(request):
  if request.method == 'POST':
    form = CampaignForm(request.POST, request.FILES)
    if form.is_valid():
      campaign = form.save(commit = False)
      campaign.organizer = request.user.key()
      if (campaign.put()):
        return redirect(reverse('myapp.views.show_campaign', kwargs = dict(key = '%(key)s')), campaign)
  else:
    form = CampaignForm()
  return render_to_response(request, 'campaign_form.html', {'form': form})

@login_required
def edit_campaign(request, key):
  return update_object(request, object_id = key, form_class = CampaignForm, template_name = 'campaign_form.html')
  
@login_required
def delete_campaign(request, key):
    return delete_object(request, Campaign, object_id = key, post_delete_redirect = reverse('myapp.views.list_campaigns'), template_name = 'campaign_confirm_delete.html')
    
def clean_up_campaigns(request):
  status = 200
  task = TaskModel.all().get()
  if task:
    task_key = task.key()
    logging.info('Executing clean up campaign task: %s' % task_key)
    if (task.execute()):
      logging.info('Finished clean up campaign task: %s' % task_key)
      stats = 201
  return HttpResponse(status = status)