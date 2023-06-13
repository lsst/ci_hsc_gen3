# This file is part of ci_hsc_gen3.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import unittest

import lsst.utils.tests

from lsst.ci.hsc.gen3 import PSF_MODEL_ROBUSTNESS_FAILURE_DATA_IDS
from lsst.daf.butler import Butler, DataCoordinate
from lsst.utils import getPackageDir


class TestPsfModelTraceRadiusFails(lsst.utils.tests.TestCase):
    """Test the deselection of detectors based on PSF model robustness check.
    """
    def setUp(self):
        self.butler = Butler(os.path.join(getPackageDir("ci_hsc_gen3"), "DATA"), writeable=False,
                             collections=["HSC/calib/2013-06-17", "HSC/runs/ci_hsc"])
        self.skymap = "discrete/ci_hsc"
        self.tract = 0
        self.patch = 69
        self.band = "r"
        self.coaddDataId = DataCoordinate.standardize(
            instrument="HSC", skymap=self.skymap, tract=self.tract, patch=self.patch, band=self.band,
            universe=self.butler.dimensions,
        )

    def tearDown(self):
        del self.butler
        del self.skymap
        del self.tract
        del self.patch
        del self.band
        del self.coaddDataId

    def testFailedPsfTraceRadiusDeltaNotInCoadd(self):
        """Check that the detectors failing the maxPsfTraceRadiusDelta
        criterion are not included in the coadd.
        """
        coadd = self.butler.get("deepCoadd_calexp", self.coaddDataId)
        inputCcds = coadd.getInfo().getCoaddInputs().ccds
        for failedDataId in PSF_MODEL_ROBUSTNESS_FAILURE_DATA_IDS:
            visit = failedDataId["visit"]
            detector = failedDataId["detector"]
            failedMask = (inputCcds["visit"] == visit) & (inputCcds["ccd"] == detector)
            self.assertTrue(sum(failedMask) == 0)


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
