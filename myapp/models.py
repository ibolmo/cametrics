from django.db.models import signals
from google.appengine.ext import db
from ragendja.auth.hybrid_models import User
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
  histograms = db.StringListProperty()
  count = db.IntegerProperty()
  
  @staticmethod
  def get_by_campaign_and_namespace(campaign, namespace):
    '''docstring for get_by_campaign_and_namespace'''
    result = Statistics.all().filter('campaign = ', campaign).filter('namespace = ', namespace).fetch(1)
    return len(result) and result[0] or None

def cb_statistics(sender, **kwargs):
  '''docstring for cb_statistics'''
  instance = kwargs.get('instance')
  if (not instance):
    return logging.error('No instance for cb_statistics')
  
  statistic = Statistics.get_by_campaign_and_namespace(instance.campaign, instance.namespace) or Statistics(campaign = instance.campaign, namespace = instance.namespace)
  if (not statistic.is_saved()):  # todo, remove this
    statistic.save()              #
  stat.get(instance.type).calculate(statistic, instance)
  statistic.save()
  logging.info('statistic: %s' % (statistic and statistic.key(), ))
    
signals.post_save.connect(cb_statistics, sender = Storage)

class Histogram(SerializableExpando):
  statistic = db.ReferenceProperty(Statistics, collection_name = 'statistic')
  name = db.StringProperty(required = True)
  index = db.StringProperty()
  datum = db.ReferenceProperty(Storage, collection_name = 'datum')

