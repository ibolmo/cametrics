import logging, stat
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
            
class Visual(NoVisual):
  pass
  
class NumberVisual(Visual):
  match_type = stat.NumberSummary.match_type
  
  @classmethod
  def get_url(cls, request, obj):    
    chs = dict(enumerate(request.GET.get('chs', '').split('x')))
    w = int(chs.get(0) or cls.w)
    h = int(chs.get(1) or cls.h)
    logging.debug('NumberVisual.get_url::s = (%s, %s)' % (w, h))
    
    ChartCLS = CHART_TYPE_MAP.get(request.GET.get('cht', ''), SparkLineChart)
    logging.debug('Using chart %s' % ChartCLS)
    
    chart = ChartCLS(w, h)
    logging.debug('NumberVisual::obj = %s' % obj)
    
    chart.add_data(obj)
    return chart.get_url()
    
class DatetimeVisual(Visual):
  match_type = stat.DatetimeSummary.match_type
  DATETIME_FORMAT = stat.DatetimeSummary.DATETIME_FORMAT
  
class LocationVisual(Visual):
  match_type = stat.LocationSummary.match_type