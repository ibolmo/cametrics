  
'''
Need to test for:
@see notes.md
'''

import os, util
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app

from models import *

''' Generated Models

The following will eventually be generated on-the-fly and saved/retrieved from data store for each organizer
'''
class Visitor (FloatDatum):
    pass
    
class Click (FloatDatum):
    pass

class X (FloatDatum):
    pass

class Agent (StringDatum):
    pass

class MainPage(webapp.RequestHandler):
    def get(self):
        print 'hi'
        
application = webapp.WSGIApplication(debug = os.environ['SERVER_SOFTWARE'].startswith('Dev'), url_mapping = [
    ('/', MainPage)
])

if __name__ == "__main__":  
    run_wsgi_app(application)
     