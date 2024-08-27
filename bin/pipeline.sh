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
INJECTION_COLLECTION=HSC/runs/ci_hsc_injection
INJECTION_INPUTCOLL=injection_catalogs
FARO_COLLECTION=HSC/runs/ci_hsc_faro
RESOURCE_USAGE_COLLECTION=HSC/runs/ci_hsc_resource_usage
HIPS_COLLECTION=HSC/runs/ci_hsc_hips

export DYLD_LIBRARY_PATH="$LSST_LIBRARY_PATH"
# exercise saving of the generated quantum graph to a file and reading it back
QGRAPH_FILE=$(mktemp).qgraph
INJECTION_QGRAPH_FILE=$(mktemp)_injection.qgraph
POST_INJECTION_QGRAPH_FILE=$(mktemp)_post_injection.qgraph
FARO_QGRAPH_FILE=$(mktemp)_faro.qgraph
RESOURCE_USAGE_QGRAPH_FILE=$(mktemp)_resource_usage.qgraph
HIPS_QGRAPH_FILE=$(mktemp)_hips.qgraph

trap 'rm -f $QGRAPH_FILE $INJECTION_QGRAPH_FILE $FARO_QGRAPH_FILE $RESOURCE_USAGE_QGRAPH_FILE \
$HIPS_QGRAPH_FILE' EXIT

pipetask --long-log --log-level="$loglevel" qgraph \
    -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69" \
    -b "$repo"/butler.yaml \
    --input "$INPUTCOLL" --output "$COLLECTION" \
    -p "$DRP_PIPE_DIR/pipelines/HSC/DRP-ci_hsc.yaml" \
    -c calibrate:astrometry.maxMeanDistanceArcsec=0.025 \
    -c calibrate:requireAstrometry=False \
    -c calibrate:requirePhotoCal=False \
    -c makeDirectWarp:select.maxPsfTraceRadiusDelta=0.2 \
    --save-qgraph "$QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    --input "$INPUTCOLL" --output "$COLLECTION" \
    --register-dataset-types $mock \
    --qgraph "$QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" qgraph \
    -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69" \
    -b "$repo"/butler.yaml \
    --input "$COLLECTION","$INJECTION_INPUTCOLL" --output "$INJECTION_COLLECTION" \
    -p "$repo"/DRP-ci_hsc+injection.yaml \
    --save-qgraph "$INJECTION_QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    --input "$COLLECTION","$INJECTION_INPUTCOLL" --output "$INJECTION_COLLECTION" \
    --register-dataset-types $mock \
    --qgraph "$INJECTION_QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" qgraph \
    -d "skymap='discrete/ci_hsc' AND tract=0 and patch=69" \
    -b "$repo"/butler.yaml \
    --output "$INJECTION_COLLECTION" \
    -p "$DRP_PIPE_DIR/pipelines/HSC/DRP-ci_hsc-post-injected.yaml" \
    --save-qgraph "$POST_INJECTION_QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    --output "$INJECTION_COLLECTION" \
    --register-dataset-types $mock \
    --qgraph "$POST_INJECTION_QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" qgraph \
    -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69 AND band in ('r', 'i')" \
    -b "$repo"/butler.yaml \
    --input "$COLLECTION" --output "$FARO_COLLECTION" \
    -p "$FARO_DIR"/pipelines/metrics_pipeline.yaml \
    --save-qgraph "$FARO_QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    --input "$COLLECTION" --output "$FARO_COLLECTION" \
    --register-dataset-types $mock \
    --qgraph "$FARO_QGRAPH_FILE"

build-gather-resource-usage-qg --output "$RESOURCE_USAGE_COLLECTION" "$repo" "$RESOURCE_USAGE_QGRAPH_FILE" "$COLLECTION"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    --output "$RESOURCE_USAGE_COLLECTION" \
    --register-dataset-types $mock \
    -g "$RESOURCE_USAGE_QGRAPH_FILE"

# The output from this is unused, but this will exercise that the code runs.
build-high-resolution-hips-qg segment -b "$repo" -p "$CI_HSC_GEN3_DIR/resources/highres_hips.yaml" -i "$COLLECTION"

build-high-resolution-hips-qg build \
    -b "$repo" -p "$CI_HSC_GEN3_DIR/resources/highres_hips.yaml" \
    -i "$COLLECTION" --output "$HIPS_COLLECTION" \
    --pixels 18 -q "$HIPS_QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    --output "$HIPS_COLLECTION" \
    --register-dataset-types $mock \
    -g "$HIPS_QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    -i "$HIPS_COLLECTION" \
    --output "$HIPS_COLLECTION" \
    -p "$CI_HSC_GEN3_DIR/resources/gen_hips.yaml" \
    -c "generateHips:hips_base_uri=$repo/hips" \
    -c "generateColorHips:hips_base_uri=$repo/hips" \
    --register-dataset-types $mock
