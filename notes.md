cmd /K "dev_appserver \www\cm -p 80 -c"

Use Cases
---------

## Use 1
    measure('visitor')
    measure('visitor.click')
    measure('visitor.click.x', 44.3)
    measure('visitor.agent', 'ie', 'string')

### Expected (json) object-tree

    visitor:
        values: [1]
        statistics (NumberStatistics):
        
        click:
            values: [1]
            statistics (NumberStatistics):
            
            x:
                values: [44.3]
                statistics (NumberStatistics):
        agent:
            values: ['ie']
            statistics (StringStatistics):
                
### Expected Class-tree (entitiy group)

    Visitor (FloatDatum):
        value = db.FloatProperty(required = True)
        statistics = VisitorStatistics
        
        click (FloatDatum):
            value = db.FloatProperty(required = True)
            statistics = ClickStatistics
            
            x (FloatDatum):
                statistics = FloatStatistics
        
        agent (StringDatum):
            value = db.StringPropety(required = True)
            statistics = AgentStatistics

### (Tested) Expected Classes
    class Datum (db.Model):
        created_at = db.DateTimeProperty(auto_now = True)
        statistics = db.ReferenceProperty()
    
    class Histogram (db.Expando):
        pass
    
    class HitsHistogram (Histogram):
        pass
    
    class Statistics (db.Model):
        first = db.ReferenceProperty(collection_name = "first")
        last = db.ReferenceProperty(collection_name = "last")
        hits = db.ReferenceProperty(HitsHistogram, collection_name = "hits")
    
    class FloatDatum(Datum):
        value = db.FloatProperty(required = True)
    
    class FloatStatistics (Statistics):
        min = db.FloatProperty()
        max = db.FloatProperty()
        mean = db.FloatProperty()
        sum = db.FloatProperty()
        # ...
    
    class StringDatum(Datum):
        value = db.StringProperty(required = True)
    
    class StringStatistics (Statistics):
        pass
    
    # Generated/looked-up
    class Vistor (FloatDatum):
        pass
    
    class Click (FloatDatum):
        pass
    
    class X (FloatDatum):
        pass
    
    class Agent (StringDatum):
        pass
-----

Questions
---------

### Will I get datastore collisions for same kind for different campaigns?
For example,
    
    # Campaign 1
    measure('visitor', 1)
        
    # Campaign 2
    measure('visitor', 'olmo')


### Can I set the parent/(entity group) within the class definition?

### Can I change a kind's class definition?

### Does db.*Property() have clone method? This way I can define a global property set and just clone?

### What is the exact way to create static columns/attributes for a class/model?

### What will I do if parent type changes, from float to string (as a cause of measure('parent', 'olmo', 'string'))?

### What are the python rule for class names? These rules will dictate the column naming rules. For reserved words, use `_{input} = *(*, name = "{input}")`

### What is the correct way to hook into the insert/update/etc so for the statistics and histograms?

### Do I need to save the classes to the datastore?
    Yes, for retrieving using the namespace, you will lose the type for the namespace/val. 