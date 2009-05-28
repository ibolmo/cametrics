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
    
    campaign = Campaign.all(keys_only = True).filter('__key__ = ', db.Key(key)).get()
    if (not campaign):
      logging.warning('No campaign (%s) found.' % key)
      return self.error(404)
    
    ns = (path or '').strip('/').replace('/', '.')
    format = format or self.request.get('format', 'json')
    ns, data_path = util.getParts(ns)

    logging.info("%s, %s, %s; %s" % (key, ns, format, data_path))
    
    data = Storage.all().filter('campaign = ', campaign).filter('namespace = ', ns).fetch(1000) # todo, paginator
    stats = Statistics.get_by_campaign_and_namespace(campaign, ns)
    renderer.get(format)(self, format, data, stats, data_path)

  def post(self, key, path, format):
    if (not key):
      return self.error(500)
    
    campaign = Campaign.all(keys_only = True).filter('__key__ = ', db.Key(key)).get()
    if (not campaign):
      logging.warning('No campaign (%s) found.' % key)
      return self.error(404)
      
    logging.warning("%s, %s, %s" % (key, path, format))
    
    models = []
    error = False
    if 'bulk' in self.request.get('type'):
      data = simplejson.loads(self.request.get('data') or '[]')  #todo remove need for loads
      for datum in data:
        ns = datum.get('namespace')
        if ns:
          models.append(create_datum(campaign, ns, datum))
    elif path:
        models.append(create_datum(campaign, path, self.request))
    
    models += _Stats.values() + stat._Hists.values()
    try:
      keys = db.put(models)
    except:
      error = True
      logging.warning('Could not save all models: (%s/%s)' % (len(keys) / len(models)))
    self.response.set_status(error and 304 or 201)

def create_datum(campaign, ns, obj = {}):
  ns = ns.strip('/').replace('/', '.')    
  value = obj.get('value')
  kind = obj.get('type', 'number')
  
  logging.debug('POST | value: %s | kind: %s' % (value, kind))
    
  datum = Storage(campaign = campaign, namespace = ns, type = kind, value = value)
  
  key = '%s.%s' % (campaign, ns)
  if (not _Stats.has_key(key)):
    datum.stats = _Stats[key] = Statistics.get_by_key_name_or_insert(key, campaign = campaign, namespace = ns)
  else:
    datum.stats = _Stats[key]
    
  if not hasattr(datum, '_invalid'):
    stat.get(kind).calculate(datum)
    return datum

def cleanup_relations(sender, **kwargs):
  campaign = kwargs.get('instance')
  if (not TaskModel(object = campaign, task = 'delete campaign').put()):
    logging.critical('Could not schedule a DELETE Campaign Task for Campaign (%s)' % campaign)
      
application = webapp.WSGIApplication(debug = os.environ['SERVER_SOFTWARE'].startswith('Dev'), url_mapping = [
  ('/measure/([^/]+)/([^\.]+)?(?:\.(.+))?', MainPage)
])
 
if __name__ == "__main__":  
  run_wsgi_app(application)