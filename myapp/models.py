#from django.db.models import signals
from google.appengine.ext import db
import logging, util

from google.appengine.api import datastore_types
from django.utils import simplejson
import stat

class SerializableExpando(db.Expando):
  """Extends Expando to have json and possibly other serializations
  
  Use the class variable 'json_does_not_include' to declare properties
  that should *not* be included in json serialization.
  TODO -- Complete round-tripping
  """
  json_does_not_include = []

  def to_dict(self):
    """Convert datastore types in entity to JSON-friendly structures."""
    entity = {}
    self._to_entity(entity)
    for skipped_property in self.__class__.json_does_not_include:
      if skipped_property in entity:
        del entity[skipped_property]
    return entity
  
  def to_json(self):
    entity = self.to_dict()
    util.replace_datastore_types(entity)
    return simplejson.dumps(entity)

class Campaign(db.Model):
  title = db.StringProperty(required = True)
  description = db.StringProperty(multiline = True)
  homepage = db.StringProperty()
  organizer = db.ReferenceProperty(collection_name = 'campaigns')
  created_on = db.DateTimeProperty(auto_now_add = 1)
    
class Storage(SerializableExpando):
  json_does_not_include = ['campaign', 'namespace', 'type', 'prev', 'stats']
  
  campaign = db.ReferenceProperty(Campaign)
  namespace = db.StringProperty(required = True)
  type = db.StringProperty(required = True)
  created_on = db.DateTimeProperty(auto_now_add = 1)
  
  prev = db.SelfReferenceProperty(collection_name = 'previous')
  stats = db.ReferenceProperty(collection_name = 'statistics')
    
class Statistics (SerializableExpando):
  json_does_not_include = ['campaign', 'namespace']
  
  campaign = db.ReferenceProperty(Campaign)
  namespace = db.StringProperty(required = True)
  head = db.ReferenceProperty(Storage, collection_name = 'head')
  tail = db.ReferenceProperty(Storage, collection_name = 'tail')
  count = db.IntegerProperty(default = 0)
  
  @staticmethod
  def get_by_campaign_and_namespace(campaign, namespace):
    '''docstring for get_by_campaign_and_namespace'''
    return Statistics.all().filter('campaign = ', campaign).filter('namespace = ', namespace).get()
    
  def to_dict(self):
    entity = super(Statistics, self).to_dict()
    
    for hist in Histogram.all().filter('statistic =', self):
      if (entity.get(hist.name) is None):
        entity[hist.name] = {}
      entity[hist.name][hist.index] = hist.count
    return entity

class Histogram(SerializableExpando):
  json_does_not_include = ['statistic', 'name']
  
  statistic = db.ReferenceProperty(Statistics, collection_name = 'statistic')
  name = db.StringProperty(required = True)
  index = db.StringProperty(required = True)
  count = db.IntegerProperty(default = 0)

  @staticmethod
  def has(stat):
    return Histogram.all(keys_only = True).filter('statistic =', stat).count(1)

def cb_prepare_datum(sender, **kwargs):
  datum = kwargs.get('instance')
  if (not datum):
    return logging.error('No datum for cb_prepare_datum')
    
  statistic = Statistics.get_by_campaign_and_namespace(datum.campaign, datum.namespace) or Statistics(campaign = datum.campaign, namespace = datum.namespace)
  if (not statistic.is_saved()):
    statistic.save()
  datum.stats = statistic
  stat.get(datum.type).prepare(datum)
      
def cb_calc_statistic(sender, **kwargs):
  datum = kwargs.get('instance')
  if (not datum):
    return logging.error('No datum for cb_statistics')
  
  if (hasattr(datum, '_invalid')):
    logging.debug('Datum (%s) is an invalid' % datum.key())
    return datum.delete()
  
  if (stat.get(datum.type).calculate(datum) is not False):
    datum.stats.save()
    
#signals.pre_save.connect(cb_prepare_datum, sender = Storage)
#signals.post_save.connect(cb_calc_statistic, sender = Storage)

class TaskModel(db.Expando):
  object = db.ReferenceProperty(required = True)
  task = db.StringProperty(required = True)
  
  def execute(self):
     obj = self.properties()['object'].get_value_for_datastore(self)
     import tasks
     return tasks.get(self.task)(self, obj)
  
  @staticmethod
  def has(object):
    return TaskModel.all(keys_only = True).filter('object =', object).count(1)

  
def cleanup_relations(sender, **kwargs):
  campaign = kwargs.get('instance')
  if (not TaskModel(object = campaign, task = 'delete campaign').put()):
    logging.critical('Could not schedule a DELETE Campaign Task for Campaign (%s)' % campaign)
  
#signals.pre_delete.connect(cleanup_relations, sender = Campaign)