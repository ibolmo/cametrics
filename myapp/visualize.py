import logging, stat, cgi, urllib
from pygooglechart import *

def get(prop):
  glbs = globals()
  Classes = map(lambda p: glbs[p], [p for p in glbs if '__' not in p and p is not 'get'])
  for Class in Classes:
    if hasattr(Class, 'match_type') and Class.match_type and prop in Class.match_type:
      return Class
  return NoVisual
  
def _chart_type(chart):
  cls = globals().get(chart + 'Chart')
  if cls:
    try:
      chart = cls(1, 1, auto_scale=False)
      tupl = (chart.type_to_url().split('=')[1], cls)
      del chart
      return tupl
    except:
      pass  

CHART_TYPE_MAP = dict(map(_chart_type, ChartGrammar.get_possible_chart_types()))

class NoVisual(object):
  match_type = stat.NoSummary.match_type
  
  w = 200
  h = 100
  s = (w, h)
  
  @classmethod
  def get_url(cls, dqs, obj):
    pass
    
  @classmethod
  def _get_url(cls, request, chart):
    url, dqs = chart.get_url().split('?')
    query = request.GET.copy()
    query.update(dict(cgi.parse_qsl(dqs)))
    return url + '?' + urllib.urlencode(query)
            
class Visual(NoVisual):
  pass
  
class NumberVisual(Visual):
  match_type = stat.NumberSummary.match_type
  
  @classmethod
  def get_url(cls, request, obj):    
    chs = dict(enumerate(request.GET.get('chs', '').split('x')))
    w = int(chs.get(0) or cls.w)
    h = int(chs.get(1) or cls.h)
    
    ChartCLS = CHART_TYPE_MAP.get(request.GET.get('cht', ''), SparkLineChart)
    
    chart = ChartCLS(w, h)
    logging.debug('NumberVisual::obj = %s' % obj)
    
    chart.add_data(obj)
    return cls._get_url(request, chart)
    
class DatetimeVisual(Visual):
  match_type = stat.DatetimeSummary.match_type
  DATETIME_FORMAT = stat.DatetimeSummary.DATETIME_FORMAT
  
class LocationVisual(Visual):
  match_type = stat.LocationSummary.match_type