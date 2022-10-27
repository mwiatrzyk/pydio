#!/bin/bash

set -e

if [ ! -z "$(git status --porcelain)" ]; then
    echo "Working directory not clean."
    exit 1
fi
inv adjust-formatting
git commit -a -m "style: run code formatting tools" || exit 0
