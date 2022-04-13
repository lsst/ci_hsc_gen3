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
import yaml
from lsst.ci.hsc.gen3.tests import MockCheckMixin
from lsst.daf.butler import Butler
from lsst.utils import getPackageDir


class TestSchemaMatch(lsst.utils.tests.TestCase, MockCheckMixin):
    """Check the schema of the parquet outputs match the DDL in sdm_schemas"""

    def setUp(self):
        self.butler = Butler(os.path.join(getPackageDir("ci_hsc_gen3"), "DATA"),
                             writeable=False, collections=["HSC/runs/ci_hsc"])
        schemaFile = os.path.join(getPackageDir("sdm_schemas"), 'yml', 'hsc.yaml')
        with open(schemaFile, "r") as f:
            self.schema = yaml.safe_load(f)['tables']

    def _validateSchema(self, dataset, dataId, tableName):
        """Check the schema of the parquet dataset match that in the DDL.
        Only the column names are checked currently.
        """
        # skip the test in mock execution
        self.skip_mock(dataset)

        sdmSchema = [table for table in self.schema if table['name'] == tableName]
        self.assertEqual(len(sdmSchema), 1)
        expectedColumnNames = set(column['name'] for column in sdmSchema[0]['columns'])

        df = self.butler.get(dataset, dataId)
        df.reset_index(inplace=True)
        outputColumnNames = set(df.columns.to_list())
        self.assertEqual(outputColumnNames, expectedColumnNames)

    def testObjectSchemaMatch(self):
        """Check objectTable_tract"""
        dataId = {"instrument": "HSC", "tract": 0}
        self._validateSchema("objectTable_tract", dataId, "Object")

    def testSourceSchemaMatch(self):
        """Check one sourceTable_visit"""
        dataId = {"instrument": "HSC", "detector": 100, "visit": 903334, "band": "r"}
        self._validateSchema("sourceTable_visit", dataId, "Source")


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
