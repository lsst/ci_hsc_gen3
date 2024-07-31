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

"""Module to support mock option in unit tests.
"""

__all__ = ["MockCheckMixin"]

from typing import Optional
import unittest

from lsst.daf.butler import Butler


class MockCheckMixin:
    """Mix-in class to support checking for mock execution."""

    butler: Optional[Butler] = None
    """Sub-class can define ``butler`` attribute to avoid passing Butler
    instance to each method."""

    def check_mock(
        self, dataset_type: str = "initial_pvi", butler: Optional[Butler] = None
    ) -> bool:
        """Check whether Butler contents correspond to a mock execution.

        Parameters
        ----------
        dataset_type : `str`, optional
            Name of the dataset that is expected to exist in butler.
        butler : `Butler`, optional
            Data butler instance, if `None` then ``self.butler`` must not be
            `None`.

        Returns
        -------
        mock : `bool`
            True if there is a mock dataset type corresponding to a given type.
        """
        if butler is None:
            butler = self.butler
        if butler is None:
            raise ValueError("No butler instance provided")
        try:
            # check for mock dataset type
            butler.get_dataset_type(f"_mock_{dataset_type}")
            return True
        except KeyError:
            return False

    def skip_mock(
        self, dataset_type: str = "initial_pvi", butler: Optional[Butler] = None
    ) -> None:
        """Skip a unit test during mock execution.

        Parameters
        ----------
        dataset_type : `str`, optional
            Name of the dataset that is expected to exist in butler.
        butler : `Butler`, optional
            Data butler instance, if `None` then ``self.butler`` must not be
            `None`.

        Raises
        -------
        unittest.SkipTest
            Raised if butler was populated by a mock execution.
        """
        if self.check_mock(dataset_type, butler):
            raise unittest.SkipTest("Skipping due to mock execution")
