import urllib, logging, math, re
from models import Histogram
from django.utils import simplejson

from django.http import HttpResponse, HttpResponseRedirect
from ragendja.template import render_to_response

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
    return datum and datum.to_dict() or {}
    
  @classmethod
  def render(cls, request, format = 'json', data = '{}', stats = None, data_path = None):
    return render_to_response(request, 'myapp/get_data.%s' % format, {'data': data}, mimetype = Renderer.mimetypes.get(format, 'text/plain'))
  
class Json_Renderer(Renderer):
  @classmethod
  def render(cls, request, format, data, stats, data_path):
      """docstring for render"""      
      data_path = data_path or []
      data_type = len(data) and data[0].type or None
          
      logging.info('data path: %s' % data_path)
      
      if 'values' in data_path:
        data = simplejson.dumps(map(Renderer.to_dict, data))
      elif 'stats' in data_path:
        path = data_path.split('.'); path.pop(0)
        data_stats = map(Renderer.to_dict, stats)
        data_stats = data_stats[0]
        obj = data_stats
        for p in path:
          obj = data_stats.get(p)
        data = simplejson.dumps(obj)
      else:
        data = simplejson.dumps({
        'type': data_type,
        'values': map(Renderer.to_dict, data),
        'stats': map(Renderer.to_dict, stats)
      })
      return super(Json_Renderer, cls).render(request, data = data)

class TextData(object):
    max_value = 100
    
    @staticmethod
    def encode(data):
        encoded_data = []
        for datum in data:
            sub_data = []
            for value in datum:
                if value is None:
                    sub_data.append(-1)
                elif value >= 0 and value <= TextData.max_value:
                    sub_data.append("%.1f" % float(value))
                else:
                    logging.critical('Could not TextData %s' % (value))
            encoded_data.append(','.join(sub_data))
        return 't:' + '|'.join(encoded_data)

class SimpleData(object):
    max_value = 61
    enc_map = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    
    @staticmethod
    def encode(data):
        encoded_data = []
        for datum in data:
            sub_data = []
            for value in datum:
                if value is None:
                    sub_data.append('_')
                elif value >= 0 and value <= SimpleData.max_value:
                    sub_data.append(SimpleData.enc_map[value])
                else:
                    logging.critical('cannot encode value: %d' % value)
                    sub_data.append('__')
            encoded_data.append(''.join(sub_data))
        return 's:' + ','.join(encoded_data)

class ExtendedData(object):
  max_value = 4095
  enc_map = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-.'

  @staticmethod
  def encode(data):
    encoded_data = []
    enc_size = len(ExtendedData.enc_map)
    for datum in data:
      sub_data = []
      for value in datum:
        if value is None:
          sub_data.append('__')
        elif value >= 0 and value <= ExtendedData.max_value:
          first, second = divmod(int(value), enc_size)
          sub_data.append('%s%s' % (ExtendedData.enc_map[first], ExtendedData.enc_map[second]))
        else:
          sub_data.append('__')
          logging.critical('Item #%i "%s" is out of range' % (datum.index(value), value))
      encoded_data.append(''.join(sub_data))
    return 'e:' + ','.join(encoded_data)

class Gchart_Renderer(Renderer):
  BASE_URL = 'http://chart.apis.google.com/chart?'
  
  default_dqs = {
    'chs': '250x100',
    'cht': 'bvs',
    'chxt': 'x,y'
  }
  
  @classmethod
  def render(cls, request, format, data, stats, data_path):
    '''
    Get data_path, grab query, append to query the chd=, and also add/replace axes
    '''
    if ('?' in data_path):
      data_path, qs = data_path.split('?')
      import urlparse
      try:
        dqs = urlparse.parse_qs(qs, keep_blank_values = True, strict_parsing = True)
      except ValueError:
        logging.critical('Could not parse_qs(%s)' % qs)
    else:
      logging.warning('No arguments passed to Google Charts API')
      dqs = Gchart_Renderer.default_dqs
      
    if 'values' in data_path:
      chd = [[d.value for d in data]]
      chxl = ['Values']
    elif 'stats' in data_path:
      path = data_path.split('.'); path.pop(0)
      data_stats = map(Renderer.to_dict, stats)
      data_stats = data_stats[0]
      obj = data_stats
      for p in path:
        obj = data_stats.get(p)
      if (isinstance(obj, dict)): # guess (for now) that this is a histogram/bucket list
        chd = []
        chxl = []
        for key, values in obj.iteritems():
          chxl.append(key)
          chd.append(len(values))
        chd = [chd] # todo, ExtendedData expects multi-d list which would be correct for stats snapshots
    else:
      logging.critical('Unexpected gchart for %s' % data_path)          
    
    # convert
    chd = TextData.encode(chd)
    chxl = '0:|%s|' % '|'.join(chxl)
    dqs['chds'] = '%s,%s' % (stats[0].min - 1, stats[0].max) # careful
    dqs['chxr'] = '%s,%s,%s' % (1, stats[0].min - 1, stats[0].max) # careful
    dqs['chd'] = chd
    dqs['chxl'] = dqs.get('chxl', chxl) # todo, need a placeholder for x-axis for allowing custom axes
    return HttpResponseRedirect(Gchart_Renderer.BASE_URL + urllib.urlencode(dqs))
  
class Gc_Renderer(Gchart_Renderer):
  pass
  