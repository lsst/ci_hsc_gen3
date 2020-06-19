#!/usr/bin/env sh

set -e

COLLECTION=shared/ci_hsc_output
INPUTCOLL=HSC/calib,HSC/raw,HSC/masks,ref_cats,skymaps,shared/ci_hsc

export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH

# exercise saving of the generated quantum graph to a file and reading it back
QGRAPH_FILE=$(mktemp)
trap 'rm -f $QGRAPH_FILE' EXIT

pipetask qgraph -d "patch = 69" -b "$2"/butler.yaml \
    -i "$INPUTCOLL" -o "$COLLECTION" \
    -p "$CI_HSC_GEN3_DIR"/pipelines/CiHsc.yaml \
    --save-qgraph "$QGRAPH_FILE"

pipetask run -j "$1" -b "$2"/butler.yaml \
    -i "$INPUTCOLL" -o "$COLLECTION" \
    --register-dataset-types \
    --qgraph "$QGRAPH_FILE"
