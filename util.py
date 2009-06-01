import re, logging
from google.appengine.ext import db

def generateModel(name, properties = {}, base = db.Model):
  return type(name, (base, ), properties)

def dictcomp(obj, without = []):
  return dict((k, v) for k, v in obj.iteritems() if k not in without)

special_keys = re.compile(r'\.((?:stats|values).*)')

def getParts(ns):
  x = special_keys.split(ns)
  return len(x) and x[0] or '', len(x) > 1 and x[1] or ''
  
# From: http://github.com/DocSavage/bloog/blob/346e5fb7c1fd87259dc79f2c4ae852badb6f2b79/models/__init__.py
import datetime
from google.appengine.api import users, datastore_types

def to_dict(model_obj, attr_list, init_dict_func=None):
    """Converts Model properties into various formats.
 
    Supply a init_dict_func function that populates a
    dictionary with values.  In the case of db.Model, this
    would be something like _to_entity().  You may also
    designate more complex properties in attr_list, like
      "counter.count"
    Each object in the chain will be retrieved.  In the
    example above, the counter object will be retrieved
    from model_obj's properties.  And then counter.count
    will be retrieved.  The value returned will have a
    key set to the last name in the chain, e.g. 'count' 
    in the above example.
    """
    values = {}
    init_dict_func(values)
    for token in attr_list:
        elems = token.split('.')
        value = getattr(model_obj, elems[0])
        for elem in elems[1:]:
            value = getattr(value, elem)
        values[elems[-1]] = value
    return values
 
# Format for conversion of datetime to JSON
DATE_FORMAT = "%Y-%m-%d" 
TIME_FORMAT = "%H:%M:%S"

def replace_datastore_types(entity):
  """Replaces any datastore types in a dictionary with standard types.
  
  Passed-in entities are assumed to be dictionaries with values that
  can be at most a single list level.  These transformations are made:
    datetime.datetime      -> string
    db.Key                 -> key hash suitable for regenerating key
    users.User             -> dict with 'nickname' and 'email'
  TODO -- GeoPt when needed
  """    
  def get_replacement(value):
    if isinstance(value, datetime.datetime):
      return value.strftime("%s %s" % (DATE_FORMAT, TIME_FORMAT))
    elif isinstance(value, datetime.date):
      return value.strftime(DATE_FORMAT)
    elif isinstance(value, datetime.time):
      return value.strftime(TIME_FORMAT)
    elif isinstance(value, datastore_types.Key):
      return str(value)
    elif isinstance(value, users.User):
      return { 'nickname': value.nickname(), 'email': value.email() }
  for key, value in entity.iteritems():
    if isinstance(value, list):
      entity[key] = [isinstance(item, (datetime.datetime, datetime.date, datetime.time, datastore_types.Key, users.User)) and get_replacement(item) or item for item in values]
    else:
      entity[key] = isinstance(value, (datetime.datetime, datetime.date, datetime.time, datastore_types.Key, users.User)) and get_replacement(value) or value
  return entity

def getattr_by_path(obj, attr, *default):
  """Like getattr(), but can go down a hierarchy like 'attr.subattr'"""
  value = obj
  for i, part in enumerate(attr.split('.')):
    if isinstance(value, dict):
      if not value.has_key(part) and len(default) > i:
        return default[i]
      value = value.get(part)
      if callable(value):
        value = value()
    else:
      if not hasattr(value, part) and len(default) > i:
        return default[i]
      try:
        value = getattr(value, part)
      except:
        value = None
      if callable(value):
        value = value()
  return value



class Mapper(object):
  # Subclasses should replace this with a model class (eg, model.Person).
  KIND = None
 
  # Subclasses can replace this with a list of (property, value) tuples to filter by.
  FILTERS = []
  
  def map(self, entity):
    """Updates a single entity.
   
    Implementers should return a tuple containing two iterables (to_update, to_delete).
    """
    return ([], [])
 
  def get_query(self):
    """Returns a query over the specified kind, with any appropriate filters applied."""
    q = self.KIND.all()
    for prop, value in self.FILTERS:
      q.filter("%s =" % prop, value)
    q.order("__key__")
    return q
 
  def run(self, batch_size=100):
    """Executes the map procedure over all matching entities."""
    q = self.get_query()
    entities = q.fetch(batch_size)
    while entities:
      to_put = []
      to_delete = []
      for entity in entities:
        map_updates, map_deletes = self.map(entity)
        to_put.extend(map_updates)
        to_delete.extend(map_deletes)
      if to_put:
        db.put(to_put)
      if to_delete:
        db.delete(to_delete)
      q = self.get_query()
      q.filter("__key__ >", entities[-1].key())
      entities = q.fetch(batch_size)
 
class FixNamespace(Mapper):
  def __init__(self, kind, filters = None):
    self.KIND = kind
    if filters:
      self.FILTERS = filters
      
  def map(self, entity):
    if hasattr(entity, 'namespace'):
      if '/' in entity.namespace:
        entity.namespace = entity.namespace.strip('/').replace('/', '.')
        return ([entity], [])
    return ([], [])

import csv

class Export(Mapper):
  def __init__(self, filename, kind, attrs, filters = None):
    self.KIND = kind
    if filters:
      self.FILTERS = filters
    self.ATTRS = attrs
    self.writer = csv.writer(open(filename, 'w'))
    self.writer.writerow(self.ATTRS)
    
  def map(self, entity):
    self.writer.writerow([getattr(entity, attr) for attr in self.ATTRS])
    return ([], [])
    
class Delete(Mapper):
  def __init__(self, kind, filters = None):
    self.KIND = kind
    if filters:
      self.FILTERS = filters
  
  def map(self, entity):
    return ([], [entity])