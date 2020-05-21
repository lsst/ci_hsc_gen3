#!/usr/bin/env sh
COLLECTION=shared/ci_hsc_output

export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH

pipetask qgraph -q ci_hsc.pickle -d "patch = 69" -b "$2"/butler.yaml \
-i calib/hsc,raw/hsc,masks/hsc,ref_cats,skymaps,shared/ci_hsc -o "$COLLECTION" \
-p "$CI_HSC_GEN3_DIR"/pipelines/CiHsc.yaml

pipetask run --qgraph ci_hsc.pickle -j "$1" -b "$2"/butler.yaml \
-i calib/hsc,raw/hsc,masks/hsc,ref_cats,skymaps,shared/ci_hsc -o "$COLLECTION" \
--register-dataset-types
