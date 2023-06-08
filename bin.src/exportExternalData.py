#!/usr/bin/env python

import os.path
import argparse
import logging

from lsst.utils import getPackageDir
from lsst.daf.butler import Butler, FileDataset

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Re-export the YAML file used to ingest calibs, refcats, and masks."
    )
    parser.add_argument(
        "root",
        help=("Path to Gen3 butler to export from (usually "
              "$CI_HSC_GEN2_DIR/DATAgen3, after gen2to3 has been run there).")
    )
    parser.add_argument(
        "filename",
        help="Path to YAML file describing external files (usually resources/external.yaml)."
    )
    parser.add_argument("-v", "--verbose", action="store_const", dest="logLevel",
                        default=logging.INFO, const=logging.DEBUG,
                        help="Set the log level to DEBUG.")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    lgr = logging.getLogger("lsst.daf.butler")
    lgr.setLevel(args.logLevel)

    butler = Butler(args.root, collections=["HSC/calib"])

    def rewrite(dataset: FileDataset) -> FileDataset:
        # Join the datastore root to the exported path.  This should yield
        # absolute paths that start with $CI_HSC_GEN2_DIR.
        dataset.path = os.path.join(butler.datastore.root.ospath, dataset.path)
        # Remove symlinks in the path; this should result in absolute paths
        # that start with $TESTDATA_CI_HSC_DIR, because ci_hsc_gen2 always
        # symlinks these datasets from there.
        dataset.path = os.path.realpath(dataset.path)
        # Recompute the path relative to $TESTDATA_CI_HSC_DIR, so we can deal
        # with that moving around after the export file is created.
        dataset.path = os.path.relpath(dataset.path, getPackageDir("testdata_ci_hsc"))
        return dataset

    with butler.export(filename=args.filename) as export:
        for datasetTypeName in ("brightObjectMask", "ps1_pv3_3pi_20170110", "jointcal_photoCalib",
                                "jointcal_wcs"):
            export.saveDatasets(butler.registry.queryDatasets(datasetTypeName, collections=...),
                                elements=(), rewrite=rewrite)
        for datasetTypeName in ("bias", "dark", "flat", "sky"):
            export.saveDatasets(butler.registry.queryDatasets(datasetTypeName, collections=...),
                                elements=(), rewrite=rewrite)
        for collection in butler.registry.queryCollections("HSC/defaults", includeChains=True,
                                                           flattenChains=True):
            export.saveCollection(collection)
