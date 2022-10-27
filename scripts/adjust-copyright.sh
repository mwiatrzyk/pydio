#!/bin/bash

set -e

if [ ! -z "$(git status --porcelain)" ]; then
    echo "Working directory not clean."
    exit 1
fi
inv adjust-copyright
git commit -a -m "chore: update copyright notice" || exit 0
