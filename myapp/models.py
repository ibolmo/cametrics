from django.db.models import signals
from google.appengine.ext import db
from ragendja.auth.hybrid_models import User
import logging, util

from google.appengine.api import datastore_types
from django.utils import simplejson
                
class SerializableExpando(db.Expando):
    """Extends Expando to have json and possibly other serializations
    
    Use the class variable 'json_does_not_include' to declare properties
    that should *not* be included in json serialization.
    TODO -- Complete round-tripping
    """
    json_does_not_include = []
 
    def to_dict(self, attr_list=[]):
        def to_entity(entity):
            """Convert datastore types in entity to 
               JSON-friendly structures."""
            self._to_entity(entity)
            for skipped_property in self.__class__.json_does_not_include:
                del entity[skipped_property]
            util.replace_datastore_types(entity)
        return util.to_dict(self, attr_list, to_entity)
    
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
  json_does_not_include = ['campaign', 'namespace', 'type']
  
  campaign = db.ReferenceProperty(Campaign)
  namespace = db.StringProperty(required = True)
  type = db.StringProperty(required = True, choices = ('string', 'number', 'datetime'))
  created_on = db.DateTimeProperty(auto_now_add = 1)
  
class Statistics (SerializableExpando):
  json_does_not_include = ['campaign', 'namespace']
  
  campaign = db.ReferenceProperty(Campaign)
  namespace = db.StringProperty(required = True)
  first_  = db.ReferenceProperty(name=  'first', collection_name = 'first')
  last_ = db.ReferenceProperty(name = 'last', collection_name = 'last')
  hits = JSONProperty()
  count = db.IntegerProperty()
  
  @staticmethod
  def get_by_campaign_and_namespace(campaign, namespace):
    '''docstring for get_by_campaign_and_namespace'''
    result = Statistics.all().filter('campaign = ', campaign).filter('namespace = ', namespace).fetch(1)
    return len(result) and result[0] or None
      
  def calc_stats(self, datum):
    '''docstring for calc_stats'''
    if (not self.first_):
      self.first_ = datum
    self.last_ = datum
    
    if (not self.count):
      self.count = 0
    self.count += 1
    
    if (not self.hits):
      self.hits = {}
    key = str(datum.value) #careful
    if (key not in self.hits):
      self.hits[key] = []
    self.hits[key].append(str(datum.key()))
  
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
  stats.mean = stats.sum / stats.count

def calc_string_statistics(stats, datum):
  pass

'''
### Datetime
 - value
 - timestamp
 - statistics
    - frequency
    - day\_of\_week (histogram)
    - hour (histogram)
'''
def calc_date_statistics(stats, datum):
  pass
  
def calc_timestamp_statistics(stats, datum):
  pass

'''
### Location
 - longitude
 - latitude
 - statistics
    - first (location)
    - last (location)
    - area
    - centroid
    - boundary
    - box (histogram)
'''
def calc_location_statistics(stats, datum):
  pass
  
def calc_coordinate_statistics(stats, datum):
  pass
  
'''
### Interval
 - start (date)
 - stop (date)
 - duration (number)
 - statistics
    - first (interval)
    - last (interval)
'''
  
CALC_STATS = {
  'number': calc_number_statistics,
  'float': calc_number_statistics,
  'int': calc_number_statistics,
  'integer': calc_number_statistics,
  'long': calc_number_statistics,
  
  'string': calc_string_statistics,
  'text': calc_string_statistics,
  'str': calc_string_statistics,
  
  'date': calc_date_statistics,
  'datetime': calc_date_statistics,
  'timestamp': calc_timestamp_statistics,
  
  'location': calc_location_statistics,
  'gps': calc_location_statistics,
  'coordinate': calc_coordinate_statistics
}

def cb_statistics(sender, **kwargs):
  '''docstring for cb_statistics'''
  global calc_stats
  instance = kwargs['instance'] or logging.error('No instance for cb_statistics')
  
  statistic = Statistics.get_by_campaign_and_namespace(instance.campaign, instance.namespace) or Statistics(campaign = instance.campaign, namespace = instance.namespace)
  if (not statistic.is_saved()):
    statistic.save()
  statistic.calc_stats(instance)
  if (instance.type in calc_stats):
    logging.info('Calculating Statistics for %s' % instance.type)
    CALC_STATS.get(instance.type, lambda x,y: None)(statistic, instance)
  statistic.save()
  logging.info('statistic: %s' % (statistic and statistic.key(), ))
    
signals.post_save.connect(cb_statistics, sender = Storage)