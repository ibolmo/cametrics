import re, logging
from google.appengine.ext import db

def generateModel(name, properties = {}, base = db.Model):
  return type(name, (base, ), properties)

special_keys = re.compile(r'\.((?:stats|values).*)')

def getParts(ns):
  x = special_keys.split(ns)
  return len(x) and x[0] or None, len(x) > 1 and x[1] or None
  
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
            return { 'nickname': value.nickname(), 
                     'email': value.email() }
        else:
            return None
 
    for key, value in entity.iteritems():
        if isinstance(value, list):
            new_list = []
            for item in value:
                new_value = get_replacement(item)
                new_list.append(new_value or item)
            entity[key] = new_list
        else:
            new_value = get_replacement(value)
            if new_value:
                entity[key] = new_value