Name
====
Still in progress.

### Candidates
 - Campaign Meter
 - Meter
 - Info, for "informatics"
 - Webbug, see: Firebug
 - Measure

Ontology
--------
All things related to models, objects, or classes and their respected statistics that are auto incremented/decremented/updated.

### Date
 - value
 - timestamp
 - statistics
    - first (date)
    - last (date)
    - frequency
    - weekday (histogram)
    - hour (histogram)

### Location
 - longitude
 - latitude
 - statistics
    - first (location)
    - last (location)
    - area
    - centroid
    - boundary
    - box (histogram)

### Number
 - value
 - statistics 
    - first (number)
    - last (number)
    - min
    - max
    - mean
    - sum
    - deviation
    - mode_id
    - median
    - unit (histogram) (0.1, 1, 10, ...)

### String
 - value
 - length (number)
 - statistics
    - first (string)
    - last (string)
    - values (histogram)
 
### Interval
 - start (date)
 - stop (date)
 - duration (number)
 - statistics
    - first (interval)
    - last (interval)

### Histogram
 - bins
 - statistics
    - count

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
The following map/alias between different kind of inputs

 - timestamp -> Date

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