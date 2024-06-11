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

# Windows: https://kivy.org/doc/stable/guide/packaging-windows.html
# Android: https://kivy.org/doc/stable/guide/packaging-android.html
# iOS: https://kivy.org/doc/stable/guide/packaging-ios.html