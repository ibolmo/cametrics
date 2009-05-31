import os, logging
logging.getLogger().setLevel(logging.DEBUG)

from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app

from django.utils import simplejson
from myapp.models import Campaign, Storage, Statistics

import util
import myapp.stat as stat
import myapp.renderer as renderer
 
_Stats = {}

class MainPage(webapp.RequestHandler):
  def get(self, key, path, format):
    if (not key):
      return self.error(500)
    
    self.campaign = Campaign.all(keys_only = True).filter('__key__ = ', db.Key(key)).get()
    if (not self.campaign):
      logging.warning('No campaign (%s) found.' % key)
      return self.error(404)
    
    self.format = format or self.request.get('format', 'json')
    self.namespace, path = util.getParts((path or '').strip('/').replace('/', '.'))
  
    logging.debug("%s, %s, %s; %s" % (key, self.namespace, self.format, path))
    helper = renderer.get(self.format)
    if path.startswith('values'): # this could be automated
      return helper.render_values(self, path)
    elif path.startswith('stats'):
      return helper.render_stats(self, path)
    helper.render(self)

  def post(self, key, path, format):
    if (not key):
      return self.error(500)
    
    self.campaign = Campaign.all(keys_only = True).filter('__key__ = ', db.Key(key)).get()
    if (not self.campaign):
      logging.warning('No campaign (%s) found.' % key)
      return self.error(404)
      
    logging.debug("%s, %s, %s" % (key, path, format))
    
    models = []
    error = False
    if 'bulk' in self.request.get('type'):
      data = simplejson.loads(self.request.get('data') or '[]')  #todo remove need for loads
      for datum in data:
        ns = datum.get('namespace')
        if ns:
          models.append(create_datum(self.campaign, ns, datum))
    elif path:
        models.append(create_datum(self.campaign, path, self.request))
    
    models += _Stats.values() + stat._Hists.values()
    send_to_datastore(models)
    self.response.set_status(error and 304 or 201)

def send_to_datastore(models):
  lm = len(models)    
  if lm:
    try:
      db.put(models);
      logging.info('::STATS:: db.put(%s)' % lm)
    except:
      logging.warning('Could not save whole set')
      send_to_datastore(models[:lm / 2])
      send_to_datastore(models[lm / 2:])

def create_datum(campaign, ns, obj = {}):
  ns = ns.strip('/').replace('/', '.')    
  value = obj.get('value')
  kind = obj.get('type', 'number')
    
  datum = Storage(campaign = campaign, namespace = ns, type = kind, value = value)
  
  key = '%s.%s' % (campaign, ns)
  if (not _Stats.has_key(key)):
    datum.stats = _Stats[key] = Statistics.get_by_key_name_or_insert(key, campaign = campaign, namespace = ns, type = kind)
  else:
    datum.stats = _Stats[key]
  
  helper = stat.get(kind)
  helper.prepare(datum)
  if not hasattr(datum, '_invalid'):
    helper.calculate(datum)
    return datum
  else:
    logging.warning('datum invalid %s/%s, %s, %s' % (campaign, ns, datum.value, datum.type))

def cleanup_relations(sender, **kwargs):
  campaign = kwargs.get('instance')
  if (not TaskModel(object = campaign, task = 'delete campaign').put()):
    logging.critical('Could not schedule a DELETE Campaign Task for Campaign (%s)' % campaign)
      
application = webapp.WSGIApplication(debug = os.environ['SERVER_SOFTWARE'].startswith('Dev'), url_mapping = [
  ('/measure/([^/]+)/([^\.]+)?(?:\.(.+))?', MainPage)
])
 
if __name__ == "__main__":  
  run_wsgi_app(application)