helen
=====

A job launcher for NEMORB/maybe other codes

The aim of this project is to create a job launcher which can do n-dimensional parameter scans using a fortran code.
There will be (at least) two parts:
      the first part will create some sort of namelist object, which knows about all the possible input parameters and their possible values.
      the second part will allow the user to specify n of those parameters and what range the scan should be over, and then generate the input files (and any necessary meta-data).

Maybe also launch the jobs? Remotely/locally?
Would be nice to eventually do all/some of the processing afterwards too!
