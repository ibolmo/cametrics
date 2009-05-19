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

Questions
---------

### What is the exact way to create static columns/attributes for a class/model?

### What will I do if parent type changes, from float to string (as a cause of measure('parent', 'olmo', 'string'))?

### What is the correct way to hook into the insert/update/etc so for the statistics and histograms?