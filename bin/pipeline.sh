#!/usr/bin/env sh

set -e

usage() {
    cat <<USAGE
Usage: $0 [-j N] [-l level] repo

Options:
    -h          Print usage information.
    -j N        Run pipetask with N processes, default is 1.
    -l level    Logging level, default is INFO.
USAGE
}

jobs=1
loglevel=INFO

while getopts hj:l: opt
do
    case $opt in
        h) usage; exit;;
        j) jobs=$OPTARG;;
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
RESOURCE_USAGE_COLLECTION=HSC/runs/ci_hsc_resource_usage
HIPS_COLLECTION=HSC/runs/ci_hsc_hips

export DYLD_LIBRARY_PATH="$LSST_LIBRARY_PATH"
# exercise saving of the generated quantum graph to a file and reading it back
QGRAPH_FILE=ci_hsc.qgraph
INJECTION_QGRAPH_FILE=ci_hsc_injection.qgraph
POST_INJECTION_QGRAPH_FILE=ci_hsc_post_injection.qgraph
RESOURCE_USAGE_QGRAPH_FILE=ci_hsc_resource_usage.qgraph

pipetask --long-log --log-level="$loglevel" qgraph \
    -d "skymap='discrete/ci_hsc' AND tract=0 AND patch=69" \
    -b "$repo"/butler.yaml \
    --input "$INPUTCOLL" --output "$COLLECTION" \
    -p "$DRP_PIPE_DIR/pipelines/HSC/DRP-ci_hsc.yaml" \
    -c calibrateImage:astrometry.maxMeanDistanceArcsec=0.0196 \
    -c makeDirectWarp:select.maxPsfTraceRadiusDelta=0.2 \
    --save-qgraph "$QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    --input "$INPUTCOLL" --output "$COLLECTION" \
    --no-raise-on-partial-outputs \
    --register-dataset-types \
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
    --register-dataset-types \
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
    --register-dataset-types \
    --qgraph "$POST_INJECTION_QGRAPH_FILE"


build-gather-resource-usage-qg --output "$RESOURCE_USAGE_COLLECTION" "$repo" "$RESOURCE_USAGE_QGRAPH_FILE" "$COLLECTION"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    --output "$RESOURCE_USAGE_COLLECTION" \
    --register-dataset-types \
    -g "$RESOURCE_USAGE_QGRAPH_FILE"

pipetask --long-log --log-level="$loglevel" run \
    -j "$jobs" -b "$repo"/butler.yaml \
    -i "$COLLECTION" \
    --output "$HIPS_COLLECTION" \
    -p "$CI_HSC_GEN3_DIR/resources/hips.yaml" \
    -c "generateHips:hips_base_uri=$repo/hips" \
    -c "generateColorHips:hips_base_uri=$repo/hips" \
    --register-dataset-types
