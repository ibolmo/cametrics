  
'''
Need to test for:
@see notes.md
'''

import os, util
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app

from models import *

class MainPage(webapp.RequestHandler):
    def get(self):
        print 'hi'
        
application = webapp.WSGIApplication(debug = os.environ['SERVER_SOFTWARE'].startswith('Dev'), url_mapping = [
    ('/', MainPage)
])

if __name__ == "__main__":  
    run_wsgi_app(application)
     