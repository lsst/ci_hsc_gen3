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
import numpy as np
from lsst.ci.hsc.gen3.tests import MockCheckMixin
from lsst.daf.butler import Butler
from lsst.utils import getPackageDir


class TestCalibrateOutputs(lsst.utils.tests.TestCase, MockCheckMixin):
    """Test the output data products of calibrate task make sense

    This is a regression test and not intended for scientific validation
    """

    def setUp(self):
        self.butler = Butler(os.path.join(getPackageDir("ci_hsc_gen3"), "DATA"),
                             writeable=False, collections=["HSC/runs/ci_hsc"])
        self.skip_mock()
        self.dataId = {"instrument": "HSC", "detector": 100, "visit": 903334}
        self.calexp = self.butler.get("calexp", self.dataId)
        self.src = self.butler.get("src", self.dataId)

    def testLocalPhotoCalibColumns(self):
        """Check calexp's calibs are consistent with src's photocalib columns
        """
        # Check that means are in the same ballpark
        calexpCalib = self.calexp.getPhotoCalib().getCalibrationMean()
        calexpCalibErr = self.calexp.getPhotoCalib().getCalibrationErr()
        srcCalib = np.mean(self.src['base_LocalPhotoCalib'])
        srcCalibErr = np.mean(self.src['base_LocalPhotoCalibErr'])

        self.assertAlmostEqual(calexpCalib, srcCalib, places=3)
        self.assertAlmostEqual(calexpCalibErr, srcCalibErr, places=3)

        # and that calibs evalutated at local positions match a few rows
        randomRows = [0, 8, 20]
        for rowNum in randomRows:
            record = self.src[rowNum]
            localEval = self.calexp.getPhotoCalib().getLocalCalibration(record.getCentroid())
            self.assertAlmostEqual(localEval, record['base_LocalPhotoCalib'])

    def testLocalWcsColumns(self):
        """Check the calexp's wcs match local wcs columns in src
        """
        # Check a few rows:
        randomRows = [1, 9, 21]
        for rowNum in randomRows:
            record = self.src[rowNum]
            centroid = record.getCentroid()
            trueCdMatrix = np.radians(self.calexp.getWcs().getCdMatrix(centroid))

            self.assertAlmostEqual(record['base_LocalWcs_CDMatrix_1_1'], trueCdMatrix[0, 0])
            self.assertAlmostEqual(record['base_LocalWcs_CDMatrix_2_1'], trueCdMatrix[1, 0])
            self.assertAlmostEqual(record['base_LocalWcs_CDMatrix_1_2'], trueCdMatrix[0, 1])
            self.assertAlmostEqual(record['base_LocalWcs_CDMatrix_2_2'], trueCdMatrix[1, 1])
            self.assertAlmostEqual(
                self.calexp.getWcs().getPixelScale(centroid).asRadians(),
                np.sqrt(np.fabs(record['base_LocalWcs_CDMatrix_1_1']*record['base_LocalWcs_CDMatrix_2_2']
                                - record['base_LocalWcs_CDMatrix_2_1']*record['base_LocalWcs_CDMatrix_1_2'])))


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
