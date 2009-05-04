  
'''
Need to test for:
@see notes.md
'''

import os, util, logging
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app

from models import *

class MainPage(webapp.RequestHandler):
  def get(self):
    print 'hi'
        
class ActionPage(webapp.RequestHandler):
  def get(self, key, path):
    self.response.out.write('get: %s, %s' % (key, path))

  def post(self, key, path):
    self.response.out.write('post: %s, %s' % (key, path))
    
application = webapp.WSGIApplication(debug = os.environ['SERVER_SOFTWARE'].startswith('Dev'), url_mapping = [
  (r'/([^/]+)/(.*)', ActionPage),
  ('/', MainPage)
])

if __name__ == "__main__":  
    run_wsgi_app(application)