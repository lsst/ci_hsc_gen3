######
ci_hsc
######

``ci_hsc`` provides scripts which use the LSST stack to perform single frame and coadd processing based on engineering test data from Hyper Suprime-Cam.

Obtaining test data
===================

``ci_hsc`` uses the the files in `testdata_ci_hsc`_ to run its tests.
That package must be setup first, before running ``scons`` (see below).

.. _testdata_ci_hsc: https://github.com/lsst/testdata_ci_hsc/

Running the tests
=================

Set up the package
------------------

Both `testdata_ci_hsc`_ both and ``ci_hsc`` must be setup in eups in order to run the tests in this package.
One way to accomplish this is as follows::

  $ cd PATH_TO_TESTDATA_CI_HSC
  $ setup -r .
  $ cd PATH_TO_CI_HSC
  $ setup -kr .


Running the tests
-----------------

Execute ``scons -jN``, where ``N`` is the number of CPU cores to use.
Note that running these tests can take a few hours, depending on the speed of your machine and the number of cores available.

This will create a butler repository at ``DATA/``, ingest the raw data into ``HSC/raw/all``, create a chained ``HSC/defaults`` collection for all of the input data, and write the output of the pipeline run to ``HSC/runs/ci_hsc``.
It will also run various checks of the data integrity of the processed output.

Cleaning up
-----------
After each run of this test, and before the next the repository should be cleaned as follows (with appropriate
modifications for MacOs::
 $ scons --clean
