#!/usr/bin/env python

import argparse
import logging

from collections import namedtuple

import lsst.log
from lsst.log import Log

from lsst.daf.butler import Butler, DatasetType


ExternalProducts = namedtuple("ExternalProducts",
                              ["datatype", "dimensions", "storageClass", "dataId", "path"])


def ingestExternalData(butler, products):
    """Adds a list of products to a registry and ingests them into a
    Datastore.

    butler: `lsst.daf.butler.Butler`
        Butler which to operate on
    products: `ExternalProducts`
        Named tuple describing datasets to add to the registry and datastore
    """

    for entry in products:
        dsType = DatasetType(entry.datatype, butler.registry.dimensions.extract(entry.dimensions),
                             entry.storageClass)
        butler.registry.registerDatasetType(dsType)
        dsRef = butler.registry.addDataset(dsType, entry.dataId, butler.run)
        butler.datastore.ingest(entry.path, dsRef)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Writes Curtaled Calibrations")
    parser.add_argument("root", help="Path to butler to use")
    parser.add_argument("-v", "--verbose", action="store_const", dest="logLevel",
                        default=Log.INFO, const=Log.DEBUG,
                        help="Set the log level to DEBUG.")

    args = parser.parse_args()
    log = Log.getLogger("lsst.daf.butler")
    log.setLevel(args.logLevel)

    # Forward python logging to lsst logger
    lgr = logging.getLogger("lsst.daf.butler")
    lgr.setLevel(logging.INFO if args.logLevel == Log.INFO else logging.DEBUG)
    lgr.addHandler(lsst.log.LogHandler())

    butler = Butler(args.root, run="shared/ci_hsc")

    products = [ExternalProducts("brightObjectMask",
                                 ("tract", "patch", "skymap", "abstract_filter"),
                                 "ObjectMaskCatalog",
                                 {"tract": 0,
                                  "patch": 69,
                                  "skymap": "ci_hsc",
                                  "abstract_filter": "i"},
                                 "brightObjectMasks/0/BrightObjectMask-0-5,4-HSC-I.reg"),
                ExternalProducts("brightObjectMask",
                                 ("tract", "patch", "skymap", "abstract_filter"),
                                 "ObjectMaskCatalog",
                                 {"tract": 0,
                                  "patch": 69,
                                  "skymap": "ci_hsc",
                                  "abstract_filter": "r"},
                                 "brightObjectMasks/0/BrightObjectMask-0-5,4-HSC-I.reg"),
                ExternalProducts("ref_cat",
                                 ("skypix",),
                                 "SimpleCatalog",
                                 {"skypix": 189584},
                                 "ps1_pv3_3pi_20170110/189584.fits"),
                ExternalProducts("ref_cat",
                                 ("skypix",),
                                 "SimpleCatalog",
                                 {"skypix": 189648},
                                 "ps1_pv3_3pi_20170110/189648.fits"),
                ]
    ingestExternalData(butler, products)
