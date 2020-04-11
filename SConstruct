import os
from SCons.Script import SConscript, Environment, GetOption, Default, Dir, Touch
from lsst.sconsUtils.utils import libraryLoaderEnvironment
SConscript(os.path.join(".", "bin.src", "SConscript"))

env = Environment(ENV=os.environ)
env["ENV"]["OMP_NUM_THREADS"] = "1"  # Disable threading


def getExecutableCmd(package, script, *args, directory=None):
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
    cmds = [libraryLoaderEnvironment(), "python", os.path.join(env.ProductDir(package), directory, script)]
    cmds.extend(args)
    return " ".join(cmds)


TESTDATA_ROOT = env.ProductDir("testdata_ci_hsc")
PKG_ROOT = env.ProductDir("ci_hsc_gen3")
REPO_ROOT = os.path.join(PKG_ROOT, "DATA")

# Create butler
butler = env.Command([os.path.join(REPO_ROOT, "butler.yaml"),
                      os.path.join(REPO_ROOT, "gen3.sqlite3")], "bin",
                     [getExecutableCmd("daf_butler", "makeButlerRepo.py", REPO_ROOT)])
env.Alias("butler", butler)

# Register instrument and write curated calibrations
instrument = env.Command(os.path.join(REPO_ROOT, "calib"), butler,
                         [getExecutableCmd("ci_hsc_gen3", "registerInstrument.py", REPO_ROOT)])
env.Alias("instrument", instrument)

skymap = env.Command(os.path.join(REPO_ROOT, "skymaps"), instrument,
                     [getExecutableCmd("pipe_tasks", "makeGen3Skymap.py", REPO_ROOT,
                                       "-C", os.path.join(PKG_ROOT, "configs", "skymap.py"), "skymaps")])
env.Alias("skymap", skymap)

raws = env.Command(os.path.join(REPO_ROOT, "raw"), [instrument, skymap],
                   [getExecutableCmd("ci_hsc_gen3", "ingestRaws.py", REPO_ROOT,
                                     os.path.join(TESTDATA_ROOT, "raw"))])

visits = env.Command(os.path.join(REPO_ROOT, "visits"), [raws],
                     [getExecutableCmd("ci_hsc_gen3", "defineVisits.py", REPO_ROOT),
                      Touch(os.path.join(REPO_ROOT, "visits"))])

external = env.Command([Dir(os.path.join(REPO_ROOT, "masks")),
                        Dir(os.path.join(REPO_ROOT, "ref_cats")),
                        Dir(os.path.join(REPO_ROOT, "shared"))],
                       [instrument, skymap, raws, visits],
                       [getExecutableCmd("ci_hsc_gen3", "ingestExternalData.py", REPO_ROOT,
                                         os.path.join(PKG_ROOT, "resources", "external.yaml"))])
env.Alias("external", external)

# Use name ingest to run everything up to but not including running the
# pipeline
ingest = env.Alias("ingest", raws + visits)

num_process = GetOption('num_jobs')

pipeline = env.Command(os.path.join(REPO_ROOT, "shared", "ci_hsc_output"), ingest,
                       ["bin/pipeline.sh {}".format(num_process)])

tests = []
executable = os.path.join(PKG_ROOT, "bin", "sip_safe_python.sh")
for file in os.listdir(os.path.join(PKG_ROOT, "tests")):
    test = os.path.join(PKG_ROOT, "tests", file)
    if test.endswith(".py"):
        tests.append(env.Command(os.path.join(PKG_ROOT, "tests", ".tests", file), pipeline,
                     f"{executable} {test}"))

env.Alias("tests", tests)
everything = [butler, instrument, skymap, external, raws, pipeline, tests]

# Add a no-op install target to keep Jenkins happy.
env.Alias("install", "SConstruct")

env.Alias("all", everything)
Default(everything)

env.Clean(everything, [y for x in everything for y in x])
