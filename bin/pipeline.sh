#!/usr/bin/env sh

set -e

COLLECTION=shared/ci_hsc_output
INPUTCOLL=HSC/calib,HSC/raw/all,HSC/masks,refcats,skymaps

export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH

# exercise saving of the generated quantum graph to a file and reading it back
QGRAPH_FILE=$(mktemp).pickle
trap 'rm -f $QGRAPH_FILE' EXIT

pipetask qgraph -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69" -b "$2"/butler.yaml \
    --input "$INPUTCOLL" --output "$COLLECTION" \
    -p "$OBS_SUBARU_DIR"/pipelines/DRP.yaml \
    --save-qgraph "$QGRAPH_FILE"

pipetask run -j "$1" -b "$2"/butler.yaml \
    --input "$INPUTCOLL" --output "$COLLECTION" \
    --register-dataset-types \
    --qgraph "$QGRAPH_FILE"
