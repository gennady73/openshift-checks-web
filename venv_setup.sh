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
python3 -m pip install --upgrade pip
python3 -m pip --version

echo "### The venv created ###"
echo "### start use by: 'source $VENV_DIR/bin/activate'. ###"