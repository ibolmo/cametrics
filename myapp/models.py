import logging, util

from google.appengine.ext import db
from django.utils import simplejson

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
    
  @classmethod
  def get_by_key_name_or_insert(cls, key, **kwds):
    model = cls.get_by_key_name(key)
    if (model is None):
        model = cls.get_or_insert(key, **kwds)
    return model

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
  json_does_not_include = ['campaign', 'namespace', 'histograms']
  
  campaign = db.ReferenceProperty(Campaign)
  namespace = db.StringProperty(required = True)
  #head = db.ReferenceProperty(Storage, collection_name = 'head')
  #tail = db.ReferenceProperty(Storage, collection_name = 'tail')
  count = db.IntegerProperty(default = 0)
  histograms = db.StringListProperty()
  
  @staticmethod
  def get_by_campaign_and_namespace(campaign, namespace):
    return Statistics.get_by_key_name('%s.%s' % (campaign, namespace))
    
  def __getattr__(self, key):
    if key in self.histograms:
      entity = {}
      for bucket in Histogram.all().filter('statistic =', self).filter('name =', key):
        entity[bucket.index] = bucket.count
      return entity
    else:
      return super(Statistics, self).__getattr__(key)
    
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