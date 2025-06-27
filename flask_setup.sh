#!/usr/bin/env bash

SRV_PORT=5500
export FLASK_RUN_PORT=$SRV_PORT
export INSTALL_CONFIG_PATH=/home/gunger/Documents/openshift-checks/kubeconfig/install-config.yaml
export PYTHONUNBUFFERED=1
export SERVER_NAME=localhost:$SRV_PORT

echo "### FLACK CONFIGURATION ###"

echo "FLASK_RUN_PORT      : $FLASK_RUN_PORT"
echo "INSTALL_CONFIG_PATH : $INSTALL_CONFIG_PATH"
echo "PYTHONUNBUFFERED    : $PYTHONUNBUFFERED"
echo "SERVER_NAME         : $SERVER_NAME"

echo "### ################### ###"

