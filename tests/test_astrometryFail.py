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


class TestAstrometryFails(lsst.utils.tests.TestCase):
    """Tests the outputs of the forced astrometry failures.
    """
    def setUp(self):
        self.butler = Butler(os.path.join(getPackageDir("ci_hsc_gen3"), "DATA"), writeable=False,
                             collections=["HSC/calib/2013-06-17", "HSC/runs/ci_hsc"])
        # The dataId here represents one of the astrometry fit failures
        # imposed by setting astrometry.maxMeanDistanceArcsec: 0.025 in
        # the pipeline.
        self.detector = 0
        self.visit = 903344
        self.pviMinimalDataId = DataCoordinate.standardize(
            instrument="HSC", detector=self.detector, visit=self.visit,
            universe=self.butler.dimensions,
        )

    def tearDown(self):
        del self.butler
        del self.detector
        del self.visit
        del self.calexpMinimalDataId

    def testWcsAndPhotoCalibIsNoneForFailedAstrom(self):
        """Test the WCS and photoCalib objects attached to failed WCS exposure.

        An exposure with a failed astrometric fit should have WCS and
        photoCalib set to None.
        """
        pvi = self.butler.get("initial_pvi", self.pviMinimalDataId)
        self.assertTrue(pvi.getWcs() is None)
        self.assertTrue(pvi.getPhotoCalib() is None)

        pviWcs = self.butler.get("initial_pvi.wcs", self.pviMinimalDataId)
        self.assertTrue(pviWcs is None)

        pviPhotoCalib = self.butler.get("initial_pvi.photoCalib", self.pviMinimalDataId)
        self.assertTrue(pviPhotoCalib is None)

    def testSrcCoordsAreNanForFailedAstrom(self):
        """Test coord values in all source catalogs.

        The coord values in the catalogs, i.e. the results from SFM,
        should all be `numpy.nan` for a failed astrometric fit.  However,
        when applying external calibrations, the coordinates can indeed get
        successfully "reevaluated" if the associated calibration does indeed
        exist (this is to allow for the external calibrations to potentially
        "recover" from a failed SFM astrometric fit).  In this case, those
        files do indeed exist in the ci_hsc_gen3 repo, so the ``source`` and
        ``sourceTable`` catalogs will have valid coord entries.
        """
        sourceCat = self.butler.get("initial_stars_footprints_detector", self.pviMinimalDataId)
        self.assertTrue(np.all(np.isnan(sourceCat["coord_ra"])))
        self.assertTrue(np.all(np.isnan(sourceCat["coord_dec"])))
        for catStr in ["source", "sourceTable"]:
            sourceCat = self.butler.get(catStr, self.pviMinimalDataId)
            self.assertFalse(np.all(np.isnan(sourceCat["coord_ra"])))
            self.assertFalse(np.all(np.isnan(sourceCat["coord_dec"])))

    def testCentroidsAreNotNanForFailedAstrom(self):
        """Test that at least some catalog centroids have finite values.

        The coord values in the catalogs, i.e. the results from SFM,
        should all be `numpy.nan` for a failed astrometric fit.  However,
        the centroid x and y values should have (at least some) valid entries.
        This is also true for the ``source`` and ``sourceTable`` catalogs,
        so check those as well.
        """
        for catStr in ["initial_stars_footprints_detector", "source"]:
            sourceCat = self.butler.get(catStr, self.pviMinimalDataId)
            self.assertFalse(np.all(np.isnan(sourceCat["slot_Centroid_x"])))
            self.assertFalse(np.all(np.isnan(sourceCat["slot_Centroid_y"])))
        for catStr in ["sourceTable"]:
            sourceCat = self.butler.get(catStr, self.pviMinimalDataId)
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
        visitTable = self.butler.get("visitTable", self.pviMinimalDataId)
        self.assertTrue(np.all(np.isfinite(visitTable["ra"])))

        visitSummary = self.butler.get("visitSummary", self.pviMinimalDataId)
        self.assertTrue(np.isfinite(visitSummary["id" == self.detector]["astromOffsetMean"]))
        self.assertTrue(np.isfinite(visitSummary["id" == self.detector]["astromOffsetStd"]))
        self.assertTrue(np.all(np.isnan(visitSummary["id" == 1]["raCorners"])))
        self.assertTrue(np.all(np.isnan(visitSummary["id" == 1]["decCorners"])))

    def testMetadataForFailedAstrom(self):
        """Test that the metadata for a failed astrometic fit is set properly.

        If the fitter converged, the astrometry quality of fit metrics should
        get added to the metadata, even if the fit was deemed a failure
        according to the value of the maxMeanDistanceArcsec config.
        """
        pviMetadata = self.butler.get("initial_pvi.metadata", self.pviMinimalDataId)
        self.assertTrue(np.isfinite(pviMetadata["SFM_ASTROM_OFFSET_MEAN"]))
        self.assertTrue(np.isfinite(pviMetadata["SFM_ASTROM_OFFSET_STD"]))


class MemoryTester(lsst.utils.tests.MemoryTestCase):
    pass


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
