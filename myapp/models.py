from django.db.models import signals
from google.appengine.ext import db
from ragendja.auth.hybrid_models import User
import logging

class Campaign(db.Model):
  title = db.StringProperty(required = True)
  description = db.StringProperty(multiline = True)
  homepage = db.StringProperty()
  organizer = db.ReferenceProperty(User, collection_name = 'campaigns')
  created_on = db.DateTimeProperty(auto_now_add = 1)
    
class Storage(db.Expando):
  campaign = db.ReferenceProperty(Campaign)
  namespace = db.StringProperty(required = True)
  type = db.StringProperty(required = True, choices = ('string', 'number', 'datetime'))
  created_on = db.DateTimeProperty(auto_now_add = 1)

class Histogram (db.Expando):
  pass
  
class HitsHistogram (Histogram):
  pass
  
class Statistics (db.Expando):
  campaign = db.ReferenceProperty(Campaign)
  namespace = db.StringProperty(required = True)
  first_  = db.ReferenceProperty(name=  'first', collection_name = 'first')
  last_ = db.ReferenceProperty(name = 'last', collection_name = 'last')
  hits = db.ReferenceProperty(HitsHistogram, collection_name = 'hits')
  count = db.IntegerProperty()
  
  @staticmethod
  def get_by_campaign_and_namespace(campaign, namespace):
    '''docstring for get_by_campaign_and_namespace'''
    result = Statistics.all().filter('campaign = ', campaign).filter('namespace = ', namespace).fetch(1)
    return len(result) and result[0] or None
      
  def calc_stats(self, datum):
    '''docstring for calc_stats'''
    logging.info('Statistics')
    if (not self.first_):
      self.first_ = datum
    self.last_ = datum
    if (not self.count):
      self.count = 0
    self.count += 1
    
    # self.hits
  
def calc_number_statistics(stats, datum):
    if (not hasattr(stats, 'min') or datum.value < stats.min):
      stats.min = datum.value
    if (not hasattr(stats, 'max') or datum.value > stats.max):
      stats.max = datum.value
    if (not hasattr(stats, 'sum')):
      stats.sum = 0
    stats.sum += datum.value
    if (not hasattr(stats, 'mean')):
      stats.mean = 0
    stats.mean = ((stats.mean * (stats.count - 1)) + datum.value) / stats.count

def cb_statistics(sender, **kwargs):
    '''docstring for cb_statistics'''
    logging.info('Kwargs: %s' % kwargs)
    instance = kwargs['instance'] or logging.error('No instance for cb_statistics')
    logging.info('instance type: %s, value: %s' % (instance.type, instance.value))
    
    statistic = Statistics.get_by_campaign_and_namespace(instance.campaign, instance.namespace) or Statistics(campaign = instance.campaign, namespace = instance.namespace)
    if (not statistic.is_saved()):
      statistic.save()
    statistic.calc_stats(instance)
    calc_number_statistics(statistic, instance)
    statistic.save()
    logging.info('statistic: %s' % (statistic and statistic.key(), ))
    
signals.post_save.connect(cb_statistics, sender = Storage)