#!/usr/bin/env python

import os
import subprocess

from lsst.ci.builder import CommandRunner, BaseCommand, BuildState, CommandError
from lsst.ci.builder.commands import (CreateButler, RegisterInstrument, WriteCuratedCalibrations,
                                      RegisterSkyMap, IngestRaws, DefineVisits, ButlerImport,
                                      TestRunner)

TESTDATA_DIR = os.environ['TESTDATA_CI_HSC_DIR']
INSTRUMENT_NAME = "HSC"
INPUTCOL = "HSC/defaults"
COLLECTION = "HSC/runs/ci_hsc"
QGRPAH_FILE = "qgraph_file.qgraph"


ciHscRunner = CommandRunner(os.environ["CI_HSC_GEN3_DIR"])


ciHscRunner.register("butler", 0)(CreateButler)


@ciHscRunner.register("instrument", 1)
class HscRegisterInstrument(RegisterInstrument):
    instrumentName = "lsst.obs.subaru.HyperSuprimeCam"


@ciHscRunner.register("calibrations", 2)
class HscWriteCuratedCalibrations(WriteCuratedCalibrations):
    instrumentName = INSTRUMENT_NAME


ciHscRunner.register("skymap", 3)(RegisterSkyMap)


@ciHscRunner.register("ingest", 4)
class HscIngestRaws(IngestRaws):
    rawLocation = os.path.join(TESTDATA_DIR, "raw")


@ciHscRunner.register("defineVisits", 5)
class HscDefineVisits(DefineVisits):
    instrumentName = INSTRUMENT_NAME
    collectionsName = "HSC/raw/all"


@ciHscRunner.register("importExternalBase", 6)
class HscBaseButlerImport(ButlerImport):
    dataLocation = TESTDATA_DIR

    @property
    def importFileLocation(self) -> str:
        return os.path.join(self.runner.pkgRoot, "resources", "external.yaml")


@ciHscRunner.register("importExternalJointcal", 7)
class HscJointcalButlerImport(ButlerImport):
    dataLocation = TESTDATA_DIR

    @property
    def importFileLocation(self) -> str:
        return os.path.join(self.runner.pkgRoot, "resources", "external_jointcal.yaml")


@ciHscRunner.register("qgraph", 8)
class QgraphCommand(BaseCommand):
    def run(self, currentState: BuildState):
        args = ("qgraph",
                "-d", '''skymap='discrete/ci_hsc' AND tract=0 AND patch=69''',
                "-b", self.runner.RunDir,
                "--input", INPUTCOL,
                "--output", COLLECTION,
                "-p", "$CI_HSC_GEN3_DIR/pipelines/DRP.yaml",
                "--save-qgraph", os.path.join(self.runner.RunDir, QGRPAH_FILE))
        pipetask = self.runner.getExecutableCmd("CTRL_MPEXEC_DIR", "pipetask", args)
        result = subprocess.run(pipetask)
        if result.returncode != 0:
            raise CommandError("Issue Running QuntumGraph")


@ciHscRunner.register("processing", 9)
class ProcessingCommand(BaseCommand):
    def run(self, currentState: BuildState):
        args = ("run",
                "-j", str(self.arguments.num_cores),
                "-b", self.runner.RunDir,
                "--input", INPUTCOL,
                "--output", COLLECTION,
                "--register-dataset-types",
                "--qgraph", os.path.join(self.runner.RunDir, QGRPAH_FILE))
        pipetask = self.runner.getExecutableCmd("CTRL_MPEXEC_DIR", "pipetask", args)
        result = subprocess.run(pipetask)
        if result.returncode != 0:
            raise CommandError("Issue Running Pipeline")


ciHscRunner.register("tests", 10)(TestRunner)

ciHscRunner.run()
