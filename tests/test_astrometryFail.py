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

import numpy as np
import os
import unittest

import lsst.utils.tests

from lsst.daf.butler import Butler, DataCoordinate
from lsst.utils import getPackageDir
from lsst.ci.hsc.gen3 import ASTROMETRY_FAILURE_DATA_IDS


class TestAstrometryFails(lsst.utils.tests.TestCase):
    """Tests the outputs of the forced astrometry failures.
    """
    def setUp(self):
        self.butler = Butler(os.path.join(getPackageDir("ci_hsc_gen3"), "DATA"), writeable=False,
                             collections=["HSC/calib/2013-06-17", "HSC/runs/ci_hsc"])
        # The dataId here represents one of the astrometry fit failures
        # imposed by setting astrometry.maxMeanDistanceArcsec: 0.0228 in
        # the pipeline.
        self.detector = ASTROMETRY_FAILURE_DATA_IDS[0]["detector"]
        self.visit = ASTROMETRY_FAILURE_DATA_IDS[0]["visit"]
        self.calexpMinimalDataId = DataCoordinate.standardize(
            instrument="HSC", detector=self.detector, visit=self.visit,
            universe=self.butler.dimensions,
        )

    def testWcsAndPhotoCalibIsNoneForFailedAstrom(self):
        """Test the WCS and photoCalib objects attached to failed WCS exposure.

        An exposure with a failed astrometric fit should have WCS and
        photoCalib set to None.
        """
        calexp = self.butler.get("calexp", self.calexpMinimalDataId)
        self.assertTrue(calexp.getWcs() is None)
        self.assertTrue(calexp.getPhotoCalib() is None)

        calexpWcs = self.butler.get("calexp.wcs", self.calexpMinimalDataId)
        self.assertTrue(calexpWcs is None)

        calexpPhotoCalib = self.butler.get("calexp.photoCalib", self.calexpMinimalDataId)
        self.assertTrue(calexpPhotoCalib is None)

    def testSrcCoordsAreNanForFailedAstrom(self):
        """Test coord values in all source catalogs.

        The coord values in the src catalogs, i.e. the results from SFM,
        should all be `numpy.nan` for a failed astrometric fit.  However,
        when applying external calibrations, the coordinates can indeed get
        successfully "reevaluated" if the associated calibration does indeed
        exist (this is to allow for the external calibrations to potentially
        "recover" from a failed SFM astrometric fit).  In this case, those
        files do indeed exist in the ci_hsc_gen3 repo, so the ``sourceTable``
        catalogs will have valid coord entries.
        """
        sourceCat = self.butler.get("src", self.calexpMinimalDataId)
        self.assertTrue(np.all(np.isnan(sourceCat["coord_ra"])))
        self.assertTrue(np.all(np.isnan(sourceCat["coord_dec"])))
        for catStr in ["sourceTable"]:
            sourceCat = self.butler.get(catStr, self.calexpMinimalDataId)
            self.assertFalse(np.all(np.isnan(sourceCat["coord_ra"])))
            self.assertFalse(np.all(np.isnan(sourceCat["coord_dec"])))

    def testCentroidsAreNotNanForFailedAstrom(self):
        """Test that at least some src catalog centroids have finite values.

        The coord values in the src catalogs, i.e. the results from SFM,
        should all be `numpy.nan` for a failed astrometric fit.  However,
        the centroid x and y values should have (at least some) valid entries.
        This is also true for the ``preSource`` and ``preSourceTable``
        catalogs, so check those as well.
        """
        for catStr in ["src", "preSource"]:
            sourceCat = self.butler.get(catStr, self.calexpMinimalDataId)
            self.assertFalse(np.all(np.isnan(sourceCat["slot_Centroid_x"])))
            self.assertFalse(np.all(np.isnan(sourceCat["slot_Centroid_y"])))
        for catStr in ["preSourceTable"]:
            sourceCat = self.butler.get(catStr, self.calexpMinimalDataId)
            self.assertFalse(np.all(np.isnan(sourceCat["x"])))
            self.assertFalse(np.all(np.isnan(sourceCat["y"])))

    def testVisitCoordsAreNanForFailedAstrom(self):
        """Test coord and astrom values for visitTable and visitSummary.

        The coord values in the visitTable should be finite, but those
        associated with the failed detector in the visitSummary should be
        set to `numpy.nan`.  If the fitter converged, the astrometry metrics
        in the visitSummary should be finite even if the fit was deemed a
        falilure according to the value of the maxMeanDistanceArcsec config.
        """
        visitTable = self.butler.get("visitTable", self.calexpMinimalDataId)
        self.assertTrue(np.all(np.isfinite(visitTable["ra"])))

        visitSummary = self.butler.get("visitSummary", self.calexpMinimalDataId)
        row = visitSummary.find(self.detector)
        self.assertTrue(np.isfinite(row["astromOffsetMean"]))
        self.assertTrue(np.isfinite(row["astromOffsetStd"]))
        self.assertTrue(np.all(np.isnan(row["raCorners"])))
        self.assertTrue(np.all(np.isnan(row["decCorners"])))

    def testMetadataForFailedAstrom(self):
        """Test that the metadata for a failed astrometic fit is set properly.

        If the fitter converged, the astrometry quality of fit metrics should
        get added to the metadata, even if the fit was deemed a failure
        according to the value of the maxMeanDistanceArcsec config.
        """
        calexpMetadata = self.butler.get("calexp.metadata", self.calexpMinimalDataId)
        self.assertTrue(np.isfinite(calexpMetadata["SFM_ASTROM_OFFSET_MEAN"]))
        self.assertTrue(np.isfinite(calexpMetadata["SFM_ASTROM_OFFSET_STD"]))


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
