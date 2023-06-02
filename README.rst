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
The resulting repository in ``DATA/`` will take up about 18GB.

Debugging ``HSC/runs/ci_hsc``
-----------------------------

If the run fails on a given task for the primary ``HSC/runs/ci_hsc`` run, you can rerun a specific task in your failed run with the following command (replacing ``taskLabelToRerun`` with the appropriate label from the DRP pipeline):

.. code-block:: bash

    pipetask run -b DATA -j 1 -i HSC/runs/ci_hsc -o u/USER/testing -p "${DRP_PIPE_DIR}/pipelines/HSC/DRP-ci_hsc.yaml#taskLabelToRerun" -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69"

This will pick up the outputs from everything that had been run prior to the task that failed and rerun the task with the output going to a new collection called ``u/USER/testing``.

After fixing any problems, the processing can be resumed with the following command (note the ``..`` at the end of the task label):

.. code-block:: bash

    pipetask run -b DATA -j NPROCESS -i HSC/runs/ci_hsc -o HSC/runs/ci_hsc -p "${DRP_PIPE_DIR}/pipelines/HSC/DRP-ci_hsc.yaml#taskLabelToRerun.." -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69"

Debugging Other Runs
--------------------

If the problem occurs in one of the fakes or faro pipeline runs, the following calls may be of use.

.. code-block:: bash

   pipetask run -b DATA -j 1 -i HSC/runs/ci_hsc_fakes -o u/USER/testing -p "${DRP_PIPE_DIR}/pipelines/HSC/DRP-ci_hsc+fakes.yaml#taskLabelToRerun" -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69"

.. code-block:: bash

   pipetask run -b DATA -j 1 -i HSC/runs/ci_hsc_faro -o u/USER/testing -p "${FARO_DIR}/pipelines/metrics_pipeline.yaml#taskLabelToRerun" -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69"

Cleaning up
-----------
After each run of this test (and, in particular, before re-running it), the repository should be cleaned as follows::

  $ scons --clean

