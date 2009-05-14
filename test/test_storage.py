import unittest, logging, util
from google.appengine.ext import db
from google.appengine.api import users

from myapp.models import *

class CMTestCase (unittest.TestCase):
  def setUp(self):
    self.user = users.User('olmo.maldonado@gmail.com')
    self.failUnless(self.user, 'User exists')
    self.campaign = Campaign(name = "Olmo's Campaign", owner = self.user)
    self.failUnless(self.campaign.put(), 'Campaign not created')
    
    logging.info(self.user)
    logging.info('Campaign Key: %s' % self.campaign.key())
  
  def measure(self, namespace, value = 1, v_type = 'number'):
    self.datum = Storage(
      namespace = namespace,
      value = value,
      type = v_type,
      campaign = self.campaign
    )
    logging.info('Datum %s' % self.datum)
    self.failUnless(self.datum.put(), 'Datum not created')

''' Test for collision for
  # Campagin 1
  measure('visitor') # defaults: 1, 'number')
  
  # Campaign 2
  measure('visitor', 'olmo', 'string')
'''
class StorageTest(CMTestCase):    
  ''' Test Logging 1
  measure('visitor.click')
    -> namespace: 'visitor.click'
    -> value: 1
    -> type: 'number'
  '''
  def test_put(self):
    self.measure('visitor.click', 1, 'number')
    
  def test_retrieve(self):
    self.measure('visitor.click', 1, 'number')
    q = Storage.all()
    q.filter('campaign =', self.campaign)
    q.filter('namespace =', 'visitor.click')
    entries = q.fetch(1)
    self.failUnless(entries and entries[0], 'Entry not found')
    
    entry = entries[0]
    logging.info('Storage entry: %s' % entry)
    
    self.assertEqual(1, entry.value)
    self.assertEqual('number', entry.type)
    
  def test_put_string(self):
    self.measure('visitor', 'olmo', 'string')
    
  def test_put_datetime(self):
    from datetime import datetime
    self.measure('visitor.arrived', datetime.now(), 'datetime')