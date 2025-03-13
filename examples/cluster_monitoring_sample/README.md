
# Overview
This is a simple [OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector) configuration for scraping NVCA endpoints, [hostmetrics](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/receiver/hostmetricsreceiver/README.md) and [DCGM metrics](https://github.com/NVIDIA/dcgm-exporter) (assumes a gpu operator is running on the cluster) and exporting them to local debug and [Lightstep](https://docs.lightstep.com/). This assumes there is a monitoring namespace configured on your cluster. Note that you'll have to ensure the DCGM target is updated to your cluster's DCGM exporter service name and namespace. Refer to the [NVCF documentation](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/cluster-management.html) for cluster registration steps.

# Prerequisites
* Have NVCA running on your cluster
* Have the GPU operator running on your cluster with dcgm exporter

# Steps
1. Create monitoring namespace if not created.
`kubectl create namespace monitoring`

2. Create NVCA pod and service monitors if not already created.
```
kubectl apply -f nvca-operator-pod-monitor.yaml
kubectl apply -f nvca-service-monitor.yaml
```

3. Update the OpenTelemetry Collector configuration with the correct target for the DCGM exporter.

    3a. Identify the DCGM exporter service name and namespace:
    `kubectl get svc -A | grep nvidia-dcgm`

    Example response:
    `gpu-operator    nvidia-dcgm-exporter                                 ClusterIP   10.96.128.176   <none>        9400/TCP                       22h`

    Then modify the configuration to include the correct namespace, service name, and port.

    3b. Update the collector configuration with the appropriate exporters to your monitoring provider. In this example, Lightstep is used (see the lightstep credentials section for where to set the endpoint and access token).

4. Create all the k8s resources and verify the result.
`kubectl apply -f otel-collector-k8s.yaml`

Verify by tailing the logs on the collector that no errors are occurring.
`kubectl logs -f -n monitoring -l app=otel-collector` 

Remember each time when you are modifying the collector configuration, you are re-applying the k8s manifest file and restarting the collector pod. Set the debug level to "detailed" for more logging.