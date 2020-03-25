#!/usr/bin/env python

import argparse
import logging
import os

import lsst.log
from lsst.log import Log

from lsst.daf.butler import Butler
from lsst.obs.base import RawIngestTask, RawIngestConfig

from lsst.obs.subaru import HyperSuprimeCam

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingests raw frames into the butler registry")
    parser.add_argument("root", help="Path to butler to use")
    parser.add_argument("dir", help="Path to directory containing raws to ingest")
    parser.add_argument("-v", "--verbose", action="store_const", dest="logLevel",
                        default=Log.INFO, const=Log.DEBUG,
                        help="Set the log level to DEBUG.")
    parser.add_argument("-C", "--config-file", help="Path to config file overload for RawIngestTask",
                        default=None, dest="configFile")

    args = parser.parse_args()
    log = Log.getLogger("lsst.daf.butler")
    log.setLevel(args.logLevel)

    # Forward python logging to lsst logger
    lgr = logging.getLogger("lsst.daf.butler")
    lgr.setLevel(logging.INFO if args.logLevel == Log.INFO else logging.DEBUG)
    lgr.addHandler(lsst.log.LogHandler())

    butler = Butler(args.root, run="raw/hsc")

    config = RawIngestConfig()
    instrument = HyperSuprimeCam()
    instrument.applyConfigOverrides("ingest-gen3", config)
    config.transfer = "symlink"
    if args.configFile is not None:
        config.load(args.configFile)
    ingester = RawIngestTask(config=config, butler=butler)

    files = [os.path.join(args.dir, f) for f in os.listdir(args.dir)
             if f.endswith("fits") or f.endswith("FITS")]
    ingester.run(files)
