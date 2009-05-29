import logging
from google.appengine.ext import db
from models import Storage, Histogram, TaskModel

def get(task):
  for cls_name in globals().keys():
    if not cls_name.endswith('Task'):
      continue
    if (cls_name.startswith(task.title().replace(' ', ''))):
      return globals()[cls_name].execute
  return lambda x,y: None


class DeleteHistogramTask(object):
  @staticmethod
  def execute(task, stat):
    hists_query = Histogram.all(keys_only = True).filter('statistic =', stat)
    if (hists_query.count(limit = 1)):
      for hist in hists_query.fetch(100):
        db.delete(hist)
    else:
      logging.info('Nothing left of histograms with statistic: %s' % stat)
      db.delete(stat)
      task.delete()
      return True

class DeleteCampaignTask(object):  
  @staticmethod
  def execute(task, campaign):
    storage_query = Storage.all().filter('campaign =', campaign)
    if (storage_query.count(limit = 1)):
      for datum in storage_query.fetch(100):
        logging.info('checking for stats: %s' % datum.stats.key())
        if (Histogram.has(datum.stats) and not TaskModel.has(datum.stats)): #perhaps use a pickled dictionary instead of count queries
          if (not TaskModel(object = datum.stats, task = 'delete histogram').put()):
            logging.critical('Could not create delete histogram task for %s' % datum.stats)
        else:
          datum.stat.delete()
        datum.delete()
    else:
      task.delete()
      logging.info('Nothing left in storage to clean up for campaign %s' % campaign)
      return True