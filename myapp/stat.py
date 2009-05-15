import urllib, logging
from models import Histogram

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
    '''Decorates the datum with additional attributes or redefines the value attribute for the calculations'''
    pass
  
  @classmethod
  def calculate(cls, stats, datum):
    '''Decorates the statistic with additional attributes.
    For example, the first and last datum and increment the count of data in the system
    '''
    if (not stats.first_):
      stats.first_ = datum
    stats.last_ = datum
    
    if (not stats.count):
      stats.count = 0
    stats.count += 1
    
class Summary(NoSummary):
  @classmethod
  def calculate(cls, stats, datum):    
    '''The simplest summary by creating a histogram of all the 'hits' for the exact value.
    For example: input = ['a', 'b', 'a', 'c']
      hits = {
        'a': ['a'.key(), 'a'.key()],
        'b': ['b'.key()],
        'c': ['c'.key()]
      }
    '''
    super(Summary, cls).calculate(stats, datum)
    
    if ('hits' not in stats.histograms):
      stats.histograms.append('hits')
    hist = Histogram(statistic = stats, name = 'hits')
    try:
      hist.index = str(datum.value) # careful
    except:
      return logging.critical('Could not str(%s)' % datum.value)
    hist.datum = datum
    if (not hist.put()):
      return logging.critical('Could not save hist: %s' % hist)    
  
class NumberSummary(Summary):
  match_type = ['number', 'float', 'int', 'integer', 'long']
  @classmethod
  def prepare(cls, datum):
      '''Converts the datum from a string, to (optimistically) into a float. Additionally, if value is None defaults value to 1.0'''
      try:
        datum.value = float(datum.value or 1)  
      except:
        logging.critical('Could not convert %s into a float' % value)
    
  @classmethod
  def calculate(cls, stats, datum):
    '''Adds to the statistics the min, max, sum, mean, and other standard numerical statistics'''
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

class DatetimeSummary(Summary):
  match_type = ['date', 'datetime', 'timestamp']
  DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
  
  @classmethod
  def prepare(self, datum):
    '''Adds to the datum the equivalent timestamp, datetime to standardize the interface for the datum'''
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
  
  @classmethod
  def calculate(cls, stats, datum):
    '''Adds to the statistic various histograms/buckets for the years, months,
    days, and so forth (see datetime.datetime.timetuple for other histograms).
    Datetime statistics do not include the 'hits' histogram.'''
    NoSummary.calculate(stats, datum) # No need for hits histogram
    
    timetuple = datum.datetime.timetuple()
    for i, bucket in enumerate(['year%s', 'month%s', 'day%s', 'hour%s', 'minute%s', 'second%s', 'weekday%s', 'day%s_of_the_year']):
      attr = bucket % 's'      
      if (attr not in stats.histograms):
        stats.histograms.append(attr)
      hist = Histogram(statistic = stats, name = attr)
      hist.index = str(timetuple[i])
      hist.datum = datum
      if (not hist.put()):
        return logging.critical('Could not save hist: %s' % hist)
        
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