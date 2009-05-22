from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Message
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, update_object, redirect

from google.appengine.ext import db
from ragendja.template import render_to_response

import os, util, logging, stat, renderer
from myapp.forms import CampaignForm
from myapp.models import *

from django.contrib.auth.decorators import login_required

def list_measurements(request):
  pass #return object_list(request, Person.all(), paginate_by=10)

def about(request):
  return render_to_response(request, 'myapp/about.html')

def create_admin_user(request):
  user = User.get_by_key_name('admin')
  if not user or user.username != 'admin' or not (user.is_active and user.is_staff and user.is_superuser and user.check_password('admin')):
    user = User(key_name='admin', username='admin', email='admin@localhost', first_name='Boss', last_name='Admin', is_active=True, is_staff=True, is_superuser=True)
    user.set_password('admin')
    user.put()
  return render_to_response(request, 'myapp/admin_created.html')

def create_new_user(request):
  form = UserCreationForm()
  # if form was submitted, bind form instance.
  if request.method == 'POST':
    form = UserCreationForm(request.POST)
    if form.is_valid():
      user = form.save(commit=False)
      # user must be active for login to work
      user.is_active = True
      user.put()
      return HttpResponseRedirect('/login')
  return render_to_response(request, 'myapp/user_create_form.html', {'form': form, 'heading': 'Register' })

def measurements(request, key, path, format):
  logging.debug('measurements::path = %s' % path)
  logging.debug('measurements::format = %s' % format)
  if (not key):
    return HttpResponse('Invalid service usage')
  
  campaign = Campaign.get(key)
  if (not campaign):
    return HttpResponse('Campaign not found')
  
  ns = path.strip('/').replace('/', '.')
  
  if request.method == 'GET':
    format = format or request.GET.get('format', 'json')
    ns, data_path = util.getParts(ns)
    data = Storage.all().filter('campaign = ', campaign).filter('namespace = ', ns).fetch(1000) # todo, paginator
    stats = Statistics.get_by_campaign_and_namespace(campaign, ns)
    return renderer.get(format)(request, format, data, stats, data_path)
  elif request.method == 'POST':   
    value = request.POST.get('value')
    kind = request.POST.get('type', 'number')
    logging.debug('POST | value: %s | kind: %s' % (value, kind))
    datum = Storage(campaign = campaign, namespace = ns, type = kind, value = value)
    if (not datum.put()):
      logging.error('Datum not saved. Campaign: %s %s %s %s' % (campaign, ns, value, kind))
      return HttpResponse('Internal error when saving measurement', status = 500)
    return HttpResponse('Ok', status = 201)
  elif request.method == 'DELETE':
    return HttpResponse('Not yet supported, please contact admin.', status = 304)

  return HttpResponse('Internal Error', status = 500)

@login_required
def list_campaigns(request):
  return object_list(request, Campaign.all().filter('organizer =', request.user), paginate_by=10)

@login_required
def show_campaign(request, key):
  return object_detail(request, Campaign.all().filter('organizer =', request.user), key)

@login_required
def add_campaign(request):
  if request.method == 'POST':
    form = CampaignForm(request.POST, request.FILES)
    if form.is_valid():
      new_object = form.save(commit = False)
      new_object.organizer = request.user
      if (new_object.put()):
        if request.user.is_authenticated():
          Message(user = request.user, message= "The campaign was created successfully.").put()
        return redirect(reverse('myapp.views.show_campaign', kwargs = dict(key = '%(key)s')), new_object)
  else:
    form = CampaignForm()
  return render_to_response(request, 'myapp/campaign_form.html', {'form': form})

@login_required
def edit_campaign(request, key):
  return update_object(request, object_id = key, form_class = CampaignForm)
  
@login_required
def delete_campaign(request, key):
    return delete_object(request, Campaign, object_id = key, post_delete_redirect = reverse('myapp.views.list_campaigns'))
    
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