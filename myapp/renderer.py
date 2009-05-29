import os, logging, math, re, urlparse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson

from models import Storage, Statistics, Histogram
import util, visualize

DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Dev')

def get(prop):
  for cls_name in globals().keys():
    if not cls_name.endswith('_Renderer'):
      continue
    if (cls_name.startswith(prop.capitalize())):
      return globals()[cls_name].render
  return lambda ns, data_path: HttpResponse('Unsupported format: %s' % format, status = 500)

def getattr_by_path(obj, attr, *default):
  """Like getattr(), but can go down a hierarchy like 'attr.subattr'"""
  value = obj
  for i, part in enumerate(attr.split('.')):
    if isinstance(value, dict):
      if not value.has_key(part) and len(default) > i:
        return default[i]
      value = value.get(part)
      if callable(value):
        value = value()
    else:
      if not hasattr(value, part) and len(default) > i:
        return default[i]
      try:
        value = getattr(value, part)
      except:
        value = None
      if callable(value):
        value = value()
  return value

class Renderer(object):
  mimetypes = {
    'json': DEBUG and 'text/html' or 'application/json',
    'html': 'text/html',
    'csv': 'text/csv',
    'plain': 'text/plain'
  }
  
  @staticmethod
  def to_dict(datum):
    return datum and datum.to_dict() or None
    
  @classmethod
  def render(cls, page, data, format):
    page.response.headers.add_header('Content-Type', Renderer.mimetypes.get(format, 'text/plain'))
    page.response.out.write(data)
    page.response.set_status(200)

class Json_Renderer(Renderer):
  @classmethod
  def get_stored_data(cls, campaign, ns):
    data = Storage.all().filter('campaign = ', campaign).filter('namespace = ', ns).fetch(1000) # todo, paginator
    return map(lambda datum: datum.to_json(), data)
  
  @classmethod
  def get_statistics(cls, campaign, ns, path):
    stats = Statistics.get_by_campaign_and_namespace(campaign, ns)
    if (not stats):
      data = '{}'
    else:
      path = path.lstrip('stats').strip('.')
      data = path and simplejson.dumps(getattr_by_path(stats, path)) or stats.to_json()
    return data
    
  @classmethod
  def render(cls, page, ns, path):
      """docstring for render"""      
      path = path or ''
    
      if path.startswith('values'):
        data = cls.get_stored_data(page.campaign, ns)
      elif path.startswith('stats'):
        data = cls.get_statistics(page.campaign, ns, path)
      else:
        datum = Storage.all().filter('campaign = ', page.campaign).filter('namespace =', ns).get()
        data = {
          'type': simplejson.dumps(datum and datum.type),
          'values': cls.get_stored_data(page.campaign, ns),
          'stats': cls.get_statistics(page.campaign, ns, path)
        }
      return super(Json_Renderer, cls).render(page, data, 'json')

class Gchart_Renderer(Renderer):  
  @staticmethod
  def get_dqs(qs):
    logging.debug('Gchart_Renderer::qs = %s' % qs)
    if (qs):
      try:
        return urlparse.parse_qs(qs, keep_blank_values = True, strict_parsing = True)
      except ValueError:
        logging.critical('Could not parse_qs(%s)' % qs)
    else:
      logging.warning('No arguments passed to Google Charts API')
      return {}
    
  @classmethod
  def render(cls, page, format, data, stats, data_path):    
    obj = None
    if not len(data):
      logging.critical('No data found for page %s' % page)
      return HttpResponse(status = 404)
    
    dtype = data[0].type
    if 'values' in data_path and len(data):
      obj = [d.value for d in data]
    elif 'stats' in data_path and stats:
      obj = cls.object_from_path(root = stats.to_dict(), path = data_path)
    else:
      logging.warning('Did not expect data_path: %s' % data_path)
    logging.info('Getting visualization for: %s' % (not obj and 'none' or dtype))
    url = visualize.get(not obj and 'none' or dtype).get_url(page.request, obj)
    logging.info('Redirecting to: %s' % url)
    return url and (DEBUG and HttpResponse('<img src="%s" />' % url) or HttpResponseRedirect(url)) or HttpResponse('No visualization found', status = 500)

class Gc_Renderer(Gchart_Renderer):
  pass
  