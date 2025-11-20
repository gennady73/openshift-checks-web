#!/usr/bin/env bash

VENV_DIR=venv

if [ -d "$VENV_DIR" ]; then
  echo "### Remove existing venv directory: $VENV_DIR ###"
  rm -rf $VENV_DIR
fi

echo "### Using Python version ###"
python3 -V

echo "### Create venv ###"
python3 -m venv $VENV_DIR

echo "### Activate venv ###"
source $VENV_DIR/bin/activate
which python

echo "### Upgrade pip in venv ###"
# Ensure you can run pip from the command line
python3 -m ensurepip --default-pip
# Ensure pip, setuptools, and wheel are up to date
#old version: python3 -m pip install --upgrade pip
python3 -m pip install --upgrade pip setuptools wheel
# make sure you have pip available
python3 -m pip --version

echo "### The venv created ###"
echo "### start use by: 'source $VENV_DIR/bin/activate'. ###"
# flaskcode
# pip install --force-reinstall --no-cache-dir --use-pep517 --no-build-isolation flaskcode