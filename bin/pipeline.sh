#!/usr/bin/env sh

set -e

usage() {
    cat <<USAGE
Usage: $0 [-j N] [-m] [-l level] repo

Options:
    -h          Print usage information.
    -j N        Run pipetask with N processes, default is 1.
    -m          Run mock pipeline.
    -l level    Logging level, default is INFO.
USAGE
}

jobs=1
mock=
loglevel=INFO

while getopts hj:ml: opt
do
    case $opt in
        h) usage; exit;;
        j) jobs=$OPTARG;;
        m) mock="--mock";;
        l) loglevel=$OPTARG;;
        \?) usage 1>&2; exit 1;;
    esac
done
shift $((OPTIND - 1))
if [ $# -eq 0 ]; then
    usage 1>&2
    exit 1
fi
repo=$1

COLLECTION=HSC/runs/ci_hsc
INPUTCOLL=HSC/defaults
FAKES_COLLECTION=HSC/runs/ci_hsc_fakes
FARO_COLLECTION=HSC/runs/ci_hsc_faro
RESOURCE_USAGE_COLLECTION=HSC/runs/ci_hsc_resource_usage
HIPS_COLLECTION=HSC/runs/ci_hsc_hips

export DYLD_LIBRARY_PATH="$LSST_LIBRARY_PATH"
# exercise saving of the generated quantum graph to a file and reading it back
QGRAPH_FILE=$(mktemp).qgraph
trap 'rm -f $QGRAPH_FILE' EXIT

FAKES_QGRAPH_FILE=$(mktemp)_fakes.qgraph
trap 'rm -f $FAKES_QGRAPH_FILE' EXIT

FARO_QGRAPH_FILE=$(mktemp)_faro.qgraph
trap 'rm -f $FARO_QGRAPH_FILE' EXIT

RESOURCE_USAGE_QGRAPH_FILE=$(mktemp)_resource_usage.qgraph
trap 'rm -f $RESOURCE_USAGE_QGRAPH_FILE' EXIT

HIPS_QGRAPH_FILE=$(mktemp)_hips.qgraph
trap 'rm -f $HIPS_QGRAPH_FILE' EXIT

pipetask --long-log --log-level="$loglevel" qgraph \
    -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69" \
    -b "$repo"/butler.yaml \
    --input "$INPUTCOLL" --output "$COLLECTION" \
    -p "$DRP_PIPE_DIR/pipelines/HSC/DRP-ci_hsc.yaml" \
    -c makeWarp:select.maxPsfTraceRadiusDelta=0.2 \
    --save-qgraph "$QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    --input "$INPUTCOLL" --output "$COLLECTION" \
    --register-dataset-types $mock \
    --qgraph "$QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" qgraph \
    -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69" \
    -b "$repo"/butler.yaml \
    --input "$COLLECTION" --output "$FAKES_COLLECTION" \
    -p "$DRP_PIPE_DIR/pipelines/HSC/DRP-ci_hsc+fakes.yaml" \
    --save-qgraph "$FAKES_QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    --input "$COLLECTION" --output "$FAKES_COLLECTION" \
    --register-dataset-types $mock \
    --qgraph "$FAKES_QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" qgraph \
    -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69" \
    -b "$repo"/butler.yaml \
    --input "$COLLECTION" --output "$FARO_COLLECTION" \
    -p "$FARO_DIR"/pipelines/metrics_pipeline.yaml \
    --save-qgraph "$FARO_QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    --input "$COLLECTION" --output "$FARO_COLLECTION" \
    --register-dataset-types $mock \
    --qgraph "$FARO_QGRAPH_FILE"

build-gather-resource-usage-qg "$repo" "$RESOURCE_USAGE_QGRAPH_FILE" "$COLLECTION"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    --output "$RESOURCE_USAGE_COLLECTION" \
    --register-dataset-types $mock \
    -g "$RESOURCE_USAGE_QGRAPH_FILE"

# The output from this is unused, but this will exercise that the code runs.
build-high-resolution-hips-qg segment -b "$repo" -p "$CI_HSC_GEN3_DIR/resources/highres_hips.yaml" -i "$COLLECTION"

build-high-resolution-hips-qg build -b "$repo" -p "$CI_HSC_GEN3_DIR/resources/highres_hips.yaml" -i "$COLLECTION" --pixels 18 -q "$HIPS_QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    --output "$HIPS_COLLECTION" \
    --register-dataset-types $mock \
    -g "$HIPS_QGRAPH_FILE"
