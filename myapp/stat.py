import urllib, logging, math, re
from models import Histogram

_Hists = {}

def get(prop):
  glbs = globals()
  Summaries = map(lambda p: glbs[p], [p for p in glbs if '__' not in p and p is not 'get'])
  for Class in Summaries:
    if hasattr(Class, 'match_type') and Class.match_type and prop in Class.match_type:
      return Class
  
  logging.debug('No Summary for %s' % prop)
  return NoSummary

class NoSummary(object):
  match_type = ['off', 'none']
  
  @classmethod
  def prepare(cls, datum):
    '''Decorates the datum with additional attributes or redefines the value attribute for the calculations'''
    if (not hasattr(datum, 'value') or datum.value is None or datum.value is '' or datum.value is u''):
      return cls.invalidate(datum, 'No value provided')
  
  @classmethod
  def calculate(cls, datum):
    '''Decorates the statistic with additional attributes.
    For example, the first and last datum and increment the count of data in the system
    '''
    stats = datum.stats
    # The datum is not yet saved, and referencing it is not possible. Need to come up with a workaround. Perhaps Key.from_path().
    #if (not stats.head):
    #  stats.head = datum
    #stats.tail = datum
    
    if (not stats.count):
      stats.count = 0
    stats.count += 1
  
  @classmethod
  def invalidate(cls, datum, msg = ''):
    datum._invalid = True
    if (msg):
      return cls.critical(msg)
    
  @classmethod
  def critical(cls, msg):
    logging.critical(msg)
    return False
    
  @classmethod
  def tally(cls, stats, name, index):
    if (not isinstance(index, str)):
      try:
        index = str(index)
      except:
        return cls.critical('Could not str(%s)' % index)
        
    if name not in stats.histograms:
      stats.histograms.append(name)
      
    key = '%s.%s' % (stats.key(), name)
    if not _Hists.has_key(key):
      hist = _Hists[key] = Histogram.get_by_key_name_or_insert(key, statistic = stats, name = name)
    else:
      hist = _Hists[key]
      
    try:
      value = getattr(hist, index)
    except:
      value = 0
    setattr(hist, index, value + 1)     
        
class Summary(NoSummary):
  @classmethod
  def calculate(cls, datum):    
    '''The simplest summary by creating a histogram of all the 'hits' for the exact value.
    For example: input = ['a', 'b', 'a', 'c']
      hits = {
        'a': ['a'.key(), 'a'.key()],
        'b': ['b'.key()],
        'c': ['c'.key()]
      }
    '''
    super(Summary, cls).calculate(datum)
    cls.tally(stats = datum.stats, name = 'hits', index = datum.value)
  
class NumberSummary(Summary):
  match_type = ['number', 'float', 'int', 'integer', 'long']
  @classmethod
  def prepare(cls, datum):
    if super(NumberSummary, cls).prepare(datum) is False:
      return False
    try:
      x = datum.value is None and 1 or datum.value
      if not isinstance(x, (float, long, int)):
        datum.value = float(x) if '.' in x else long(x) if 'L' in x else int(x)
      else:
        datum.value = x
    except TypeError, err:
      return cls.invalidate(datum, 'Could not number(%s): %s' % (datum.value, err))
    
  @classmethod
  def calculate(cls, datum):
    '''Adds to the statistics the min, max, sum, mean, and other standard numerical statistics'''
    super(NumberSummary, cls).calculate(datum)
      
    stats = datum.stats
    if (not hasattr(stats, 'min') or datum.value < stats.min):
      stats.min = datum.value
    if (not hasattr(stats, 'max') or datum.value > stats.max):
      stats.max = datum.value
    if (not hasattr(stats, 'sum')):
      stats.sum = 0
    stats.sum = stats.sum + datum.value
    if (not hasattr(stats, 'mean')):
      stats.mean = 0
    stats.mean = stats.sum / stats.count
    
class StringSummary(Summary):
  match_type = ['str', 'string', 'text']
  
  @classmethod
  def prepare(cls, datum):
    if super(StringSummary, cls).prepare(datum) is False:
      return False
    
    try:
      datum.value = str(datum.value)
    except:
      return cls.invalidate(datum, 'Could not str(%s)' % datum.value)


