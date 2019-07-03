import os

from lsst.utils import getPackageDir

subaruConfig = os.path.join(getPackageDir("obs_subaru"), "config", "compareWarpAssembleCoadd.py")
if os.path.exists(subaruConfig):
    config.load(subaruConfig)
hscConfig = os.path.join(getPackageDir("obs_subaru"), "config", "hsc", "compareWarpAssembleCoadd.py")
if os.path.exists(hscConfig):
    config.load(hscConfig)
