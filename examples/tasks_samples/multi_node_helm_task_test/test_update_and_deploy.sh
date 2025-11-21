#!/usr/bin/env bash

TARGETED_DEPLOYMENT_SPECIFICATION=GB200:AWS.GPU.GB200_4x.x2:nvcf-dgxc-k8s-aws-use1-prd8
CONFIGURATION_FILE=gb200-override.yaml
ORG=qdrlnbkss8u1
CHART_NAME=multi-node-task-test
CHART_VERSION=0.1.0

# ngc registry chart create $ORG/$CHART_NAME --short-desc "Multi-node task test" 

ngc registry chart remove $ORG/$CHART_NAME:$CHART_VERSION -y
rm $CHART_NAME-$CHART_VERSION.tgz

set -e

helm package multi-node-task-test/

ngc registry chart push $ORG/$CHART_NAME:$CHART_VERSION

ngc cf task create \
  --org $ORG \
  --name $CHART_NAME \
  --gpu-specification $TARGETED_DEPLOYMENT_SPECIFICATION \
  --configuration-file $CONFIGURATION_FILE \
  --max-runtime-duration 1H \
  --max-queued-duration 1H \
  --termination-grace-period-duration 1H \
  --result-handling-strategy NONE \
  --helm-chart $ORG/$CHART_NAME:$CHART_VERSION