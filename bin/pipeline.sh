#!/usr/bin/env sh
COLLECTION=shared/ci_hsc_output

export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH

pipetask run -d "patch = 69" -j "$1" -b "$CI_HSC_GEN3_DIR"/DATA/butler.yaml \
-i calib/hsc,raw/hsc,masks/hsc,ref_cats,skymaps,shared/ci_hsc -o "$COLLECTION" \
--register-dataset-types \
-p "$CI_HSC_GEN3_DIR"/pipelines/CiHsc.yaml
