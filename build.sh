#!/bin/bash

cd $(dirname $0)

pip3 show dungeonfaster
FOUND=$?
# Uninstall:
if [ $FOUND ]; then
    pip3 uninstall dungeonfaster -y
fi

# Build
poetry build

# Install:
pip install dist/dungeonfaster-*.whl
