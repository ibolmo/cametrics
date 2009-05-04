class Histogram (db.Expando):
    pass
    
class HitsHistogram (Histogram):
    pass
    
class Statistics (db.Model):
    first = db.ReferenceProperty(collection_name = "first")
    last = db.ReferenceProperty(collection_name = "last")
    hits = db.ReferenceProperty(HitsHistogram, collection_name = "hits")
    
class FloatStatistics (Statistics):
    min = db.FloatProperty()
    max = db.FloatProperty()
    mean = db.FloatProperty()
    sum = db.FloatProperty()
    # ...

class StringStatistics (Statistics):
    pass

class Datum (db.Model):
    created_at = db.DateTimeProperty(auto_now = True)
    statistics = db.ReferenceProperty()

class FloatDatum(Datum):
    value = db.FloatProperty(required = True)

class StringDatum(Datum):
    value = db.StringProperty(required = True)


''' Generated Models

The following will eventually be generated on-the-fly and saved/retrieved from data store for each organizer
'''
class Vistor (FloatDatum):
    pass
    
class Click (FloatDatum):
    pass

class X (FloatDatum):
    pass

class Agent (StringDatum):
    pass