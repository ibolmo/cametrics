import unittest, logging, util
from google.appengine.ext import db

from models import *

''' Test for collision for
  # Campagin 1
  measure('visitor') # defaults: 1, 'number')
  
  # Campaign 2
  measure('visitor', 'olmo', 'string')
'''
class ModelTest(unittest.TestCase):
  def setUp(self):
    # Generate 
    self.Visitor1 = util.generateModel('Visitor', base = FloatDatum)
    entity = self.Visitor1(value = 1)
    self.setup_key1 = entity.put()

  def tearDown(self):
    # There is no need to delete test entities.
    pass

  def test_entity_saved(self):
    entity = db.get(self.setup_key1)
    self.assertEqual(1, entity.value)

  def test_new_visitor(self):
    self.Visitor2 = util.generateModel('Visitor', base = StringDatum)
    entity = self.Visitor2(value = 'olmo')
    self.setup_key2 = entity.put()

  def test_both_exist(self):
    entity1 = db.get(self.setup_key1)
    entity2 = db.get(self.setup_key2)
    self.assertEqual(1, entity1.value)
    self.assertEqual('olmo', entity2.value)