import unittest, logging, util

class UtilTest (unittest.TestCase):
  def setUp(self):
    self.test_paths = [
      ('', (None, None)),
      ('visitor', ('visitor', None)),
      ('visitor/olmo', ('visitor', 'olmo')),
      ('visitor/count/1', ('visitor.count', '1')),
      ('visitor/agent/ie', ('visitor.agent', 'ie')),
      ('visitor/agent/ie/1', ('visitor.agent.ie', '1')),
      #('visitor.joined=2009-05-04%2015:11:32.239000', ('visitor.joined', '2009-05-04%2015:11:32.239000'))
    ]
    
  def test_get_parts(self):
    for test in self.test_paths:
      self.failUnlessEqual(util.getParts(test[0]), test[1])