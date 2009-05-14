import unittest, logging, util, datetime
from myapp import stat

class Object(object):
  def __init__(self):
    self.data = {}
    
  def key(self):
    return datetime.datetime.now()
  
  def __setitem__(self, key, value):
    self.data[key] = value;
    
  def __getitem__(self, key):
    return self.data[key]
    
  def __delete__(self, key):
    del self.data[key]

class StatTest (unittest.TestCase):
  def setUp(self):
    self.number = stat.get('number')
    self.string = stat.get('string')
    self.datetime = stat.get('datetime')
    self.none = stat.get('none')
    
  def test_number_prepare(self):
    tests = [
      (10.245, '10.245'),
      (10, '10'),
    ]
    for test in tests:
      expected, raw = test
      self.assertEqual(expected, self.number.prepare(raw))
      
  def test_number_calc(self):
    datum = Object()
    datum.value = 10
    datum.type = 'number'
    stats = Object()
    
    self.number.calculate(stats, datum)
    self.assertEqual(1, stats.count)
    self.assertEqual(10, stats.sum)
    self.assertTrue(hasattr(stats, 'hits'))
    
    self.number.calculate(stats, datum)
    self.assertEqual(2, stats.count)
    self.assertEqual(20, stats.sum)
    self.assertTrue(hasattr(stats, 'hits'))
      
  def test_string_prepare(self):
    tests = [
      ('string', 'string'),
      ('string value', 'string+value'),
      ('string value', 'string%20value')
    ]
    for test in tests:
      expected, raw = test
      self.assertEqual(expected, self.string.prepare(raw))
      
  
  def test_string_calc(self):
    datum = Object()
    datum.value = 'a string'
    datum.type = 'string'
    stats = Object()
    
    self.string.calculate(stats, datum)
    self.assertEqual(1, stats.count)
    self.assertTrue(hasattr(stats, 'hits'))
    
    self.string.calculate(stats, datum)
    self.assertEqual(2, stats.count)
    self.assertTrue(hasattr(stats, 'hits'))
    
  def test_date_prepare(self):
    tests = [
      ('1242257428', '1242257428'),
      ('2009-05-13 16:31:39', '2009-05-13+16%3A31%3A39')
    ]
    for test in tests:
      expected, raw = test
      self.assertEqual(expected, self.string.prepare(raw))
      
  def test_date_calc(self):
    datum = Object()
    datum.value = '1242257428'
    datum.type = 'timestamp'
    stats = Object()
    
    self.datetime.calculate(stats, datum)
    self.assertEqual(1, stats.count)
    self.assertFalse(hasattr(stats, 'hits'))
    self.assertEqual(1, len(stats['days']))


