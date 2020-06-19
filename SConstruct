import os
from SCons.Script import SConscript, Environment, GetOption, Default, Dir, Touch
from lsst.sconsUtils.utils import libraryLoaderEnvironment
SConscript(os.path.join(".", "bin.src", "SConscript"))

env = Environment(ENV=os.environ)
env["ENV"]["OMP_NUM_THREADS"] = "1"  # Disable threading
profileNum = -1


def getProfiling(script):
    """Return python command-line argument string for profiling
    If activated (via the "--enable-profile" command-line argument),
    we write the profile to a filename starting with the provided
    base name and including a sequence number and the script name,
    so its contents can be quickly identified.
    Note that this is python function-level profiling, which won't
    descend into C++ elements of the codebase.
    A basic profile can be printed using python:
        >>> from pstats import Stats
        >>> stats = Stats("profile-123-script.pstats")
        >>> stats.sort_stats("cumulative").print_stats(30)
    """
    base = GetOption("enable_profile")
    if not base:
        return ""
    global profileNum
    profileNum += 1
    if script.endswith(".py"):
        script = script[:script.rfind(".")]
    return f" -m cProfile -o {base}-{profileNum:03}-{script}.pstats"


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
    cmds = [libraryLoaderEnvironment(), "python", getProfiling(script),
            os.path.join(env.ProductDir(package), directory, script)]
    cmds.extend(args)
    return " ".join(cmds)


TESTDATA_ROOT = env.ProductDir("testdata_ci_hsc")
PKG_ROOT = env.ProductDir("ci_hsc_gen3")
AddOption("--repo-root", dest="root", default=os.path.join(PKG_ROOT, "DATA"),
          help="Path to root of the data repository.")
REPO_ROOT = GetOption("root")

AddOption("--enable-profile", nargs="?", const="profile", dest="enable_profile",
          help=("Profile base filename; output will be <basename>-<sequence#>-<script>.pstats; "
                "(Note: this option is for profiling the scripts, while --profile is for scons)"))
AddOption("--butler-config", dest="butler_conf", default="",
          help="Path to an external Butler config used to create a data repository.")
AddOption("--config-override", action="store_true", dest="conf_override",
          help="Override the default config root with the given repo-root.")

conf = GetOption("butler_conf")
butler_conf = f"--seed-config {conf}" if conf != "" else ""
conf_override = "--override" if GetOption("conf_override") else ""

# Create butler
butler = env.Command([os.path.join(REPO_ROOT, "butler.yaml"),
                      os.path.join(REPO_ROOT, "gen3.sqlite3")], "bin",
                     [getExecutableCmd("daf_butler", "butler", "create", REPO_ROOT,
                                       butler_conf, conf_override)])
env.Alias("butler", butler)

# Register instrument and write curated calibrations
instrument = env.Command(os.path.join(REPO_ROOT, "instrument"), butler,
                         [getExecutableCmd("daf_butler", "butler", "register-instrument", REPO_ROOT,
                                           "lsst.obs.subaru.HyperSuprimeCam")])
env.Alias("instrument", instrument)

# Write curated calibrations
curatedCalibrations = env.Command(os.path.join(REPO_ROOT, "calib"), instrument,
                                  [getExecutableCmd("daf_butler", "butler", "write-curated-calibrations",
                                                    REPO_ROOT,
                                                    "-i", "HSC")])
env.Alias("curatedCalibrations", curatedCalibrations)

skymap = env.Command(os.path.join(REPO_ROOT, "skymaps"), curatedCalibrations,
                     [getExecutableCmd("pipe_tasks", "makeGen3Skymap.py", REPO_ROOT,
                                       "-C", os.path.join(PKG_ROOT, "configs", "skymap.py"), "skymaps")])
env.Alias("skymap", skymap)

raws = env.Command(os.path.join(REPO_ROOT, "raw"), [curatedCalibrations, skymap],
                   [getExecutableCmd("daf_butler", "butler", "ingest-raws", REPO_ROOT,
                                     "-d", os.path.join(TESTDATA_ROOT, "raw"))])

visits = env.Command(os.path.join(REPO_ROOT, "visits"), [raws],
                     [getExecutableCmd("daf_butler", "butler", "define-visits", REPO_ROOT,
                                       "-i", "HSC",
                                       "--collections", "HSC/raw/all"),
                     Touch(os.path.join(REPO_ROOT, "visits"))])

external = env.Command([Dir(os.path.join(REPO_ROOT, "masks")),
                        Dir(os.path.join(REPO_ROOT, "ref_cats")),
                        Dir(os.path.join(REPO_ROOT, "shared"))],
                       [curatedCalibrations, skymap, raws, visits],
                       [getExecutableCmd("daf_butler", "butler", "import", REPO_ROOT,
                                         env.ProductDir("testdata_ci_hsc"),
                                         "--export-file", os.path.join(PKG_ROOT, "resources",
                                                                       "external.yaml"),
                                         "--output-run", "shared/ci_hsc")])
env.Alias("external", external)

# Use name ingest to run everything up to but not including running the
# pipeline
ingest = env.Alias("ingest", raws + visits)

num_process = GetOption('num_jobs')

pipeline = env.Command(os.path.join(REPO_ROOT, "shared", "ci_hsc_output"), ingest,
                       ["bin/pipeline.sh {} {}".format(num_process, REPO_ROOT)])

tests = []
executable = os.path.join(PKG_ROOT, "bin", "sip_safe_python.sh")
for file in os.listdir(os.path.join(PKG_ROOT, "tests")):
    test = os.path.join(PKG_ROOT, "tests", file)
    if test.endswith(".py"):
        tests.append(env.Command(os.path.join(PKG_ROOT, "tests", ".tests", file), pipeline,
                     f"{executable} {test}"))

env.Alias("tests", tests)
everything = [butler, instrument, curatedCalibrations, skymap, external, raws, pipeline, tests]

# Add a no-op install target to keep Jenkins happy.
env.Alias("install", "SConstruct")

env.Alias("all", everything)
Default(everything)

env.Clean(everything, [y for x in everything for y in x])
