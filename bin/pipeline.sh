#!/usr/bin/env sh

set -e

COLLECTION=HSC/runs/ci_hsc
INPUTCOLL=HSC/defaults
FAKES_COLLECTION=HSC/runs/ci_hsc_fakes
FARO_COLLECTION=HSC/runs/ci_hsc_faro

export DYLD_LIBRARY_PATH="$LSST_LIBRARY_PATH"
# exercise saving of the generated quantum graph to a file and reading it back
QGRAPH_FILE=$(mktemp).qgraph
trap 'rm -f $QGRAPH_FILE' EXIT

FAKES_QGRAPH_FILE=$(mktemp)_fakes.qgraph
trap 'rm -f $FAKES_QGRAPH_FILE' EXIT

FARO_QGRAPH_FILE=$(mktemp)_faro.qgraph
trap 'rm -f $FARO_QGRAPH_FILE' EXIT

pipetask --long-log qgraph \
    -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69" \
    -b "$2"/butler.yaml \
    --input "$INPUTCOLL" --output "$COLLECTION" \
    -p "$CI_HSC_GEN3_DIR"/pipelines/DRP.yaml \
    --save-qgraph "$QGRAPH_FILE"

pipetask --long-log run -j "$1" -b "$2"/butler.yaml \
    --input "$INPUTCOLL" --output "$COLLECTION" \
    --register-dataset-types \
    --qgraph "$QGRAPH_FILE"

pipetask --long-log qgraph \
    -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69" \
    -b "$2"/butler.yaml \
    --input "$COLLECTION" --output "$FAKES_COLLECTION" \
    -p "$CI_HSC_GEN3_DIR"/pipelines/DRPFakes.yaml \
    --save-qgraph "$FAKES_QGRAPH_FILE"

pipetask --long-log run -j "$1" -b "$2"/butler.yaml \
    --input "$COLLECTION" --output "$FAKES_COLLECTION" \
    --register-dataset-types \
    --qgraph "$FAKES_QGRAPH_FILE"

pipetask --long-log qgraph \
    -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69" \
    -b "$2"/butler.yaml \
    --input "$COLLECTION" --output "$FARO_COLLECTION" \
    -p "$FARO_DIR"/pipelines/metrics_pipeline.yaml \
    --save-qgraph "$FARO_QGRAPH_FILE"

pipetask --long-log run -j "$1" -b "$2"/butler.yaml \
    --input "$COLLECTION" --output "$FARO_COLLECTION" \
    --register-dataset-types \
    --qgraph "$FARO_QGRAPH_FILE"

