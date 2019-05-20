import os

from lsst.utils import getPackageDir

subaruConfig = os.path.join(getPackageDir("obs_subaru"), "config", "mergeCoaddDetections.py")
if os.path.exists(subaruConfig):
    config.load(subaruConfig)
hscConfig = os.path.join(getPackageDir("obs_subaru"), "config", "hsc", "mergeCoaddDetections.py")
if os.path.exists(hscConfig):
    config.load(hscConfig)

# This is specific to gen3, where the priority list needs to be in terms of abstract filters
config.priorityList = ["i", "r"]
