import os
import unittest

import lsst.pipe.base as pipeBase
import lsst.utils.tests


class PipelineLoadSubsetTest(unittest.TestCase):
    def testLoadList(self):
        """This function tests loading a specific list of labels
        """
        labels = ("charImage", "calibrate", "makeWarpTask")
        path = os.path.expandvars(f"$CI_HSC_GEN3_DIR/pipelines/CiHsc.yaml:{','.join(labels)}")
        pipeline = pipeBase.Pipeline.fromFile(path)
        self.assertEqual(set(labels), pipeline._pipelineIR.tasks.keys())

    def testLoadSingle(self):
        """This function tests loading a specific label
        """
        label = "charImage"
        path = os.path.expandvars(f"$CI_HSC_GEN3_DIR/pipelines/CiHsc.yaml:{label}")
        pipeline = pipeBase.Pipeline.fromFile(path)
        self.assertEqual(set((label,)), pipeline._pipelineIR.tasks.keys())

    def testLoadBoundedRange(self):
        """This function tests loading a bounded range
        """
        path = os.path.expandvars("$CI_HSC_GEN3_DIR/pipelines/CiHsc.yaml:charImage..assembleCoadd")
        pipeline = pipeBase.Pipeline.fromFile(path)
        self.assertEqual(set(('charImage', 'calibrate', 'makeWarpTask', 'assembleCoadd')),
                         pipeline._pipelineIR.tasks.keys())

    def testLoadUpperBound(self):
        """This function tests loading a range that only has an upper bound
        """
        path = os.path.expandvars("$CI_HSC_GEN3_DIR/pipelines/CiHsc.yaml:..assembleCoadd")
        pipeline = pipeBase.Pipeline.fromFile(path)
        self.assertEqual(set(('isr', 'charImage', 'calibrate', 'makeWarpTask', 'assembleCoadd')),
                         pipeline._pipelineIR.tasks.keys())

    def testLoadLowerBound(self):
        """This function tests loading a range that only has an upper bound
        """
        path = os.path.expandvars("$CI_HSC_GEN3_DIR/pipelines/CiHsc.yaml:mergeDetections..")
        pipeline = pipeBase.Pipeline.fromFile(path)
        self.assertEqual(set(('mergeDetections', 'deblend', 'measure', 'mergeMeasurements', 'forcedPhotCcd',
                             'forcedPhotCoadd')),
                         pipeline._pipelineIR.tasks.keys())

    def testLabelChecks(self):
        # test a bad list
        path = os.path.expandvars("$CI_HSC_GEN3_DIR/pipelines/CiHsc.yaml:FakeLabel")
        with self.assertRaises(ValueError):
            pipeBase.Pipeline.fromFile(path)

        # test a bad end label
        path = os.path.expandvars("$CI_HSC_GEN3_DIR/pipelines/CiHsc.yaml:..FakeEndLabel")
        with self.assertRaises(ValueError):
            pipeBase.Pipeline.fromFile(path)

        # test a bad begin label
        path = os.path.expandvars("$CI_HSC_GEN3_DIR/pipelines/CiHsc.yaml:FakeBeginLabel..")
        with self.assertRaises(ValueError):
            pipeBase.Pipeline.fromFile(path)

    def testContractRemoval(self):
        path = os.path.expandvars("$CI_HSC_GEN3_DIR/pipelines/CiHsc.yaml")
        pipeline = pipeBase.Pipeline.fromFile(path)
        contract = pipeBase.pipelineIR.ContractIR("forcedPhotCcd.doApplyExternalPhotoCalib == False", None)
        pipeline._pipelineIR.contracts.append(contract)
        pipeline = pipeline.subsetFromLabels(pipeBase.LabelSpecifier(labels=set(("isr",))))
        self.assertEqual(len(pipeline._pipelineIR.contracts), 0)


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
