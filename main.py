  
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
    ns, value, v_type = self.getParameters(path)
    logging.info('get: %s, %s, %s' % (ns, value, v_type))
    self.post(key, path)

  def post(self, key, path):
    if (not key):
      self.error(500)
    campaign = Campaign.get(key)
    if (not campaign):
      self.error(404)
      
    ns, value, v_type = self.getParameters(path)
    logging.info('post: %s, %s, %s' % (ns, value, v_type))
    
    self.measure(campaign, ns, value, v_type)
    
  def measure(self, campaign, ns, value, v_type):
    datum = Storage(
      namespace = ns,
      value = value,
      type = v_type,
      campaign = campaign
    )
    if (not datum.put()):
      logging.error('Datum not saved. Campaign: %s %s %s %s' % (campaign, ns, value, v_type))
      self.error(500)
    else:
      self.response.set_status(201)
  
  def getParameters(self, path):
    ns, value = util.getParts(path)
    v_type = self.request.get('type')
    if (not ns):
      self.error(500)
    if (not value and value is not 0):
      if (not v_type): # Todo, default_values_dict
        value = 1
        v_type = 'number'
    return (ns, value, v_type)
    
    
application = webapp.WSGIApplication(debug = os.environ['SERVER_SOFTWARE'].startswith('Dev'), url_mapping = [
  (r'/([^/]+)/(.*)', ActionPage),
  ('/', MainPage)
])

if __name__ == "__main__":  
    run_wsgi_app(application)