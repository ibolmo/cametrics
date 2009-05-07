from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
    
from google.appengine.ext import db
from ragendja.template import render_to_response

#from myapp.forms import PersonForm
import os, util, logging
from models import *

def list_measurements(request):
    pass #return object_list(request, Person.all(), paginate_by=10)

def about(request):
    return render_to_response(request, 'myapp/about.html')
    
def create_admin_user(request):
    user = User.get_by_key_name('admin')
    if not user or user.username != 'admin' or not (user.is_active and
            user.is_staff and user.is_superuser and
            user.check_password('admin')):
        user = User(key_name='admin', username='admin',
            email='admin@localhost', first_name='Boss', last_name='Admin',
            is_active=True, is_staff=True, is_superuser=True)
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

def measurements(request, key, path):
    if (not key):
      return HttpResponse('Invalid service usage', status = 500)
    
    ns, value = util.getParts(path)
      
    if request.method == 'GET':
        logging.info('get: %s, %s' % (ns, value))
    #elif request.method == 'POST':
        
        campaign = Campaign.get(key)
        if (not campaign):
            return HttpResponse('Campaign not found', status = 404)
          
        if ('type' not in request.POST):
            v_type = 'number'
        else:
            v_type = request.POST['type']
          
        if (v_type == 'number'):
            if (not value or not value.isdigit()):
                ns += '.%s' % value
                value = 1
        
        logging.info('post: %s, %s, %s' % (ns, value, v_type))
        
        datum = Storage(
            namespace = ns,
            value = value,
            type = v_type,
            campaign = campaign
        )
        if (not datum.put()):
            logging.error('Datum not saved. Campaign: %s %s %s %s' % (campaign, ns, value, v_type))
            return HttpResponse('Internal error when saving measurement', status = 500)
        
        return HttpResponse('Ok')
        
    return HttpResponse('Internal Error', status = 500)