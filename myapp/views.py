from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Message
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, update_object, redirect
from django.utils import simplejson
from google.appengine.ext import db
from ragendja.template import render_to_response

import os, util, logging
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

mimetypes = {
  'json': 'text/json', #'application/json',
  'html': 'text/html',
  'csv': 'text/csv',
  'plain': 'text/plain'
}

def render_json(data, stats):
  def to_dict(datum):
    return datum.to_dict()
  return simplejson.dumps({
    'type': len(data) and data[0].type or None,
    'values': map(to_dict, data),
    'stats': map(to_dict, stats)
  })

def measurements(request, key, path, format):
  if (not key):
    return HttpResponse('Invalid service usage')
  
  ns, value = util.getParts(path)
  campaign = Campaign.get(key)
  if (not campaign):
    return HttpResponse('Campaign not found')
  
  if request.method == 'GET':
    logging.info('get: %s, %s' % (ns, value))
    data = Storage.all().filter('campaign = ', campaign).filter('namespace = ', ns).fetch(1000) # todo, paginator
    stats = Statistics.all().filter('campaign = ', campaign).filter('namespace = ', ns).fetch(1)
    format = request.GET.get('format') or format or 'json'
    renderer = globals().get('render_%s' % format)
    return renderer and render_to_response(request, 'myapp/get_data.%s' % format, {'data': renderer(data, stats)}, mimetype = mimetypes.get(format, 'text/plain')) \
        or HttpResponse('Unsupported format: %s' % format, status = 500)
  elif request.method == 'POST':    
    v_type = request.POST.get('type', 'number')
    if (v_type == 'number'):
      if (not value or not value.isdigit()):
        value = 1
      else:
        value = float(value)
    logging.info('post: %s, %s, %s' % (ns, value, v_type))
    
    datum = Storage(namespace = ns, value = value, type = v_type, campaign = campaign)
    if (not datum.put()):
      logging.error('Datum not saved. Campaign: %s %s %s %s' % (campaign, ns, value, v_type))
      return HttpResponse('Internal error when saving measurement', status = 500)
    return HttpResponse('Ok')
    
  return HttpResponse('Internal Error', status = 500)

@login_required
def list_campaigns(request):
  return object_list(request, Campaign.all(), paginate_by=10)

@login_required
def show_campaign(request, key):
  return object_detail(request, Campaign.all(), key)

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