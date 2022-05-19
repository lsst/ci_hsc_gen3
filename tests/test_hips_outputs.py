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

from lsst.ci.hsc.gen3.tests import MockCheckMixin
from lsst.daf.butler import Butler
from lsst.utils import getPackageDir


class TestHipsOutputs(unittest.TestCase, MockCheckMixin):
    """Check that HIPS outputs are as expected."""
    def setUp(self):
        self.butler = Butler(os.path.join(getPackageDir("ci_hsc_gen3"), "DATA"),
                             instrument="HSC", skymap="discrete/ci_hsc",
                             writeable=False, collections=["HSC/runs/ci_hsc_hips"])
        self.skip_mock()
        self._bands = ['r', 'i']

    def test_hips_exist(self):
        """Test that the HIPS images exist and are readable."""
        for band in self._bands:
            datasets = set(self.butler.registry.queryDatasets("deepCoadd_hpx", band=band))

            # There are 64 HIPS images for each band.
            self.assertEqual(len(datasets), 64)

            for dataset in datasets:
                self.assertTrue(self.butler.datastore.exists(dataset), msg="File exists for deepCoadd_hpx")

            exp = self.butler.getDirect(list(datasets)[0])

            self.assertEqual(exp.wcs.getFitsMetadata()["CTYPE1"], "RA---HPX")
            self.assertEqual(exp.wcs.getFitsMetadata()["CTYPE2"], "DEC--HPX")


if __name__ == "__main__":
    unittest.main()
