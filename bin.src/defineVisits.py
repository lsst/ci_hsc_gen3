#!/usr/bin/env python

import argparse
import logging

import lsst.log
from lsst.log import Log

from lsst.daf.butler import Butler
from lsst.obs.base import DefineVisitsTask, DefineVisitsConfig

from lsst.obs.subaru import HyperSuprimeCam

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Defines visits from exposures in the butler registry")
    parser.add_argument("root", help="Path to butler to use")
    parser.add_argument("-v", "--verbose", action="store_const", dest="logLevel",
                        default=Log.INFO, const=Log.DEBUG,
                        help="Set the log level to DEBUG.")
    parser.add_argument("-C", "--config-file", help="Path to config file overload for DefineVisitsTask",
                        default=None, dest="configFile")

    args = parser.parse_args()
    log = Log.getLogger("lsst.daf.butler")
    log.setLevel(args.logLevel)

    # Forward python logging to lsst logger
    lgr = logging.getLogger("lsst.daf.butler")
    lgr.setLevel(logging.INFO if args.logLevel == Log.INFO else logging.DEBUG)
    lgr.addHandler(lsst.log.LogHandler())

    butler = Butler(args.root, collections=["raw/hsc"], writeable=True)

    config = DefineVisitsConfig()
    instrument = HyperSuprimeCam()
    instrument.applyConfigOverrides(DefineVisitsTask._DefaultName, config)
    if args.configFile is not None:
        config.load(args.configFile)
    task = DefineVisitsTask(config=config, butler=butler)
    task.run(butler.registry.queryDimensions(["exposure"]))
