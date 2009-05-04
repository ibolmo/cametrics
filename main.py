  
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
    self.response.out.write('Welcome')
        
class ActionPage(webapp.RequestHandler):
  def get(self, key, path):
    logging.info('get: %s, %s' % (key, path))
    self.post(key, path)

  def post(self, key, path):
    #ns, value = util.getParts(path)
    #if (not ns or not value and value is not 0):
    #  this.error(500)
    
    logging.info('post: %s, %s' % (key, path))
    
application = webapp.WSGIApplication(debug = os.environ['SERVER_SOFTWARE'].startswith('Dev'), url_mapping = [
  (r'/([^/]+)/(.*)', ActionPage),
  ('/', MainPage)
])

if __name__ == "__main__":  
    run_wsgi_app(application)