#!/bin/bash

# Work around SIP on MacOSX
build() {
    export DYLD_LIBRARY_PATH=$LSST_LIBRARY_PATH
    python "$(command -v scons)" -j"$NJOBS" prefix="$PREFIX" version="$VERSION" cc="$CC"
}

install() {
    clean_old_install
    install_ups
}
