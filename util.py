from google.appengine.ext import db

def generateModel(name, properties = {}, base = db.Model):
    return type(name, (base, ), properties)
