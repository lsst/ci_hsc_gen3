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

from felis import Schema

from lsst.daf.butler import Butler
from lsst.utils import getPackageDir
import lsst.utils.tests


class TestSchemaMatch(lsst.utils.tests.TestCase):
    """Check the schema of the parquet outputs match the DDL in sdm_schemas"""

    def setUp(self):
        self.butler = Butler(
            os.path.join(getPackageDir("ci_hsc_gen3"), "DATA"),
            writeable=False,
            collections=["HSC/runs/ci_hsc"],
        )
        schemaFile = os.path.join(getPackageDir("sdm_schemas"), "yml", "hsc.yaml")
        self.schema = Schema.from_uri(schemaFile, context={"id_generation": True})

    def _validateSchema(self, dataset, dataId, tableName):
        """Check the schema of the parquet dataset match that in the DDL.
        Only the column names are checked currently.
        """
        tables = [table for table in self.schema.tables if table.name == tableName]
        self.assertEqual(len(tables), 1)
        expectedColumnNames = set(column.name for column in tables[0].columns)

        df = self.butler.get(dataset, dataId, storageClass="ArrowAstropy")
        outputColumnNames = set(df.colnames)
        self.assertEqual(outputColumnNames, expectedColumnNames)

    def testObjectSchemaMatch(self):
        """Check objectTable_tract"""
        dataId = {"instrument": "HSC", "tract": 0}
        self._validateSchema("objectTable_tract", dataId, "Object")

    def testSourceSchemaMatch(self):
        """Check one sourceTable_visit"""
        dataId = {"instrument": "HSC", "detector": 100, "visit": 903334, "band": "r"}
        self._validateSchema("sourceTable_visit", dataId, "Source")


def setup_module(module):
    lsst.utils.tests.init()


if __name__ == "__main__":
    lsst.utils.tests.init()
    unittest.main()
