from django.db.models import signals
from google.appengine.ext import db
from ragendja.auth.hybrid_models import User
import logging, util

from google.appengine.api import datastore_types
from django.utils import simplejson
import stat, tasks

class SerializableExpando(db.Expando):
  """Extends Expando to have json and possibly other serializations
  
  Use the class variable 'json_does_not_include' to declare properties
  that should *not* be included in json serialization.
  TODO -- Complete round-tripping
  """
  json_does_not_include = []
  
  def to_entity(self, entity):
    """Convert datastore types in entity to JSON-friendly structures."""
    self._to_entity(entity)
    for skipped_property in self.__class__.json_does_not_include:
      try:
        del entity[skipped_property]
      except:
        pass
    util.replace_datastore_types(entity)

  def to_dict(self, attr_list=[]):
    return util.to_dict(self, attr_list, self.to_entity)
  
  def to_json(self, attr_list=[]):
    return simplejson.dumps(self.to_dict(attr_list))

class JSONProperty(db.Property):
    def get_value_for_datastore(self, model_instance):
        value = super(JSONProperty, self).get_value_for_datastore(model_instance)
        return db.Text(self._deflate(value))
    def validate(self, value):
        return self._inflate(value)
    def make_value_from_datastore(self, value):
        return self._inflate(value)
    def _inflate(self, value):
        if value is None:
            return {}
        if isinstance(value, unicode) or isinstance(value, str):
            return simplejson.loads(value)
        return value
    def _deflate(self, value):
        return simplejson.dumps(value)
    data_type = datastore_types.Text

class Campaign(db.Model):
  title = db.StringProperty(required = True)
  description = db.StringProperty(multiline = True)
  homepage = db.StringProperty()
  organizer = db.ReferenceProperty(User, collection_name = 'campaigns')
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
  head = db.ReferenceProperty(Storage, collection_name = 'head')
  tail = db.ReferenceProperty(Storage, collection_name = 'tail')
  histograms = db.StringListProperty()
  count = db.IntegerProperty()
  
  @staticmethod
  def get_by_campaign_and_namespace(campaign, namespace):
    '''docstring for get_by_campaign_and_namespace'''
    return Statistics.all().filter('campaign = ', campaign).filter('namespace = ', namespace).get()
    
  def to_entity(self, entity):
    super(Statistics, self).to_entity(entity)
    
    for histogram in self.histograms:
      hists = Histogram.all().filter('statistic =', self).filter('name =', histogram).fetch(1000) #pagination
      hist_dict = {}
      for h in hists:
        if h.index not in hist_dict:
          hist_dict[h.index] = []
        hist_dict[h.index].append(str(h.datum.key()))
      entity[histogram] = hist_dict

class Histogram(SerializableExpando):
  json_does_not_include = ['statistic', 'name']
  
  statistic = db.ReferenceProperty(Statistics, collection_name = 'statistic')
  name = db.StringProperty(required = True)
  index = db.StringProperty()
  datum = db.ReferenceProperty(Storage, collection_name = 'datum')

      
  @staticmethod
  def has(stat):
    return Histogram.all(keys_only = True).filter(statistic = stat).count(1)

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
    
signals.pre_save.connect(cb_prepare_datum, sender = Storage)
signals.post_save.connect(cb_calc_statistic, sender = Storage)

class TaskModel(db.Expando):
  object = db.ReferenceProperty(required = True)
  task = db.StringProperty(required = True)
  
  def execute(self):
     obj = self.properties()['object'].get_value_for_datastore(self)
     return tasks.get(self.task)(self, obj)
  
  @staticmethod
  def has(object):
    return TaskModel.all(keys_only = True).filter('object =', object).count(1)

  
def cleanup_relations(sender, **kwargs):
  campaign = kwargs.get('instance')
  if (not TaskModel(object = campaign, task = 'delete campaign').put()):
    logging.critical('Could not schedule a DELETE Campaign Task for Campaign (%s)' % campaign)
  
signals.pre_delete.connect(cleanup_relations, sender = Campaign)