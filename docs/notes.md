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

Output/Visualization
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
all                         | Storage.fetch(1000) | Statistic.get | 
key/namespace               | to_dict(values) + to_dict_stats |
key/namespace/values        | to_dict(values) |
key/namespace/stats         | to_dict(stats) |
key/namespace...gc|gchart   |

### Goal
Memoize the visualization. As data comes in the visualization should be updated and cached. Preferrably one mecache call per request. Problem, though, is utility of visualization -- opportunity cost. Being able to cache everything is not necessarily useful if people are not requesting the visualization. Ideally, the visualization should be saved only if it is popular and/or very expensive.



Questions
---------

### What is the exact way to create static columns/attributes for a class/model?

### What will I do if parent type changes, from float to string (as a cause of measure('parent', 'olmo', 'string'))?

### What is the correct way to hook into the insert/update/etc so for the statistics and histograms?