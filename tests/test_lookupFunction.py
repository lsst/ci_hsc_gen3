import os
import unittest

import lsst.daf.butler as dafButler
import lsst.pipe.base as pipeBase
import lsst.utils.tests

from lsst.utils import getPackageDir


class PrerequisiteLookupFunctionTestException(Exception):
    """An exception class to clearly identify when an unexpected situation
    has occurred in the test for prerequisite input lookup functions.
    """
    pass


def lookupFunctionTester(datasetType, registry, quantumDataId, collections):
    """This function verifies that there are datasetRefs to brighter fatter
    kernels present in the registry, but returns an empty iterable as if
    there were none.
    """
    results = list(registry.queryDatasets(datasetType,
                                          collections=collections,
                                          dataId=quantumDataId,
                                          deduplicate=True,
                                          expand=True))
    # Verify that brighter fatter kernels could be found in the registry
    # as to not have this test pass due to some unrelated error
    if len(results) == 0:
        raise PrerequisiteLookupFunctionTestException(
            "No bfKernels found in registry, but there should be some")
    # instead of returning the datasetRefs, return something clearly different,
    # an empty tuple
    return ()


class LookupTestConnections(pipeBase.PipelineTaskConnections,
                            dimensions=("instrument",)):
    """A simple dummy connections class to exercise the lookupFunction
    functionality of a prerequisite input.
    """
    testInput = pipeBase.connectionTypes.PrerequisiteInput(
        name="bfKernel",
        storageClass="NumpyArray",
        doc="test a lookup function",
        lookupFunction=lookupFunctionTester,
        dimensions=("instrument", "calibration_label"),
    )


class LookupTestConfig(pipeBase.PipelineTaskConfig, pipelineConnections=LookupTestConnections):
    """A simple dummy config class to exercise the lookupFunction functionality
    of a prerequisite input.
    """
    pass


class LookupTestPipelineTask(pipeBase.PipelineTask):
    """A simple dummy PipelineTask to exercise the lookupFunction functionality
    of a prerequisite input.
    """
    ConfigClass = LookupTestConfig


class PrerequisiteConnectionLookupFunctionTest(unittest.TestCase):
    def testPrerequisiteLookupFunction(self):
        """This tests that a lookup function defined on a prerequisite input
        is called when building a quantum graph.
        """
        butler = dafButler.Butler(os.path.join(getPackageDir("ci_hsc_gen3"), "DATA", "butler.yaml"))

        pipeline = pipeBase.Pipeline("Test LookupFunction Pipeline")
        pipeline.addTask(LookupTestPipelineTask, "test")

        graphBuilder = pipeBase.GraphBuilder(butler.registry)
        graph = graphBuilder.makeGraph(pipeline, ["calib/hsc", "shared/ci_hsc_output"],
                                       None, None)
        outputs = list(graph.quanta())
        # verify the graph contains no datasetRefs for brighter fatter kernels
        # instead of the datasetRefs that exist in the registry.
        numberOfInputs = len(outputs[0][1].predictedInputs['bfKernel'])
        self.assertEqual(numberOfInputs, 0)


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
