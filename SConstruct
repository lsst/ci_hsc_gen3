import os
from SCons.Script import SConscript
from lsst.sconsUtils.utils import libraryLoaderEnvironment
from lsst.utils import getPackageDir
SConscript(os.path.join(".", "bin.src", "SConscript"))

env = Environment(ENV=os.environ)
env["ENV"]["OMP_NUM_THREADS"] = "1"  # Disable threading

location = getPackageDir("ci_hsc_gen3")


def getExecutable(package, script, directory=None):
    """
    Given the name of a package and a script or other executable which lies
    within the given subdirectory (defaults to "bin"), return an appropriate
    string which can be used to set up an appropriate environment and execute
    the command.
    This includes:
    * Specifying an explict list of paths to be searched by the dynamic linker;
    * Specifying a Python executable to be run (we assume the one on the
      default ${PATH} is appropriate);
    * Specifying the complete path to the script.
    """
    if directory is None:
        directory = "bin"
    return "{} python {}".format(libraryLoaderEnvironment(),
                                 os.path.join(getPackageDir(package), directory, script))


# Create butler
butler = env.Command(["butler.yaml", "gen3.sqlite3"], "bin",
                     ["{} .".format(getExecutable("daf_butler", "makeButlerRepo.py"))])

# Use name butler to just run making a butler
env.Alias("butler", butler)

# Run the linker
links = env.Command(["CALIB", "raw", "brightObjectMasks", "ps1_pv3_3pi_20170110"], butler, ["bin/linker.sh"])

register = env.Command("register", links,
                       ["{} butler.yaml --nocalibs".format(getExecutable("ci_hsc_gen3", "gen3.py"))])

sql = env.Command("sql", register, ["bin/dbImport.sh"])

hsc = env.Command("shared/ci_hsc", sql, ["{} butler.yaml".format(getExecutable("ci_hsc_gen3", "gen3.py"))])

skymap = env.Command("skymap", hsc,
                     ["{} -C configs/skymap.py butler.yaml shared/ci_hsc"
                      .format(getExecutable("pipe_tasks", "makeGen3Skymap.py"))])

externalData = env.Command("external", skymap,
                           ["{} butler.yaml".format(getExecutable("ci_hsc_gen3", "ingestExternalData.py"))])

raws = env.Command("raws", externalData,
                   ["{0} butler.yaml {1}/raw -C {1}/configs/ingestRaws.py"
                    .format(getExecutable("ci_hsc_gen3", "ingestRaws.py"), location)])

# Use name ingest to run everything up to but not including running the
# pipeline
env.Alias("ingest", raws)

num_process = GetOption('num_jobs')

pipeline = env.Command("shared/ci_hsc_output", raws, ["bin/pipeline.sh {}".format(num_process)])

everything = [butler, links, register, sql, hsc, skymap, externalData, raws, pipeline]

env.Alias("all", everything)
Default(everything)

env.Clean(everything, [y for x in everything for y in x])
