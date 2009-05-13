from django.db.models import signals
from google.appengine.ext import db
from ragendja.auth.hybrid_models import User
import logging, util

from google.appengine.api import datastore_types
from django.utils import simplejson

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

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
    key = str(datum.value) # careful
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

def calc_date_statistics(stats, datum):
  import datetime
  if (datum.type == 'timestamp'):
    try:
      datum.timestamp = float(datum.value)
    except TypeError:
      return logging.critical('Could not convert string timestamp (%s) into integer' % datum.value)
    try:
      datum.datetime = datetime.datetime.fromtimestamp(datum.timestamp)
    except ValueError:
      return logging.critical('Could not datetime.fromtimestamp(%s)' % datum.timestamp)
  elif ('date' in datum.type):
    try:
      datum.datetime = datetime.datetime.strptime(datum.value, DATETIME_FORMAT) # careful
    except ValueError:
      return logging.critical('Could not datetime.strptime parse: %s' % datum.value)
    
    import time
    try:
      datum.timestamp = time.mktime(datum.datetime.timetuple())
    except ValueError, OverflowError:
      return logging.critical('Could not time.mktime(%s)' % datum.datetime.timetuple())
  else:
    return logging.critical('Unexpected type: %s for calc_date_statistics' % datum.type)
  
  timetuple = datum.datetime.timetuple()
  logging.info('Adding to the following buckets: %s' % timetuple)
  for i, bucket in enumerate(['year%s', 'month%s', 'day%s', 'hour%s', 'minute%s', 'second%s', 'weekday%s', 'day%s_of_the_year']):
    attr = bucket % 's'
    if (not hasattr(stats, attr)):
      stats[attr] = {}
    key = timetuple[i]
    if (key not in stats[attr]):
      stats[attr][key] = []
    stats[attr][key].append(str(datum.key()))

'''
### Location
 - longitude
 - latitude
 - statistics
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
  - 
'''
def calc_interval_statistics(stats, datum):
  pass
  
CALC_STATS = {
  'off': lambda stats, datum: None,
  'none': lambda stats, datum: None,

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
  'timestamp': calc_date_statistics,
  
  'location': calc_location_statistics,
  'gps': calc_location_statistics,
  'coordinate': calc_coordinate_statistics
}

def cb_statistics(sender, **kwargs):
  '''docstring for cb_statistics'''
  instance = kwargs.get('instance')
  if (not instance):
    return logging.error('No instance for cb_statistics')
  
  statistic = Statistics.get_by_campaign_and_namespace(instance.campaign, instance.namespace) or Statistics(campaign = instance.campaign, namespace = instance.namespace)
  if (not statistic.is_saved()):  # todo, remove this
    statistic.save()              #
    
  if (instance.type is not 'off' or instance.type is not 'none'):
    statistic.calc_stats(instance)
  else:
    logging.info('Statistics off for datum.key(%s)' % instance.key())
    
  if (instance.type in CALC_STATS):
    CALC_STATS[instance.type](statistic, instance)
  else:
    logging.warning('No statistics for type %s' % instance.type)
  
  statistic.save()
  logging.info('statistic: %s' % (statistic and statistic.key(), ))
    
signals.post_save.connect(cb_statistics, sender = Storage)