CLEAR CLIMATE CODE GISTEMP README FOR RELEASE 0.4.1

Nick Barnes, Clear Climate Code

$Date$


CONTENTS

  1. Introduction
  2. Dependencies
  3. Installation
  4. Input Data
  5. Running
  6. Results
  7. Regression Testing
  A. References
  B. Document history
  C. Copyright and license

1. INTRODUCTION

This is release 0.4.1 of the Clear Climate Code GISTEMP project
(ccc-gistemp).

Clear Climate Code have reimplemented GISTEMP (the GISS surface
temperature analysis system), to make it clearer.  Work continues
towards making it more clear and more accessible.

ccc-gistemp release 0.4.1 is a release of ccc-gistemp version 0.4.
The purpose of version 0.4 is to increase clarity by:
  - removing rounding;
  - removing intermediate I/O;
  - gathering and documenting parameters in parameters.py;
  - general code clarification.

Changes since earlier releases are described in more detail in
release-notes.txt.

URLs for further information:

http://clearclimatecode.org/ Clear Climate Code website and blog.
http://ccc-gistemp.googlecode.com/ ccc-gistemp code repository.


2. DEPENDENCIES

The only dependency is Python 2.5 (or a more recent Python version).
Python 2.4 was supported for previous releases but has now been dropped.
The code should run on OS X, FreeBSD, Windows, and probably a variety of
other Unix-like operating systems.  A network connection is required to
download the input files (which need only be done once), and to display
an optional graph from the results.

Python may already be installed on your machine (for example, it comes
pre-installed on OS X), it may be possible to install it using your
operating system's package manager; for Windows you can download an
installer from http://www.python.org/download/ .  We recommend you use a
stable production release from the Python 2.x series (Python 3.x will
not work).


3. INSTALLATION

Unpack ccc-gistemp-0.4.1.tar.gz.


4. INPUT DATA

ccc-gistemp-0.4.1 uses input data in the subdirectory input/.  This
input data includes large files of temperature records from GHCN,
USHCN, and sea surface data, and small files of additional temperature
records and station tables from GISS.  ccc-gistemp-0.4.1 includes code
(tool/preflight.py) to fetch this data from the originating
organisations over the internet.  It will not download a file if it is
already present in the input/ directory, so if you wish to run
ccc-gistemp with updated input data, you can delete the input/
directory before you start.


5. RUNNING

To run ccc-gistemp:

    python tool/run.py

That command runs steps 0 through 5.  To run only a single step or a shorter
sequence of steps, use the -s argument.  For instance:

    python tool/run.py -s 3         # Runs just step 3
    python tool/run.py -s 0-3,5     # Runs steps 0,1,2,3,5 (omitting 4)

We use this directory structure:

ccc-gistemp-x.x.x/code/     Source code for the GISTEMP algorithm only
                 /config/   Configuration files
                 /doc/      Internal developer documentation
                 /input/    Input data files
                 /log/      Log files
                 /tool/     Tools - sources other than the GISTEMP algorithm
                 /work/     Intermediate data files
                 /result/   Final result files

Running the code should write to the input/ directory when fetching
input data, but subsequently only write to the work/ log/ and result/
directories.  Before running tool/run.py, these directories can all be
deleted (if you wish, for example, to have a clean run).


6. RESULTS

After running run.py, the GISTEMP result files are all in the result/
directory.  A simple graphical chart is made using the Google Chart
API; this file:

    result/google-chart.url

contains the URL of a chart showing the global annual mean surface
temperature anomaly.

If you have the results of two separate runs in two different
directories, old-result/ and new-result/ , then an HTML report comparing
the two can be generated with this command:

    python tool/compare_results.py --labela=old --labela=new old-result new-result

This will produce a file called index.html in the current directory,
including various statistical comparisons of the two result files.


7. REGRESSION TESTING

To test ccc-gistemp against GISTEMP:

    python tool/regression.py

This will fetch a tarball from
http://ccc-gistemp.googlecode.com/files/ccc-gistemp-test-2009-12-28.tar.gz
and uncompress it to a local directory ccc-gistemp-test-2009-12-28/.
This contains input files and result data kindly provided to the
ccc-gistemp project by Dr Reto Ruedy of NASA GISS, from an actual run
of GISTEMP at GISS on 2009-12-28.  Once the tarball is fetched and
unpacked, the local ccc-gistemp code will be run on it and the results
compared, generating a report in index.html.

Note that there are indeed some changes between the results of the
reference run and 0.4.1, mainly caused by a change to the GISTEMP
algorithm, for rural/urban station distinction, made at GISS since the
reference run.  We have replicated that change in ccc-gistemp (see
http://ccc-gistemp.googlecode.com/issues/detail?id=54).  To test
ccc-gistemp running the same algorithm as the reference GISTEMP run,
edit code/parameters.py to set use_global_brightness = False before
running tool/regression.py.


A. REFERENCES

None.


B. DOCUMENT HISTORY

Most recent changes first:

2010-03-11 DRJ Updated to prepare for 0.4.1.
2010-03-09 DRJ Updated to prepare for 0.4.0.
2010-01-26 NB  Updated to prepare for 0.3.0.
2010-01-25 DRJ Removed PNG result.
2010-01-22 NB  Updated to reflect some code moving to tool/.
2010-01-11 NB  Updated to describe preflight better.
2010-01-06 DRJ Updated for our all-Python status.
2009-12-03 NB  Updated for transfer to GoogleCode project.
2008-09-19 DRJ Added PNG result.
2008-09-13 NB  Updated for CCC 0.1.0.
2008-09-12 NB  Updated for CCC 0.0.3.
2008-09-12 NB  Updated for CCC 0.0.2.
2008-09-11 NB  Updated for CCC 0.0.1.
2008-09-08 NB  Created.

C. COPYRIGHT AND LICENSE

This document is copyright (C) 2009, 2010 Ravenbrook Limited.  All
rights reserved.

Redistribution and use of this document in any form, with or without
modification, is permitted provided that redistributions of this
document retain the above copyright notice, this condition and the
following disclaimer.

THIS DOCUMENT IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDERS AND CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
DOCUMENT, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

$URL$
$Rev$
