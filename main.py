  
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
  
  ''' getParameters
  Parses and has necessary logic for creating namespace and value pair with default value and type
  
  Input:
    path - The path needed to be parsed into namespace and value pair
    
  Returns:
    (tuple) ns, value, v_type - namespace, value, and type of the value posted/requested
  '''
  def getParameters(self, path):
    ns, value = util.getParts(path)
    if (not ns):
      self.error(500)
      
    v_type = self.request.get('type')
    if (not v_type):
      v_type = 'number'
      if (not value and value is not 0):
        value = 1
      elif (not value.isdigit()):
        ns += '.%s' % value
        value = 1
        
    else:
      # Todo, check value and grab default for non-numeric input
      self.error(500)
      
    return (ns, value, v_type)
    
    
application = webapp.WSGIApplication(debug = os.environ['SERVER_SOFTWARE'].startswith('Dev'), url_mapping = [
  (r'/([^/]+)/(.*)', ActionPage),
  ('/', MainPage)
])

if __name__ == "__main__":  
    run_wsgi_app(application)