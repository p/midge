#!/bin/bash

set -e

while true; do
    ./sync
    midged &
    echo "sleeping for a while..."
    sleep 1h
    killall python
done
