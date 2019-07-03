import os

from lsst.utils import getPackageDir

subaruConfig = os.path.join(getPackageDir("obs_subaru"), "config", "singleBandDeblend.py")
if os.path.exists(subaruConfig):
    config.singleBandDeblend.load(subaruConfig)
hscConfig = os.path.join(getPackageDir("obs_subaru"), "config", "hsc", "singleBandDeblend.py")
if os.path.exists(hscConfig):
    config.singleBandDeblend.load(hscConfig)
