  
'''
Need to test for:
@see notes.md
'''

import os
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app

class Histogram (db.Expando):
    pass
    
class HitsHistogram (Histogram):
    pass
    
class Statistics (db.Model):
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

class Datum (db.Model):
    created_at = db.DateTimeProperty(auto_now = True)
    statistics = db.ReferenceProperty()

class FloatDatum(Datum):
    value = db.FloatProperty(required = True)

class StringDatum(Datum):
    value = db.StringProperty(required = True)


# Generated/looked-up
class Vistor (FloatDatum):
    pass
    
class Click (FloatDatum):
    pass

class X (FloatDatum):
    pass

class Agent (StringDatum):
    pass


def generateModel(name, properties = {}, base = db.Model):
    return type(name, (base, ), properties)


class MainPage(webapp.RequestHandler):
    def get(self):
        print 'hi'
        
application = webapp.WSGIApplication(debug = os.environ['SERVER_SOFTWARE'].startswith('Dev'), url_mapping = [
    ('/', MainPage)
])

if __name__ == "__main__":  
    run_wsgi_app(application)
     