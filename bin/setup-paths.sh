#!/bin/bash
# $Id$
# (C) Timothy Corbett-Clark, 2004

# Source this file when running midge commands before installation.

pushd $(dirname $0) >/dev/null

export PYTHONPATH=${PYTHONPATH}:$(pwd)/..
export PATH=${PATH}:$(pwd)

popd >/dev/null