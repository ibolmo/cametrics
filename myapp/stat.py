import urllib

def get(prop):
  glbs = globals()
  Summaries = map(lambda p: glbs[p], [p for p in glbs if '__' not in p and p is not 'get'])
  for Class in Summaries:
    if hasattr(Class, 'match_type') and Class.match_type and prop in Class.match_type:
      return Class
  return NoSummary

class NoSummary(object):
  match_type = ['off', 'none']
  
  @classmethod
  def prepare(cls, datum):
    """docstring for prepare"""
    return datum
  
  @classmethod
  def calculate(cls, stats, datum):
    """docstring for calculate"""
    if (not hasattr(stats, 'first_')):
      stats.first_ = datum
    stats.last_ = datum
    
    if (not hasattr(stats, 'count')):
      stats.count = 0
    stats.count += 1
    
class Summary(NoSummary):
  @classmethod
  def calculate(cls, stats, datum):    
    """docstring for calculate"""
    super(Summary, cls).calculate(stats, datum)
    
    if (not hasattr(stats, 'hits')):
      stats.hits = {}
    key = str(datum.value) # careful
    if (key not in stats.hits):
      stats.hits[key] = []
    stats.hits[key].append(str(datum.key()))
  
class NumberSummary(Summary):
  match_type = ['number', 'float', 'int', 'integer', 'long']
  @classmethod
  def prepare(cls, datum):
      """docstring for prepare"""
      return float(datum)  
    
  @classmethod
  def calculate(cls, stats, datum):
    """docstring for calculate"""
    super(NumberSummary, cls).calculate(stats, datum)
    if (not hasattr(stats, 'min') or datum.value < stats.min):
      stats.min = datum.value
    if (not hasattr(stats, 'max') or datum.value > stats.max):
      stats.max = datum.value
    if (not hasattr(stats, 'sum')):
      stats.sum = 0
    stats.sum += datum.value
    if (not hasattr(stats, 'mean')):
      stats.mean = 0
    stats.mean = stats.sum / stats.count
    
class StringSummary(Summary):
  match_type = ['str', 'string', 'text']
  
  @classmethod
  def prepare(self, value):
    """docstring for prepare"""
    return urllib.unquote_plus(value)
    
class DatetimeSummary(StringSummary):
  match_type = ['date', 'datetime', 'timestamp']
  DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
  
  @classmethod
  def calculate(cls, stats, datum):
    """docstring for calculate"""
    NoSummary.calculate(stats, datum)
    
    import datetime
    if (datum.type == 'timestamp'):
      try:
        datum.timestamp = float(datum.value)
      except TypeError:
        return logging.critical('Could not convert string timestamp (%s) into integer' % datum.value)
      try:
        datum.datetime = datetime.datetime.fromtimestamp(datum.timestamp)
      except ValueError:
        return logging.critical('Could not datetime.fromtimestamp(%s)' % datum.timestamp)
    elif ('date' in datum.type):
      try:
        datum.datetime = datetime.datetime.strptime(datum.value, DatetimeSummary.DATETIME_FORMAT) # careful
      except ValueError:
        return logging.critical('Could not datetime.strptime parse: %s' % datum.value)
      
      import time
      try:
        datum.timestamp = time.mktime(datum.datetime.timetuple())
      except ValueError, OverflowError:
        return logging.critical('Could not time.mktime(%s)' % datum.datetime.timetuple())
    else:
      return logging.critical('Unexpected type: %s for calc_date_statistics' % datum.type)
    
    timetuple = datum.datetime.timetuple()
    for i, bucket in enumerate(['year%s', 'month%s', 'day%s', 'hour%s', 'minute%s', 'second%s', 'weekday%s', 'day%s_of_the_year']):
      attr = bucket % 's'
      if (not hasattr(stats, attr)):
        stats[attr] = {}
      key = timetuple[i]
      if (key not in stats[attr]):
        stats[attr][key] = []
      stats[attr][key].append(str(datum.key()))

'''
### Location
 - longitude
 - latitude
 - statistics
    - area
    - centroid
    - boundary
    - box (histogram)

### Interval
 - start (date)
 - stop (date)
 - duration (number)
 - statistics
  - 
'''