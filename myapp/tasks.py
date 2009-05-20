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
def clean_up_campaigns(request):
  if (not request.META.get('X-AppEngine-Cron')):
    logging.warn('Tried to execute Cron job insecurely/improperly')
    #return HttpResponse(status = 404)
  status = 200
  for task in DeleteCampaignTask.all():
    task_key = str(task.key())
    logging.info('Executing clean up campaign task: %s' % task_key)
    if (task.execute()):
      logging.info('Finished clean up campaign task: %s' % task_key)
      stats = 201
  return HttpResponse(status = status)