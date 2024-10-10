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
from lsst.ci.hsc.gen3.tests import MockCheckMixin
from lsst.daf.butler import Butler, DataCoordinate
from lsst.geom import Box2I, Point2I
from lsst.utils import getPackageDir


class TestFilterLabelFixups(lsst.utils.tests.TestCase, MockCheckMixin):
    """Tests for the logic in
    lsst.obs.base.formatters.fitsExposure.FitsExposureFormatter._fixFilterLabels
    that uses the data ID passed to a formatter to fix and/or check the
    FilterLabel read from an Exposure FITS file, allowing us to load images
    with new, standardized filters even if they were written prior to filter
    standardization (and without enough information to reconstruct the
    standardized filter name).

    This test lives here instead of obs_base because it relies on having
    Exposure FITS files written both before and after standardization in a Gen3
    butler, something trivial to obtain here: the flats are old (from
    testdata_ci_hsc) - while pvis are new (written by Gen3 pipelines).
    And this package already has the dependency on a concrete obs package
    (obs_subaru in this case) necessary to set up a full butler repository,
    something that obs_base can by definition never have.
    """

    def setUp(self):
        self.butler = Butler(os.path.join(getPackageDir("ci_hsc_gen3"), "DATA"), writeable=False,
                             collections=["HSC/calib/2013-06-17", "HSC/runs/ci_hsc"])
        # We need to provide a physical_filter value to fully identify a flat,
        # but this still leaves the band as an implied value that this data ID
        # doesn't know.
        self.flatMinimalDataId = DataCoordinate.standardize(
            instrument="HSC", detector=0, physical_filter="HSC-R",
            universe=self.butler.dimensions,
        )
        # For a pvi, the minimal data ID just has exposure and detector,
        # so both band and physical_filter are implied and not known here.
        self.pviMinimalDataId = DataCoordinate.standardize(
            instrument="HSC", detector=100, visit=903334,
            universe=self.butler.dimensions,
        )
        # Parameters with bbox to test that logic still works on subimage gets.
        self.parameters = {"bbox": Box2I(Point2I(0, 0), Point2I(8, 7))}

    def testReadingOldFileWithIncompleteDataId(self):
        """If we try to read an old flat with an incomplete data ID, we should
        get a warning.  It is unspecified what the FilterLabel will have in
        this case, so we don't check that.
        """
        with self.assertWarns(Warning):
            self.butler.get("flat", self.flatMinimalDataId)
        with self.assertWarns(Warning):
            self.butler.get("flat", self.flatMinimalDataId, parameters=self.parameters)
        with self.assertWarns(Warning):
            self.butler.get("flat.filter", self.flatMinimalDataId)

    def testFixingReadingOldFile(self):
        """If we read an old flat with a complete data ID, we fix the
        FilterLabel.
        """
        flatFullDataId = self.butler.registry.expandDataId(self.flatMinimalDataId)
        flat = self.butler.get("flat", flatFullDataId)
        self.assertEqual(flat.getFilter().bandLabel, flatFullDataId["band"])
        self.assertEqual(flat.getFilter().physicalLabel, flatFullDataId["physical_filter"])
        flatFilterLabel = self.butler.get("flat.filter", flatFullDataId)
        self.assertEqual(flatFilterLabel.bandLabel, flatFullDataId["band"])
        self.assertEqual(flatFilterLabel.physicalLabel, flatFullDataId["physical_filter"])
        flatSub = self.butler.get("flat", flatFullDataId, parameters=self.parameters)
        self.assertEqual(flat.getFilter(), flatSub.getFilter())

    def testReadingNewFileWithIncompleteDataId(self):
        """If we try to read a new initial_pvi with an incomplete data ID, the
        reader should recognize that it can't check the filters and just trust
        the file.
        """
        self.skip_mock()
        pvi = self.butler.get("initial_pvi", self.pviMinimalDataId)
        pviFilterLabel = self.butler.get("initial_pvi.filter", self.pviMinimalDataId)
        self.assertTrue(pvi.getFilter().hasPhysicalLabel())
        self.assertTrue(pvi.getFilter().hasBandLabel())
        self.assertEqual(pvi.getFilter(), pviFilterLabel)
        pviSub = self.butler.get("initial_pvi", self.pviMinimalDataId, parameters=self.parameters)
        self.assertEqual(pvi.getFilter(), pviSub.getFilter())

    def testReadingNewFileWithFullDataId(self):
        """If we try to read a new pvi with a full data ID, the reader
        should check the filters in the file for consistency with the data ID
        (and in this case, find them consistent).
        """
        self.skip_mock()
        pviFullDataId = self.butler.registry.expandDataId(self.pviMinimalDataId)
        pvi = self.butler.get("initial_pvi", pviFullDataId)
        self.assertEqual(pvi.getFilter().bandLabel, pviFullDataId["band"])
        self.assertEqual(pvi.getFilter().physicalLabel, pviFullDataId["physical_filter"])
        pviFilterLabel = self.butler.get("initial_pvi.filter", pviFullDataId)
        self.assertEqual(pviFilterLabel.bandLabel, pviFullDataId["band"])
        self.assertEqual(pviFilterLabel.physicalLabel, pviFullDataId["physical_filter"])
        pviSub = self.butler.get("initial_pvi", pviFullDataId, parameters=self.parameters)
        self.assertEqual(pvi.getFilter(), pviSub.getFilter())

    def testReadingBadNewFileWithFullDataId(self):
        """If we try to read a new pvi with a full data ID, the reader
        should check the filters in the file for consistency with the data ID
        (and in this case, find them inconsistent, which should result in
        warnings and returning what's in the data ID).
        """
        self.skip_mock()
        pviBadDataId = DataCoordinate.standardize(
            self.pviMinimalDataId,
            band="g",
            physical_filter="HSC-G",
            day_obs=20240101,
        )
        self.assertTrue(pviBadDataId.hasFull())

        # Some tests are only relevant when reading full pvis.
        # By definition a disassembled exposure will have a correct
        # filterlabel written out.
        # In this situation the test becomes moot since the filterLabel
        # formatter will not force a correct filter label into an
        # incorrect filter label based on DataId.
        _, components = self.butler.getURIs("initial_pvi", pviBadDataId)
        if components:
            raise unittest.SkipTest("Test not relevant because composite has been disassembled")

        with self.assertWarns(Warning):
            pvi = self.butler.get("initial_pvi", pviBadDataId)
        with self.assertWarns(Warning):
            pviFilterLabel = self.butler.get("initial_pvi.filter", pviBadDataId)
        self.assertEqual(pvi.getFilter(), pviFilterLabel)
        self.assertEqual(pvi.getFilter().bandLabel, pviBadDataId["band"])
        self.assertEqual(pvi.getFilter().physicalLabel, pviBadDataId["physical_filter"])
        self.assertEqual(pviFilterLabel.bandLabel, pviBadDataId["band"])
        self.assertEqual(pviFilterLabel.physicalLabel, pviBadDataId["physical_filter"])
        with self.assertWarns(Warning):
            pviSub = self.butler.get("initial_pvi", pviBadDataId, parameters=self.parameters)
        self.assertEqual(pvi.getFilter(), pviSub.getFilter())


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
