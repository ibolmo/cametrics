Name
====
Cametrics

Types
-----
 - none (no statistics, no type)
 - elevation (altitude)
 - zipcode
 - city
 - country
 - accuracy
 - binary (true|false)
 - temperature
 - counter
 - choice
 
Modify Statistics
-----------------
Sometimes it would be useful to modify statistics to exclude certain statistics. The following are examples of such filters. Concept from Django Template Filters.

`type|filters`

### Filters
 - off, no statistics
  - number|off


Ontology
--------
All things related to models, objects, or classes and their respected statistics that are auto incremented/decremented/updated. The '**\***' items are not yet implemented. The '**?**' items are unverified for appropiateness.

### Base (common for all types)
 - value
 - created_on
 - statistics
  - first
  - last

### Datetime*
 - timestamp
 - statistics
    - frequency
    - day\_of\_week (histogram)
    - hour (histogram)

### Location*
 - longitude
 - latitude
 - elevation?
 - statistics
    - area
    - centroid
    - boundary
    - box (histogram)

### Number
 - statistics 
    - min
    - max
    - mean
    - sum
    - deviation*
    - mode*
    - median*
    - unit (histogram) (0.1, 1, 10, ...)*

### String
 - length (number)
 
### Interval*
 - start (date)
 - stop (date)
 - duration (number)

Events
------
Web hooks can be attached for when an event (for a namespace) occurs. Supports standard HTTP methods and position conditions (pre- and post- execution of the method).

    # attach(namespace, callback_uri[, method = post|get|put|delete[, condition = post|pre);
    attach(namespace, callback_uri)

    # detach([namespace, callback_uri[, method = post|get|put|delete[, condition = post|pre]]);
    detach(namespace, callback_uri, 'get', 'post')
    detach()

Map
---
The following map/alias between different type of inputs

 - timestamp -> date
 - datetime -> date
 - int -> number
 - integer -> number
 - float -> number
 - long -> number
 - text -> string
 - str -> string
 - gps -> location
 

Usage
-----
 - The namespace should be delimited by (any number of) non-alpha (for example: `/[^\w]*/`) characters
 - Array inputs (for the namespace), will be joined by '.'

### Examples

    # measure(namespace[, value = 1[, type = number]]);  
    
    measure('execution.start', 1240869175, 'timestamp');
    measure('visitor::click');
    measure(['participant', guid('ibolmo@gmail.com'), 'join']);
    
    # measure.start|pause|resume|stop(namespace)

GUID
----
Globally Unique Identifier can be useful for namespacing to get a specific measurement for an object that is known to the campaign but is anonymous to the system. For example, I can track a user's data quality without implicating the user in the backend. 

Thoughts
--------
 - Olmo: Assuming: we have a good breadth of (statistical) processings for different objects, then incr/decr operations may not be necessary
  - Olmo: Would be interesting to support abritrary/other actions, though.
 - Olmo: Would be interesting to have statistics local to a grouping.
 - Sasank: Delete all data for a campaign
 - Sasank: Delete all data for a namespace
 - Sasank: Query for specific stats, including filtering for withtin a boundary