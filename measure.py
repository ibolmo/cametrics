import os, logging
logging.getLogger().setLevel(logging.DEBUG)

from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api.labs import taskqueue

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
    self.namespace, self.path = util.getParts((path or '').strip('/').replace('/', '.'))
  
    logging.debug("%s, %s, %s; %s" % (key, self.namespace, self.path, self.format))
    helper = renderer.get(self.format)
    if self.path.startswith('values'): # this could be automated
      self.path = self.path.lstrip('values').strip('.')
      return helper.render_values(self)
    elif self.path.startswith('stats'):
      self.path = self.path.lstrip('stats').strip('.')
      return helper.render_stats(self)
    helper.render(self)
    
  def post(self, key, path, format):
    if (not key):
      return self.error(500)
      
    process_url = self.request.path.replace('measure','process')
    
    
    logging.debug("process_url = " + process_url)
    
    taskqueue.add(url=process_url, params=self.request.POST)
    
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write('Added to taskqueue.\n')
    
class Process(webapp.RequestHandler):
  def post(self,key,path,format):  
    
    self.campaign = Campaign.all(keys_only = True).filter('__key__ = ', db.Key(key)).get()
    if (not self.campaign):
      logging.warning('No campaign (%s) found.' % key)
      return self.error(404)
      
    logging.debug("%s, %s, %s" % (key, path, format))
    
    for value in self.request.POST:
			logging.info(value+": " + self.request.get(value))
    
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
    self.response.set_status(error and 304 or 200)


def send_to_datastore(models):
  payload = [models]
  
  while payload:
    models = payload.pop(0)
    l = len(models)
    if l:
      try:
        db.put(models)
        logging.info('::STATS:: db.put(%s)', l)
      except:
        logging.info('::STATS:: !db.put(%s)', l)
        if l == 1:
          logging.warning('Could not save: %s', models)
          continue
        payload.append(models[:l / 2])
        payload.append(models[l / 2:])

def create_datum(campaign, ns, obj = {}):
  ns = ns.strip('/').replace('/', '.')    
  value = obj.get('value')
  kind = obj.get('type', 'number')
    
  datum = Storage(campaign = campaign, namespace = ns, type = kind, value = value)
  
  key = '%s.%s' % (campaign, ns)
  if (not _Stats.has_key(key)):
    datum.stats = _Stats[key] = Statistics.get_by_key_name_or_insert(key, campaign = campaign, namespace = ns)
    datum.stats.type = kind
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
  ('/measure/([^/]+)/([^\.]+)?(?:\.(.+))?', MainPage),
  ('/process/([^/]+)/([^\.]+)?(?:\.(.+))?', Process)
])
 
if __name__ == "__main__":  
  run_wsgi_app(application)
