import os, logging, math, simplejson, re, urlparse
from django.http import HttpResponse, HttpResponseRedirect

from models import Histogram
import util, visualize

DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Dev')

def get(prop):
  for cls_name in globals().keys():
    if not cls_name.endswith('_Renderer'):
      continue
    if (cls_name.startswith(prop.capitalize())):
      return globals()[cls_name].render
  return lambda l, format, m, n, o: HttpResponse('Unsupported format: %s' % format, status = 500)

class Renderer(object):
  mimetypes = {
    'json': 'text/json', #'application/json',
    'html': 'text/html',
    'csv': 'text/csv',
    'plain': 'text/plain'
  }
  
  @staticmethod
  def to_dict(datum):
    return datum and datum.to_dict() or None
    
  @classmethod
  def render(cls, request, format = 'json', data = '{}', stats = None, data_path = None):
    return render_to_response(request, 'myapp/get_data.%s' % format, {'data': data}, mimetype = Renderer.mimetypes.get(format, 'text/plain'))
    
  @classmethod
  def object_from_path(cls, root = None, path = ''):
    path = path.split('.'); path.pop(0) # assume root is the first element
    obj = root
    for p in path:
      obj = obj.get(p)
    return obj      
  
class Json_Renderer(Renderer):
  @classmethod
  def render(cls, request, format, data, stats, data_path):
      """docstring for render"""      
      data_path = data_path or []
      data_type = len(data) and data[0].type or None
          
      logging.info('data path: %s' % data_path)
      
      if 'values' in data_path:
        data = map(lambda datum: datum.to_json(), data)
      elif 'stats' in data_path:
        if (not stats):
          stats = {}
        else:
          path = data_path.split('.'); path.pop(0)
          obj = stats.to_dict()
          for p in path:
            obj = obj.get(p)
          if (isinstance(obj, dict)):
            util.replace_datastore_types(obj)
          data = simplejson.dumps(obj)
      else:
        data = {
        'type': data_type,
        'values': map(lambda datum: datum.to_json(), data),
        'stats': stats and stats.to_json() or {}
      }
      return super(Json_Renderer, cls).render(request, data = data)

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
  def render(cls, request, format, data, stats, data_path):    
    obj = None
    if not len(data):
      return HttpResponse(status = 404)
    
    dtype = data[0].type
    if 'values' in data_path and len(data):
      obj = [d.value for d in data]
    elif 'stats' in data_path and stats:
      obj = cls.object_from_path(root = stats.to_dict(), path = data_path)
    else:
      logging.warning('Did not expect data_path: %s' % data_path)
    logging.info('Getting visualization for: %s' % (not obj and 'none' or dtype))
    url = visualize.get(not obj and 'none' or dtype).get_url(request, obj)
    logging.info('Redirecting to: %s' % url)
    return url and (DEBUG and HttpResponse('<img src="%s" />' % url) or HttpResponseRedirect(url)) or HttpResponse('No visualization found', status = 500)

class Gc_Renderer(Gchart_Renderer):
  pass
  