cmd /K "dev_appserver \www\cm -p 80"

Use Cases
---------

### Use 1
    measure('visitor')
    measure('visitor.click')
    measure('visitor.click.x', 44.3)
    measure('visitor.agent', 'ie', 'string')

#### Expected (json) object-tree

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

-----

Query
-----

### Uses
    get('parent.child.subchild') => parent/child/subchild
    get('parent.child.subchild.stats') => parent/child/subchild/stats
    get('parent.child.subchild.stats.column') => parent/child/subchild/stats/column
    get('parent.child.subchild.stats.column', 'format') => parent/child/subchild/stats/column.format


----------

Output Rendering
-------------

### Variations
key/namespace                             -> dict with values and stats (see below)
key/namespace/values                      -> list of values entered
key/namespace/stats                       -> dict with (for now) stats computed
key/namespace/stats/column                -> typically a single value
key/namespace/stats/histogram             -> dict with key/value pairs. key for the label and value for the bar

key/namespace/values.gc|gchart            -> typically scatterplot or line graph
key/namespace/stats/histogram.gc|gchart   -> uses dict to create a histogram representation

#### Most expensive
As of 5/20:

    all                         | Storage.fetch(1000), Statistic.get
    key/namespace                                                   \ to_dict(values) + to_dict(stats) (see below)
                                                                     \ to_entity, replace_datastore_types, to_entity, replace_datastore_types, Histogram.get, json_dump
                                                                     
    key/namespace/values                                            \ to_json(values)
                                                                     \ to_entity, replace_datastore_types
                                                                     
    key/namespace/stats                                             \ to_dict(stats)
                                                                     \ to_entity, replace_datastore_types, Histogram.get
                                                                     
    key/namespace/values.gc|gchart                                  \ get_values, populate chxl and chd
                                                                    
    key/namespace/stats/histogram.gc|gchart                         \ get_values, to_dict,                                             find_for_path, populate chxl and chd
                                                                                  \ replace_datastore_types, Histogram.get, json_dump /

### Goal
Memoize the visualization. As data comes in the visualization should be updated and cached. Preferrably one mecache call per request. Problem, though, is utility of visualization -- opportunity cost. Being able to cache everything is not necessarily useful if people are not requesting the visualization. Ideally, the visualization should be saved only if it is popular and/or very expensive.

### Optimizing
1. Instead of Histogram being a list of keys, convert a counter

Visualization
-------------
For:

    GET something/stats/histogram.gc
        something/values.gc

### What is appropiate for the type?
 type     |  values | histogram
----------|-------------------
 number   | scatter | bar
          | line    |
 location | map     |
 ...
 
### Better yet, which types fit with the type of chart?
line
 - number:values
 - buckets
bar
 - number:values
 - buckets
pie
 - [value / sum * 100 for value in values]
 - [bucket / count * 100 for bucket in buckets]
venn
scatter
 - number: values
 - if strings had length, could show the scatter map of lengths?
radar
maps
google-o-meter
QR codes
 
### Deduction
There's a many-to-many relationship, or possible combinations, between a type and a visualization. Question is: how to provide an open environment to code visuals?

Currently: some-data-uri.gc?gchart\_query\_string

If no gchart\_query\_string, use default. But what does this default mean? Default should mean, what's the simplest way to visualize the data. For this we need to look at the **datum.type**. Depending on type, one can then invoke the necessary function to return the correct gchart uri. Otherwise, use the provided gchart type as access to the necessary function to prepare the uri.

Questions
---------

### What is the exact way to create static columns/attributes for a class/model?

### What will I do if parent type changes, from float to string (as a cause of measure('parent', 'olmo', 'string'))?

### What is the correct way to hook into the insert/update/etc so for the statistics and histograms?