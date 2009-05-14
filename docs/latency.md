Latency Experimentation Setup
=============================

Objective
---------
Measure the range of latency between the client and server. 

Definitions
-----------
 - **client**, the software/script/workstation that is not on the Google App Engine infrastructure
 - **server**, the remote Google App Engine infrastructure

Experiments
-----------
### No Load
Derive a baseline latency measurement for no load of the system

### With Load (10%, 25%, 50%, 75%, 90% of bandwidth)
Using various loads on the system (simulating Client contributing data or accessing resources on the campaign) as the system is sending measurements to the server.

Method
------
Utilizing `habwatch.urban.cens.ucla.edu` VM {{specs}}, a python script will create (x) number of threads to simulate incoming campaign contributions which will POST to a local script an image file that represents the highest quality available on a N95 phone. 