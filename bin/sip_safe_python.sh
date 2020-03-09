#!/usr/bin/env bash

export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH

python "$1"
