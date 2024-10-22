# This file is part of ci_hsc_gen3.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
DATA_IDS = [
    {'visit': 903334, 'detector': 16, 'physical_filter': 'HSC-R'},
    {'visit': 903334, 'detector': 22, 'physical_filter': 'HSC-R'},
    {'visit': 903334, 'detector': 23, 'physical_filter': 'HSC-R'},
    {'visit': 903334, 'detector': 100, 'physical_filter': 'HSC-R'},
    {'visit': 903336, 'detector': 17, 'physical_filter': 'HSC-R'},
    {'visit': 903336, 'detector': 24, 'physical_filter': 'HSC-R'},
    {'visit': 903338, 'detector': 18, 'physical_filter': 'HSC-R'},
    {'visit': 903338, 'detector': 25, 'physical_filter': 'HSC-R'},
    {'visit': 903342, 'detector': 4, 'physical_filter': 'HSC-R'},
    {'visit': 903342, 'detector': 10, 'physical_filter': 'HSC-R'},
    {'visit': 903342, 'detector': 100, 'physical_filter': 'HSC-R'},
    {'visit': 903344, 'detector': 0, 'physical_filter': 'HSC-R'},
    {'visit': 903344, 'detector': 5, 'physical_filter': 'HSC-R'},
    {'visit': 903344, 'detector': 11, 'physical_filter': 'HSC-R'},
    {'visit': 903346, 'detector': 1, 'physical_filter': 'HSC-R'},
    {'visit': 903346, 'detector': 6, 'physical_filter': 'HSC-R'},
    {'visit': 903346, 'detector': 12, 'physical_filter': 'HSC-R'},
    {'visit': 903986, 'detector': 16, 'physical_filter': 'HSC-I'},
    {'visit': 903986, 'detector': 22, 'physical_filter': 'HSC-I'},
    {'visit': 903986, 'detector': 23, 'physical_filter': 'HSC-I'},
    {'visit': 903986, 'detector': 100, 'physical_filter': 'HSC-I'},
    {'visit': 904014, 'detector': 1, 'physical_filter': 'HSC-I'},
    {'visit': 904014, 'detector': 6, 'physical_filter': 'HSC-I'},
    {'visit': 904014, 'detector': 12, 'physical_filter': 'HSC-I'},
    {'visit': 903990, 'detector': 18, 'physical_filter': 'HSC-I'},
    {'visit': 903990, 'detector': 25, 'physical_filter': 'HSC-I'},
    {'visit': 904010, 'detector': 4, 'physical_filter': 'HSC-I'},
    {'visit': 904010, 'detector': 10, 'physical_filter': 'HSC-I'},
    {'visit': 904010, 'detector': 100, 'physical_filter': 'HSC-I'},
    {'visit': 903988, 'detector': 16, 'physical_filter': 'HSC-I'},
    {'visit': 903988, 'detector': 17, 'physical_filter': 'HSC-I'},
    {'visit': 903988, 'detector': 23, 'physical_filter': 'HSC-I'},
    {'visit': 903988, 'detector': 24, 'physical_filter': 'HSC-I'},
]
# The following lists the dataIds that fail the astrometry check with
# the config override calibrate.astrometry.maxMeanDistanceArcsec=0.025
# set.  This list is sensitive to the astrometry algorithms and dataset
# under consideration, so may require updating if either of those change
# in the context of this repository.
ASTROMETRY_FAILURE_DATA_IDS = [
    {'visit': 903344, 'detector': 0, 'physical_filter': 'HSC-R'},
    {'visit': 903346, 'detector': 1, 'physical_filter': 'HSC-R'},
]
# The following lists the dataIds that fail the PSF Model robustness check
# with the config override makeWarp.select.maxPsfTraceRadiusDelta=0.2 set.
# This list is sensitive to (at least) the PSF algorithms and dataset under
# consideration, so may require updating if either of those change in the
# context of this repository.
PSF_MODEL_ROBUSTNESS_FAILURE_DATA_IDS = [
    {'visit': 903334, 'detector': 22, 'physical_filter': 'HSC-R'},
]
# The following data IDs fail (with NoWorkFound) in subtractImages with
# insufficient template coverage.  There are two other data IDs that succeed
# despite also having less coverage than the threshold.
INSUFFICIENT_TEMPLATE_COVERAGE_FAILURE_DATA_IDS = [
    {'visit': 903342, 'detector': 100, 'physical_filter': 'HSC-R'},
    {'visit': 904010, 'detector': 100, 'physical_filter': 'HSC-I'},
]