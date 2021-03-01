#!/usr/bin/env sh

set -e

COLLECTION=HSC/runs/ci_hsc
INPUTCOLL=HSC/defaults

export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH

# exercise saving of the generated quantum graph to a file and reading it back
QGRAPH_FILE=$(mktemp).qgraph
trap 'rm -f $QGRAPH_FILE' EXIT

pipetask qgraph -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69" -b "$2"/butler.yaml \
    --input "$INPUTCOLL" --output "$COLLECTION" \
    -p "$OBS_SUBARU_DIR"/pipelines/DRP.yaml \
    -c makeWarp:connections.photoCalibName=jointcal \
    -c makeWarp:useGlobalExternalPhotoCalib=False \
    --save-qgraph "$QGRAPH_FILE"

pipetask run -j "$1" -b "$2"/butler.yaml \
    --input "$INPUTCOLL" --output "$COLLECTION" \
    --register-dataset-types \
    --qgraph "$QGRAPH_FILE"