import datetime, time
class DatetimeSummary(Summary):
  match_type = ['date', 'datetime', 'timestamp']
  DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
  
  @classmethod
  def prepare(cls, datum):
    '''Adds to the datum the equivalent timestamp, datetime to standardize the interface for the datum'''
    if super(DatetimeSummary, cls).prepare(datum) is False:
      return False
    
    if (datum.type == 'timestamp'):
      try:
        datum.timestamp = float(datum.value)
      except TypeError:
        return cls.invalidate(datum, 'Could not convert string timestamp (%s) into integer' % datum.value)
      try:
        datum.datetime = datetime.datetime.fromtimestamp(datum.timestamp)
      except ValueError:
        return cls.invalidate(datum, 'Could not datetime.fromtimestamp(%s)' % datum.timestamp)
    elif ('date' in datum.type):
      try:
        datum.datetime = datetime.datetime.strptime(datum.value, DatetimeSummary.DATETIME_FORMAT) # careful
      except ValueError:
        return cls.invalidate(datum, 'Could not datetime.strptime parse: %s' % datum.value)
      
      try:
        datum.timestamp = time.mktime(datum.datetime.timetuple())
      except ValueError, OverflowError:
        return cls.invalidate(datum, 'Could not time.mktime(%s)' % datum.datetime.timetuple())
    else:
      return cls.invalidate(datum, 'Unexpected type: %s for calc_date_statistics' % datum.type)
  
  @classmethod
  def calculate(cls, datum):
    '''Adds to the statistic various histograms/buckets for the years, months,
    days, and so forth (see datetime.datetime.timetuple for other histograms).
    Datetime statistics do not include the 'hits' histogram.'''
    NoSummary.calculate(datum) # No need for hits histogram
    
    timetuple = datum.datetime.timetuple()
    for i, bucket in enumerate(['year%s', 'month%s', 'day%s', 'hour%s', 'minute%s', 'second%s', 'weekday%s', 'day%sth']):
      cls.tally(stats = datum.stats, name = bucket % 's', index = timetuple[i])
    cls.tally(stats = datum.stats, name = 'weekdayth', index = datum.datetime.strftime('%U'))
    cls.tally(stats = datum.stats, name = 'hour.weekday', index = '%s.%s' % (timetuple[3], timetuple[-2]))
    cls.tally(stats = datum.stats, name = 'day.hour', index = '%s.%s' % (timetuple[2], timetuple[3]))
    cls.tally(stats = datum.stats, name = 'weekday.month', index = '%s.%s' % (timetuple[-2], timetuple[1]))

'''
### Location
 - longitude
 - latitude
 - statistics
    - area
    - centroid
    - boundary
    - box (histogram)
'''
class LocationSummary(Summary):
  match_type = ['gps', 'location']
  non_alpha = re.compile(r'[^a-zA-Z0-9\-\.]+')
  
  @classmethod
  def prepare(cls, datum):
    super(LocationSummary, cls).prepare(datum)
    try:
      longitude, latitude = cls.non_alpha.split(datum.value)
    except:
      return cls.invalidate(datum, 'Could not unpack %s got: %s' % (datum.value, cls.non_alpha.split(datum.value)))
      
    try:
      datum.longitude = float(longitude)
    except:
      return cls.invalidate(datum, 'Could not convert longitude %s to a float' % longitude)
    
    try:
      datum.latitude = float(latitude)
    except:
      return cls.invalidate(datum, 'Could not convert latitude %s to a float' % latitude)  
    
  @classmethod
  def calculate(cls, datum):
    NoSummary.calculate(datum)
    
    stats = datum.stats 
    tude = cls.geotude(datum.longitude, datum.latitude)
    key = ''
    while len(tude):
      key += tude.pop(0)
      cls.tally(stats = datum.stats, name = 'geotudes', index = key)
      key += '.'

    for limit, fn in {'min': min, 'max': max}.iteritems():
      for axis in ['longitude', 'latitude']:
        attr = '%s.%s' % (limit, axis)
        if (not hasattr(stats, attr)):
          setattr(stats, attr, getattr(datum, axis))
          continue
        setattr(stats, attr, fn(getattr(stats, attr), getattr(datum, axis)))
          
  @staticmethod
  def geotude(lon, lat):
    ''' Geotude indexing
    Reference:
      http://geotude.com/
    '''
    if (lat is None or lon is None or lat > 90 or lat <= -90 or lon < -180 or lon >= 180):
      return None
    
    alpha = 90.0 - lat
    beta = lon + 180.0
    
    gt = 500 * math.floor(alpha) + math.floor(beta) + 10000
    
    x, alpha = str(alpha).split('.')
    x, beta =  str(beta).split('.')
    gt, x = str(gt).split('.')
    
    la = len(alpha)
    lb = len(beta)
    return [gt] + [(i < la and alpha[i] or '0') + (i < lb and beta[i] or '0') for i in range(0, 7)]
    
'''
### Interval
 - start (date)
 - stop (date)
 - duration (number)
 - statistics
  - 
'''