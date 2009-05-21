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
  status = 200
  task = TaskModel.all().get()
  if task:
    task_key = task.key()
    logging.info('Executing clean up campaign task: %s' % task_key)
    if (task.execute()):
      logging.info('Finished clean up campaign task: %s' % task_key)
      stats = 201
  return HttpResponse(status = status)
  

def get(task):
  for cls_name in globals().keys():
    if not cls_name.endswith('Task'):
      continue
    if (cls_name.startswith(task.title().replace(' ', '')):
      return globals()[cls_name].execute
  return Task.execute

class Task(object):
  LIMIT = 100  
  
  @staticmethod
  def execute(task, object):
    pass
  
  @staticmethod
  def has(object):
    return False

class DeleteHistogramTask(Task):
  @staticmethod
  def execute(task, stat):
    hists_query = Histogram.all(keys_only = True).filter('statistic =', stat)
    if (hists_query.count(limit = 1)):
      for hist in hists_query.fetch(Task.LIMIT):
        hist.delete()
    else:
      task.delete()
      logging.info('Nothing left of histograms with statistic: %s' % stat.key())
      return True

class DeleteCampaignTask(Task):  
  @staticmethod
  def execute(task, campaign):
    storage_query = Storage.all().filter('campaign =', campaign)
    if (storage_query.count(limit = 1)):
      for datum in storage_query.fetch(Task.LIMIT):
        if (Histogram.has(datum.stat) and not TaskModel.has(datum.stat)): #perhaps use a pickled dictionary instead of count queries
          if (not TaskModel(object = datum.stat, task = 'delete histogram').put()):
            logging.critical('Could not create delete histogram task for %s' % datum.stat.key())
        else:
          datum.stat.delete()
        datum.delete()
    else:
      task.delete()
      logging.info('Nothing left in storage to clean up for campaign %s' % self.object.key())
      return True