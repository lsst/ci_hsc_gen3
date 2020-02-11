#!/usr/bin/env bash

export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH

"$(which python)" $1
