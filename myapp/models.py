from django.db.models import permalink, signals
from google.appengine.ext import db
from ragendja.dbutils import cleanup_relations
from ragendja.auth.hybrid_models import User

class Campaign(db.Model):
  title = db.StringProperty(required = True)
  description = db.StringProperty(multiline = True)
  homepage = db.StringProperty()
  owner = db.ReferenceProperty(User)
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
  
class Statistics (db.Model):
  campaign = db.ReferenceProperty(Campaign)
  namespace = db.StringProperty(required = True)
  first = db.ReferenceProperty(collection_name = "first")
  last = db.ReferenceProperty(collection_name = "last")
  hits = db.ReferenceProperty(HitsHistogram, collection_name = "hits")
  
class FloatStatistics (Statistics):
  min = db.FloatProperty()
  max = db.FloatProperty()
  mean = db.FloatProperty()
  sum = db.FloatProperty()
  # ...

class StringStatistics (Statistics):
  pass