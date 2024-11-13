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


class TestReprocessVisitImageOutputs(lsst.utils.tests.TestCase, MockCheckMixin):
    """Test the output data products of reprocessVisitImage task make sense.

    This is a regression test and not intended for scientific validation.
    """

    def setUp(self):
        self.butler = Butler(os.path.join(getPackageDir("ci_hsc_gen3"), "DATA"),
                             writeable=False, collections=["HSC/runs/ci_hsc"])
        self.skip_mock()
        self.dataId = {"instrument": "HSC", "detector": 100, "visit": 903334}
        self.exposure = self.butler.get("pvi", self.dataId)
        self.catalog = self.butler.get("sources_footprints_detector", self.dataId)

    def test_schema(self):
        """Test that the schema init-output agrees with the catalog output."""
        schema_cat = self.butler.get("sources_schema")
        self.assertEqual(schema_cat.schema, self.catalog.schema)

    def testLocalPhotoCalibColumns(self):
        """Check that the catalog's photoCalib columns are consistent with the
        ratio of its instFlux and flux columns.
        """
        randomRows = [0, 8, 20]
        for rowNum in randomRows:
            record = self.catalog[rowNum]
            self.assertAlmostEqual(
                record["base_PsfFlux_flux"]/record["base_PsfFlux_instFlux"],
                record['base_LocalPhotoCalib']
            )

    def testLocalWcsColumns(self):
        """Check the exposure's wcs match local wcs columns in the catalog.
        """
        # Check a few rows:
        randomRows = [1, 9, 21]
        for rowNum in randomRows:
            record = self.catalog[rowNum]
            centroid = record.getCentroid()
            trueCdMatrix = np.radians(self.exposure.getWcs().getCdMatrix(centroid))

            self.assertAlmostEqual(record['base_LocalWcs_CDMatrix_1_1'], trueCdMatrix[0, 0])
            self.assertAlmostEqual(record['base_LocalWcs_CDMatrix_2_1'], trueCdMatrix[1, 0])
            self.assertAlmostEqual(record['base_LocalWcs_CDMatrix_1_2'], trueCdMatrix[0, 1])
            self.assertAlmostEqual(record['base_LocalWcs_CDMatrix_2_2'], trueCdMatrix[1, 1])
            self.assertAlmostEqual(
                self.exposure.getWcs().getPixelScale(centroid).asRadians(),
                np.sqrt(np.fabs(record['base_LocalWcs_CDMatrix_1_1']*record['base_LocalWcs_CDMatrix_2_2']
                                - record['base_LocalWcs_CDMatrix_2_1']*record['base_LocalWcs_CDMatrix_1_2'])))


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
