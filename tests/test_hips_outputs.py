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

import unittest
import os
import re

from lsst.ci.hsc.gen3.tests import MockCheckMixin
from lsst.daf.butler import Butler
from lsst.utils import getPackageDir
from lsst.resources import ResourcePath


class TestHipsOutputs(unittest.TestCase, MockCheckMixin):
    """Check that HIPS outputs are as expected."""
    def setUp(self):
        self.butler = Butler(os.path.join(getPackageDir("ci_hsc_gen3"), "DATA"),
                             instrument="HSC", skymap="discrete/ci_hsc",
                             writeable=False, collections=["HSC/runs/ci_hsc_hips"])
        self.skip_mock()
        self._bands = ['r', 'i']
        self.hips_uri_base = ResourcePath(os.path.join(getPackageDir("ci_hsc_gen3"), "DATA", "hips"))

    def test_hips_exist(self):
        """Test that the HIPS images exist and are readable."""
        for band in self._bands:
            datasets = set(self.butler.registry.queryDatasets("deepCoadd_hpx", band=band))

            # There are 64 HIPS images for each band.
            self.assertEqual(len(datasets), 64)

            for dataset in datasets:
                self.assertTrue(self.butler.datastore.exists(dataset), msg="File exists for deepCoadd_hpx")

            exp = self.butler.get(list(datasets)[0])

            self.assertEqual(exp.wcs.getFitsMetadata()["CTYPE1"], "RA---HPX")
            self.assertEqual(exp.wcs.getFitsMetadata()["CTYPE2"], "DEC--HPX")

    def test_hips_trees_exist(self):
        """Test that the HiPS tree exists and has correct files."""
        self._check_hips_tree(self.hips_uri_base.join("band_r", forceDirectory=True))
        self._check_hips_tree(self.hips_uri_base.join("band_i", forceDirectory=True))
        self._check_hips_tree(self.hips_uri_base.join("color_gri", forceDirectory=True), check_fits=False)

    def _check_hips_tree(self, hips_uri, check_fits=True):
        """Check a HiPS tree for files.

        Parameters
        ----------
        hips_uri : `lsst.resources.ResourcePath`
            URI of base of HiPS tree.
        check_fits : `bool`, optional
            Check if FITS images exist.
        """
        self.assertTrue(hips_uri.join("properties").exists())
        self.assertTrue(hips_uri.join("Moc.fits").exists())
        allsky = hips_uri.join("Norder3", forceDirectory=True).join("Allsky.png")
        self.assertTrue(allsky.exists())

        for order in range(3, 12):
            order_uri = hips_uri.join(f"Norder{order}", forceDirectory=True)
            png_uris = list(
                ResourcePath.findFileResources(
                    candidates=[order_uri],
                    file_filter=re.compile(r'Npix.*\.png'),
                )
            )
            self.assertGreater(len(png_uris), 0)

            if check_fits:
                fits_uris = list(
                    ResourcePath.findFileResources(
                        candidates=[order_uri],
                        file_filter=re.compile(r'Npix.*\.fits'),
                    )
                )
                self.assertEqual(len(fits_uris), len(png_uris))


if __name__ == "__main__":
    unittest.main()
