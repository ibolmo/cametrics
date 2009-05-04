  
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
    ns, value = self.getParameters(path)
    logging.info('get: %s, %s' % (ns, value))
    self.post(key, path)

  def post(self, key, path):
    ns, value = self.getParameters(path)
    logging.info('post: %s, %s' % (ns, value))
  
  def getParameters(self, path):
    ns, value = util.getParts(path)
    if (not ns):
      self.error(500)
    if (not value and value is not 0):
      if (not self.request.get('type')):
        value = 1
    return (ns, value)
    
    
application = webapp.WSGIApplication(debug = os.environ['SERVER_SOFTWARE'].startswith('Dev'), url_mapping = [
  (r'/([^/]+)/(.*)', ActionPage),
  ('/', MainPage)
])

if __name__ == "__main__":  
    run_wsgi_app(application)