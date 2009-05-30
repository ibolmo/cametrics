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
    'plain': 'text/plain',
    'javascript': 'text/javascript',
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
    def prepare(datum):
      datum = datum.to_dict()
      util.replace_datastore_types(datum)
      return datum
    return map(prepare, data)
  
  @classmethod
  def get_statistics(cls, campaign, ns, path):
    stats = Statistics.get_by_campaign_and_namespace(campaign, ns)
    if (not stats):
      data = '{}'
    else:
      path = path.lstrip('stats').strip('.')
      data = path and getattr_by_path(stats, path) or stats
      if isinstance(data, (Histogram, Statistics)):
        data = data.to_dict()
        util.replace_datastore_types(data)
    return data
    
  @classmethod
  def render(cls, page, ns, path):  
    if path.startswith('values'):
      data = cls.get_stored_data(page.campaign, ns)
    elif path.startswith('stats'):
      data = cls.get_statistics(page.campaign, ns, path)
    else:
      datum = Storage.all().filter('campaign = ', page.campaign).filter('namespace =', ns).get()
      data = {
        'type': datum and datum.type,
        'values': cls.get_stored_data(page.campaign, ns),
        'stats': cls.get_statistics(page.campaign, ns, path)
      }
    return super(Json_Renderer, cls).render(page, simplejson.dumps(data), 'json')

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
  def render(cls, page, ns, path): 
    datum = Storage.all().filter('campaign = ', page.campaign).filter('namespace =', ns).get()
    if not datum:
      logging.warning('No stored data found (%s/%s)' % (page.campaign, ns))
      return page.response.set_status(404)
    
    obj = None
    if path.startswith('values'):
      data = Storage.all().filter('campaign = ', page.campaign).filter('namespace = ', ns).fetch(1000) # todo, paginator
      obj = [d.value for d in data]
    elif path.startswith('stats'):
      stats = Statistics.get_by_campaign_and_namespace(page.campaign, ns)
      path = path.lstrip('stats').strip('.')
      obj = stats and path and getattr_by_path(stats, path)
      if isinstance(obj, Histogram):
        obj = obj.to_dict()
    else:
      logging.warning('Did not expect path: %s' % path)        
      
    logging.info('Getting visualization for: %s' % (not obj and 'none' or datum.type))
    url = visualize.get(not obj and 'none' or datum.type).get_url(page.request, obj)
    logging.info('Redirecting to: %s' % url)
    if url:
      if DEBUG:
        return page.response.out.write('<img src="%s" />' % url)
      return page.redirect(url)
    page.response.set_status(500)

class Gc_Renderer(Gchart_Renderer):
  pass
  
class Gmap_Renderer(Renderer):
  options = {
    'color': '#FF0000',
    'weight': 10,
    'zoomFactor': 32,
    'numLevels': 4  
  }
  
  ''' Google Map API Renderer
  
  Transforms a longitude/latitude object (filtered, if either are not present) into three variations (using the `type` request argument):
    encoded - (default) An Encoded String as described in: http://code.google.com/apis/maps/documentation/polylinealgorithm.html
    polyline - A JavaScript polyline as described in this example: http://code.google.com/apis/maps/documentation/overlays.html#Encoded_Polylines, requires a callback or class parameter (see below)
    raw - A JSON object
    
  Other Query Arguments:
    callback - Name of the JavaScript function to call with the first argument the object returned
    class - Name of the GMap class to addOverlay with default options or user overriden options
    ... - Any other option available to the GPolyline.fromEncoded object options, the parameter is the object key. For example color=#FF0000 (only appropriate for when you pass the class parameter)
  '''
  @classmethod
  def render(cls, page, ns, path):
    gmtype = page.request.get('type', 'raw')
    logging.debug('Rendering Gmap of type: %s.' % gmtype)
    if gmtype == 'raw':
      return Json_Renderer.render(page, ns, path)
      
    if path.startswith('values'):
      data = Storage.all().filter('campaign = ', page.campaign).filter('namespace = ', ns).fetch(1000) # todo, paginator

      options = Gmap_Renderer.encode(data)
      callback = page.request.get('callback')
      if gmtype == 'polyline':
        options.update(cls.options)
        callback = callback or '%s.addOverlay' % (page.request.get('class') or 'map')
        # add user paramters
        text = '%s(new GPolyline.fromEncoded(%s));' % (callback, options)
      else:
        text = '%s(%s);' % (callback, options)
    else:
      logging.warning('Did not expect path: %s' % path)
      text = 'null'
    
    return super(Gmap_Renderer, cls).render(page, text, 'javascript')
                
  @staticmethod
  def encode(points):
    """ Encode a coordinates into an encoded string.
    
    For more information: http://wiki.urban.cens.ucla.edu/index.php/How-to_use_Google_Maps_polyline_encoding_to_compact_data_size
    
    Author
      Jason Ryder, <ryder.jason@gmail.com>
    """
    plat = 0
    plng = 0
    encoded_points = ''
    encoded_levels = ''
    for i, point in enumerate(points):
      try:
        if isinstance(point, dict):
          lat = point.get('latitude')
          lng = point.get('longitude')
        else:
          lat = point.latitude
          lng = point.longitude
      except:
        continue
        
      level = 3 - i % 4                    
      
      late5 = int(math.floor(lat * 1e5))
      lnge5 = int(math.floor(lng * 1e5)) 
      
      dlat = late5 - plat
      dlng = lnge5 - plng                
      
      plat = late5
      plng = lnge5                       
      
      encoded_points += Gmap_Renderer.encodeSignedNumber(dlat) + Gmap_Renderer.encodeSignedNumber(dlng)
      encoded_levels += Gmap_Renderer.encodeNumber(level) 
    
    return {
      'points': encoded_points,
      'levels': encoded_levels
    }
    
  @staticmethod
  def encodeNumber(num):
    '''Encode an unsigned number in the encode format.
    '''
    encodeString = ""
    while num >= 0x20:
      encodeString += chr((0x20 | (num & 0x1f)) + 63)
      num >>= 5
    encodeString += chr(num + 63)
    return encodeString
    
  @staticmethod
  def encodeSignedNumber(num):
    '''Encode a signed number into the google maps polyline encode format.
    '''
    sgn_num = num << 1
    if num < 0:
      sgn_num = ~(sgn_num)
    return Gmap_Renderer.encodeNumber(sgn_num)
      
class Gm_Renderer(Gmap_Renderer):
  pass