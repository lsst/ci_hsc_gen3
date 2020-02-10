import os

from lsst.utils import getPackageDir

subaruConfig = os.path.join(getPackageDir("obs_subaru"), "config", "forcedPhotCcd.py")
if os.path.exists(subaruConfig):
    config.load(subaruConfig)
hscConfig = os.path.join(getPackageDir("obs_subaru"), "config", "hsc", "forcedPhotCcd.py")
if os.path.exists(hscConfig):
    config.load(hscConfig)

# Disable external calibrations: Gen3 isn't ready for these yet
config.recalibrate.doApplyExternalPhotoCalib = False
config.recalibrate.doApplyExternalSkyWcs = False
config.recalibrate.doApplySkyCorr = False
