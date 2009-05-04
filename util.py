import re
from google.appengine.ext import db

def generateModel(name, properties = {}, base = db.Model):
  return type(name, (base, ), properties)


def getParts(path):
  ns = value = None
  if (not re.search('/', path)):
    ns = path or None
  else:
    value = re.search(r'([^/]+)$', path).group(0)
    ns = path[:-(len(value)+1)] or None
  
  return (ns and ns.replace('/', '.'), value)