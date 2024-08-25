#!/bin/bash

CURRENT_DIR=$(pwd)

sed "s|<HOST_PATH>|$CURRENT_DIR|g" tensorboard-template.yaml > tensorboard-deployment.yaml

kubectl apply -f tensorboard-deployment.yaml
