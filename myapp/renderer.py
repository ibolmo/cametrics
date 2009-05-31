import os, logging, math, re, urlparse
from django.utils import simplejson

from models import Storage, Statistics, Histogram
import util, visualize

DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Dev')

def get(prop):
  glbs = globals()
  Renderers = map(lambda p: glbs[p], [p for p in glbs if '__' not in p and p is not 'get'])
  for Class in Renderers:
    if hasattr(Class, 'match_formats') and Class.match_formats and prop in Class.match_formats:
      return Class

  logging.debug('No Renderer for %s' % prop)
  return Renderer

MIMETYPES = {
  'json': DEBUG and 'text/html' or 'application/json',
  'html': 'text/html',
  'csv': 'text/csv',
  'plain': 'text/plain',
  'javascript': 'text/javascript',
}

class NoRenderer(object):  
  @classmethod
  def get_values(cls, campaign, ns, path):
    return []
  
  @classmethod
  def get_statistics(cls, campaign, ns, path):
    return {}
  
  @classmethod
  def render_values(cls, page, path):
    return cls.render(page, cls.get_stored_data(page.campaign, page.namespace, path))
    
  @classmethod
  def render_stats(cls, page, path):
    return cls.render(page, cls.get_statistics(page.campaign, page.namespace, path))
  
  @classmethod
  def render(cls, page, data):
    page.response.headers.add_header('Content-Type', MIMETYPES.get(page.format, 'text/plain'))
    page.response.out.write(data)
    page.response.set_status(data and 200 or 204)

class Renderer(NoRenderer):  
  @classmethod
  def get_values(cls, campaign, ns, path):
    query = Storage.all().filter('campaign = ', campaign).filter('namespace = ', ns)
    return [datum for datum in query] # todo, paginator
  
  @classmethod
  def get_statistics(cls, campaign, ns, path):
    data = Statistics.get_by_campaign_and_namespace(campaign, ns)
    if (data and path):
      path = path.lstrip('stats').strip('.')
      if path:
        data = util.getattr_by_path(stats, path)
    return data

class JSONRenderer(Renderer):
  match_formats = ['json']
  
  @classmethod
  def get_values(cls, campaign, ns, path):
    data = super(JSONRenderer, cls).get_values(campaign, ns, path)
    return map(lambda d: util.replace_datastore_types(d.to_dict()), data)
  
  @classmethod
  def get_statistics(cls, campaign, ns, path):
    data = super(JSONRenderer, cls).get_statistics(campaign, ns, path)
    if isinstance(data, (Histogram, Statistics)):
        data = util.replace_datastore_types(data.to_dict())
    return data
    
  @classmethod
  def render(cls, page, data = None):  
    data = data or {
      'values': cls.get_values(page.campaign, page.namespace, ''),
      'stats': cls.get_statistics(page.campaign, page.namespace, '')
    }
    return super(JSONRenderer, cls).render(page, simplejson.dumps(data))
    
class GChartRenderer(Renderer):
  match_formats = ['gc', 'gchart']
  
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
    stats = Statistics.get_by_campaign_and_namespace(page.campaign, ns)
    
    obj = None
    if path.startswith('values'):
      data = Storage.all().filter('campaign = ', page.campaign).filter('namespace = ', ns).fetch(1000) # todo, paginator
      obj = [d.value for d in data]
    elif path.startswith('stats'):
      path = path.lstrip('stats').strip('.')
      obj = stats and path and util.getattr_by_path(stats, path)
      if isinstance(obj, Histogram):
        obj = obj.to_dict()
    else:
      logging.warning('Did not expect path: %s' % path)        
      
    logging.info('Getting visualization for: %s' % (not obj and 'none' or stats.type))
    url = visualize.get(not obj and 'none' or stats.type).get_url(page.request, obj)
    logging.info('Redirecting to: %s' % url)
    if url:
      if DEBUG:
        return page.response.out.write('<img src="%s" />' % url)
      return page.redirect(url)
    page.response.set_status(500)
  
class GMapRenderer(Renderer):
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
  
  options = {
    'color': '#FF0000',
    'weight': 2,
    'zoomFactor': 32,
    'numLevels': 4  
  }
  
  @classmethod
  def render(cls, page, ns, path):
    gmtype = page.request.get('type', 'raw')
    logging.debug('Rendering Gmap of type: %s.' % gmtype)
    if gmtype == 'raw':
      return Json_Renderer.render(page, ns, path)
      
    if path.startswith('values'):
      data = Storage.all().filter('campaign = ', page.campaign).filter('namespace = ', ns).fetch(1000) # todo, paginator

      options = GMapRenderer.encode(data)
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
    return super(GMapRenderer, cls).render(page, text, 'javascript')
                
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
      
      encoded_points += GMapRenderer.encodeSignedNumber(dlat) + GMapRenderer.encodeSignedNumber(dlng)
      encoded_levels += GMapRenderer.encodeNumber(level) 
    
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
    return GMapRenderer.encodeNumber(sgn_num)