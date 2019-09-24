#!/usr/bin/env python

import argparse
import logging

import lsst.log
from lsst.log import Log

from lsst.daf.butler import Butler
from lsst.obs.subaru.gen3.hsc import HyperSuprimeCam

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add the HSC instrument and its curated calibrations to the data repository."
    )
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

    butler = Butler(args.root, run="calib/hsc")
    instrument = HyperSuprimeCam()
    instrument.register(butler.registry)
    instrument.writeCuratedCalibrations(butler)
