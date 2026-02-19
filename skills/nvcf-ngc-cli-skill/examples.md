# NGC Cloud Functions Examples

Comprehensive examples for functions, tasks, clusters, and GPU operations.

## Function Workflows

### Workflow 1: Create and Deploy a Container Function

#### Step 1: Create the function

Assumes `NGC_API_KEY` is set in your shell; do not paste secrets directly into the command.

```bash
ngc cf fn create \
  --name my-inference-service \
  --inference-url /v1/predict \
  --container-image myorg/my-model:v1.0 \
  --description "Production inference service" \
  --secret API_KEY:$NGC_API_KEY \
  --container-environment-variable MODEL_PATH:/models/latest
```

Output:
```
Function Information
  Name: my-inference-service
  Version: 6698aa4d-1ea3-4f95-b6cb-4bf879fe538a
  ID: a7346e6f-4755-47cf-9163-6212e8db0900
  Status: INACTIVE
```

#### Step 2: Deploy the function

```bash
ngc cf fn deploy create a7346e6f-4755-47cf-9163-6212e8db0900:6698aa4d-1ea3-4f95-b6cb-4bf879fe538a \
  --targeted-dep-spec L40:gl40_1.br20_2xlarge:1:3:10
```

#### Step 3: Verify deployment

```bash
ngc cf fn deploy info a7346e6f-4755-47cf-9163-6212e8db0900:6698aa4d-1ea3-4f95-b6cb-4bf879fe538a
```

---

### Workflow 2: Deploy Docker Hub Image (vLLM Example)

Deploy an LLM using a Docker Hub container image.

Note: Docker Hub images require the full path with `docker.io/` prefix.

```bash
ngc cf fn create \
  --name gpt-neox-20b-vllm \
  --inference-url /v1/completions \
  --container-image docker.io/vllm/vllm-openai:latest \
  --description "GPT-NeoX 20B served via vLLM" \
  --health-uri /health \
  --health-port 8000 \
  --health-protocol HTTP \
  --health-timeout PT60S \
  --health-expected-status-code 200 \
  --container-args "--model EleutherAI/gpt-neox-20b --port 8000 --tensor-parallel-size 1"
```

Deploy:
```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec H100:OCI.GPU.H100_1x:1:1:1
```

---

### Workflow 2b: Targeted Deployments (Clusters, Regions, Attributes)

Use `--targeted-dep-spec` to control where your function runs. The format is:

```
<gpu>:<instance_type>:<min>:<max>[:<concurrency>][:<clusters>][:<regions>][:<attributes>][:<preferredOrder>]
```

All fields after `max` are optional and positional. Use commas for multiple values within a field. Skip middle fields with empty colons (`::`).

**Warning:** The CLI `--help` shows wrapper syntax like `clusters(c1,c2)` and `regions(r1,r2)`, but the CLI does not parse these wrappers. Always use plain values in the positional format shown here.
**Note:** The CLI requires clusters for non-GFN instance types (OCI/DGX). If you see `FAILED_MISSING_CLUSTERS`, add a cluster in the 6th field.

#### Discover available clusters and check quota first

```bash
# List clusters and instance types for a GPU
ngc cf gpu info A100

# Check quota limits (look for "dedicated-clusters" requiring explicit targeting)
ngc cf gpu quota --format_type json
```

#### Deploy to a specific cluster

```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec A100:OCI.GPU.A100_1x:1:1:1:nvcf-dgxc-k8s-oci-ord-dev1
```

#### Deploy to multiple clusters

```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec L40:gl40_1.br20_2xlarge:1:3:10:cluster-west,cluster-east
```

#### Deploy with cluster and region

```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec A100:OCI.GPU.A100_1x:1:2:5:my-cluster:us-east-1
```

#### Deploy with region only (skip clusters when allowed)

Use `::` to skip the cluster field:

```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec H100:OCI.GPU.H100_1x:1:2:5::us-east-1
```

#### Deploy with multiple regions

```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec H100:OCI.GPU.H100_1x:1:4:10::us-east-1,eu-west-1
```

#### Multi-spec deployment with priority ordering

Use `preferredOrder` (9th field) and repeat `--targeted-dep-spec` to define failover:

```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec A100:OCI.GPU.A100_1x:1:1:1:cluster-primary:::1 \
  --targeted-dep-spec A100:OCI.GPU.A100_2x:0:1:1:cluster-fallback:::2
```

---

### Workflow 2c: Helm Chart Function with Values

#### Step 1: Create the function from a Helm chart

```bash
ngc cf fn create \
  --name helm-inference \
  --inference-url /v1/predict \
  --helm-chart myorg/llm-helm:1.2.3 \
  --helm-chart-service inference
```

#### Step 2: Deploy with Helm values

`--configuration-file` and `--set` apply only to Helm chart functions.

```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec L40:gl40_1.br20_2xlarge:1:1:5 \
  --configuration-file values.yaml \
  --set image.tag=1.2.3
```

---

### Workflow 3: Deploy AWS ECR Image

#### Step 1: Add ECR registry credentials

```bash
ngc cf registry-credential create \
  --hostname 123456789012.dkr.ecr.us-east-1.amazonaws.com \
  --name my-ecr-credential \
  --key $AWS_SECRET_ACCESS_KEY \
  --aws-access-key $AWS_ACCESS_KEY_ID \
  --type CONTAINER
```

#### Step 2: Create function with ECR image

```bash
ngc cf fn create \
  --name my-ecr-function \
  --inference-url /v2/models/my-model/infer \
  --container-image 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-inference:latest \
  --description "Inference service from ECR"
```

#### Step 3: Deploy the function

```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec L40:gl40_1.br20_2xlarge:1:2:10
```

---

### Workflow 4: Authorize External Accounts

Allow another organization to invoke your function:

```bash
# Get your function's authorization info
ngc cf fn auth info 7835a350-921e-4fd3-8004-554b84c1367b

# Add authorized party by their NCA ID
ngc cf fn auth add 7835a350-921e-4fd3-8004-554b84c1367b:v1 \
  --authorized-party "2lxz_k9-GnzBXPFt0OCagYnVXWwoUxNMJ3-IeT-qSYA"
```

---

### Workflow 5: Update Deployment Configuration

Scale up an existing deployment:

```bash
# View current deployment
ngc cf fn deploy info <function-id>:<version-id>

# Update to new specifications (increase max instances)
ngc cf fn deploy update <function-id>:<version-id> \
  --targeted-dep-spec L40:gl40_1.br20_2xlarge:2:5:20
```

---

### Workflow 6: Debug a Failing Deployment

#### Step 1: Check deployment status

```bash
ngc cf fn deploy list --status ERROR
```

#### Step 2: Get deployment logs

```bash
ngc cf fn deploy log <function-id>:<version-id> --duration 1H
```

#### Step 3: Check instance logs

```bash
# List instances
ngc cf fn instance list <function-id>:<version-id>

# Get specific instance logs
ngc cf fn instance logs <function-id>:<version-id> \
  --instance-id <instance-id>
```

#### Step 4: Execute diagnostic command

```bash
ngc cf fn instance execute <function-id>:<version-id> \
  --instance-id <instance-id> \
  --pod-name <pod-name> \
  --container-name <container-name> \
  --command "nvidia-smi"
```

---

### Workflow 7: Set Up Rate Limiting

Protect your function from excessive requests:

```bash
# Set rate limit: 100 requests per minute
ngc cf fn update-rate-limit <function-id>:<version-id> \
  --rate-limit-pattern 100-M

# Exempt specific account from rate limiting
ngc cf fn update-rate-limit <function-id>:<version-id> \
  --rate-limit-pattern 100-M \
  --rate-limit-exempt-nca-id <trusted-nca-id>
```

---

### Workflow 8: Invoke a Deployed Function

Requires a Personal API Key enabled for Cloud Functions.

#### Get your function ID

```bash
ngc cf fn list --access-filter private --format_type json | jq -r '.[] | select(.name=="my-function") | .id'
```

#### Basic curl invocation

```bash
export NGC_API_KEY="nvapi-<your-personal-api-key>"
export FUNCTION_ID="818e9a33-e01a-457d-b3bb-5bafca412098"

curl --request POST \
  --url "https://$FUNCTION_ID.invocation.api.nvcf.nvidia.com/echo" \
  --header "Authorization: Bearer $NGC_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{"message": "hello"}'
```

#### Invoke with streaming response (SSE)

```bash
curl --request POST \
  --url "https://$FUNCTION_ID.invocation.api.nvcf.nvidia.com/v1/completions" \
  --header "Authorization: Bearer $NGC_API_KEY" \
  --header "Content-Type: application/json" \
  --header "Accept: text/event-stream" \
  --data '{"prompt": "Tell me a story", "max_tokens": 512}' \
  --no-buffer
```

#### Python invocation

```python
import os
import requests

NGC_API_KEY = os.environ["NGC_API_KEY"]  # nvapi-<token>
FUNCTION_ID = "818e9a33-e01a-457d-b3bb-5bafca412098"

response = requests.post(
    f"https://{FUNCTION_ID}.invocation.api.nvcf.nvidia.com/echo",
    headers={
        "Authorization": f"Bearer {NGC_API_KEY}",
        "Content-Type": "application/json"
    },
    json={"message": "hello"}
)

print(response.status_code)
print(response.json())
```

---

### Workflow 9: Discover Function API via OpenAPI Spec

```bash
export NGC_API_KEY="nvapi-<your-personal-api-key>"
export FUNCTION_ID="<function-id>"

# Fetch the OpenAPI spec
curl -s --request GET \
  --url "https://$FUNCTION_ID.invocation.api.nvcf.nvidia.com/openapi.json" \
  --header "Authorization: Bearer $NGC_API_KEY" \
  -o openapi.json

# List all available endpoints
cat openapi.json | jq -r '.paths | keys[]'
```

---

### Workflow 10: Graceful Function Removal

```bash
# Step 1: Gracefully remove deployment (waits for active tasks)
ngc cf fn deploy remove <function-id>:<version-id> --graceful

# Step 2: Delete the function version
ngc cf fn remove <function-id>:<version-id>
```

---

## Task Workflows

### Workflow 11: Create and Monitor a Training Task

#### Step 1: Create the task

```bash
ngc cf task create \
  --name training-job-001 \
  --container-image myorg/training:v1.0 \
  --gpu-specification A100:ga100_1.br20_4xlarge \
  --description "Model training run" \
  --max-runtime-duration 12H \
  --max-queued-duration 1D \
  --result-handling-strategy UPLOAD \
  --result-location /results
```

#### Step 2: Monitor task status

```bash
# Check task info
ngc cf task info f2a41879-1ee4-46bf-9b51-5f3da7dd139b

# Watch events for status changes
ngc cf task events f2a41879-1ee4-46bf-9b51-5f3da7dd139b
```

#### Step 3: View logs during execution

```bash
ngc cf task logs f2a41879-1ee4-46bf-9b51-5f3da7dd139b
```

#### Step 4: Retrieve results

```bash
ngc cf task results f2a41879-1ee4-46bf-9b51-5f3da7dd139b
```

---

### Workflow 11b: Helm Chart Task with Values

```bash
ngc cf task create \
  --name training-helm \
  --helm-chart myorg/training-chart:1.2.3 \
  --gpu-specification A100:ga100_1.br20_4xlarge \
  --configuration-file values.yaml \
  --set image.tag=1.2.3
```

---

### Workflow 12: Task with Environment Variables and Secrets

```bash
ngc cf task create \
  --name data-processing \
  --container-image myorg/processor:latest \
  --gpu-specification L40:gl40_1.br20_2xlarge \
  --container-environment-variable INPUT_PATH:/data/input \
  --container-environment-variable OUTPUT_PATH:/data/output \
  --container-environment-variable BATCH_SIZE:32 \
  --secret AWS_ACCESS_KEY:$AWS_ACCESS_KEY_ID \
  --secret AWS_SECRET_KEY:$AWS_SECRET_ACCESS_KEY
```

---

### Workflow 13: Debug a Failed Task

#### Step 1: Check task status

```bash
ngc cf task info <task-id>
```

Look for status: `ERRORED` or `EXCEEDED_MAX_RUNTIME_DURATION`

#### Step 2: View events for error details

```bash
ngc cf task events <task-id>
```

#### Step 3: Check container logs

```bash
ngc cf task logs <task-id>
```

#### Step 4: Check specific instance logs

```bash
# List instances
ngc cf task instance list <task-id>

# Get instance logs
ngc cf task instance logs <task-id> --instance-id <instance-id>
```

---

### Workflow 14: Execute Commands in Running Task

```bash
# List instances to get pod/container names
ngc cf task instance list <task-id>

# Execute nvidia-smi to check GPU usage
ngc cf task instance execute <task-id> \
  --instance-id <instance-id> \
  --pod-name <pod-name> \
  --container-name <container-name> \
  --command "nvidia-smi"

# Check disk usage
ngc cf task instance execute <task-id> \
  --instance-id <instance-id> \
  --pod-name <pod-name> \
  --container-name <container-name> \
  --command "df -h"
```

---

### Workflow 15: Task with Specific Cluster Targeting

```bash
ngc cf task create \
  --name targeted-task \
  --container-image myorg/myimage:latest \
  --gpu-specification L40:gl40_1.br20_2xlarge::cluster-us-west,cluster-us-east \
  --max-runtime-duration 6H
```

---

## Cluster Workflows

### Workflow 16: Register an AWS Cluster

```bash
ngc cf cluster create \
  --cluster-name aws-prod-cluster \
  --cluster-group-name production \
  --cloud-provider AWS \
  --region us-west-2 \
  --ssa-client-id abc123-def456 \
  --cluster-description "Production cluster in AWS us-west-2" \
  --capability DynamicGPUDiscovery \
  --capability LogPosting
```

---

### Workflow 17: Register an On-Premise Cluster

```bash
ngc cf cluster create \
  --cluster-name onprem-datacenter \
  --cluster-group-name datacenter \
  --cloud-provider ON-PREM \
  --region us-east-1 \
  --ssa-client-id xyz789-abc123 \
  --cluster-description "On-premise datacenter cluster"
```

---

## GPU Workflows

### Workflow 18: Check Capacity Before Deployment

```bash
# Check L40 capacity in us-west-2
ngc cf gpu capacity --region us-west-2 --gpu L40

# Check overall quota
ngc cf gpu quota

# Look up available instance types
ngc cf gpu info L40
```

---

### Workflow 19: Check Quota and Plan a Deployment

GPU quota controls how many GPUs of each type an org can use. Quota is shared across functions and tasks. Before deploying, always check quota to understand limits and determine if clusters or regions must be specified.

#### Step 1: Check quota rules

```bash
ngc cf gpu quota --format_type json
```

Example output (abbreviated):
```json
{
  "gpus": [
    {
      "name": "L40",
      "quota": 100,
      "instance-types": "*"
    },
    {
      "name": "A100",
      "quota": 0,
      "instance-types": "*",
      "dedicated-clusters": [
        { "names": "nvcf-dgxc-k8s-oci-ord-dev1", "limit": 4 }
      ]
    },
    {
      "name": "H100",
      "quota": 50,
      "instance-types": "H100_1x,H100_2x",
      "regions": [
        { "names": "us-east-1", "limit": 30 },
        { "names": "eu-west-1", "limit": 20 }
      ]
    }
  ]
}
```

How to read this:
- **L40**: 100 GPU quota, any instance type, no cluster/region restrictions. Deploy without specifying cluster or region.
- **A100**: `quota: 0` means no shared-cluster quota, but 4 GPUs on the dedicated cluster `nvcf-dgxc-k8s-oci-ord-dev1`. You **must** include the cluster in `--targeted-dep-spec`.
- **H100**: 50 GPU quota, restricted to `H100_1x` and `H100_2x` instance types, with region limits (30 in us-east-1, 20 in eu-west-1). You should include the region in `--targeted-dep-spec`.

**Note on quota scope:** Quota enforcement only applies to **public** clusters (`authorizedNcaId: *`). Private clusters (BYOC, owned by the org) and shared clusters (authorized for specific orgs) are **not** subject to quota -- unless they appear under `dedicated-clusters` in the quota rules with an explicit limit. If deploying to a private or shared cluster that has no dedicated-cluster entry, no quota rule is needed for that GPU type.

#### Step 2: Check current GPU usage

```bash
ngc cf gpu list --format_type json
```

Compare current usage against quota limits to see how many GPUs are available.

#### Step 3: Discover available clusters and instance types

```bash
ngc cf gpu info A100
```

This shows valid cluster names, instance types, and regions for A100 GPUs.

#### Step 4: Deploy based on quota rules

For L40 (no cluster/region restrictions):
```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec L40:gl40_1.br20_2xlarge:1:3:10
```

For A100 (dedicated cluster required):
```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec A100:OCI.GPU.A100_1x:1:1:1:nvcf-dgxc-k8s-oci-ord-dev1
```

For H100 (region required):
```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec H100:OCI.GPU.H100_1x:1:2:5::us-east-1
```

#### GPU counting

Quota is in GPUs, not instances. Multi-GPU instance types use more quota:
- `H100_1x` = 1 GPU
- `H100_4x` = 4 GPUs
- `H100_8x` = 8 GPUs
- `H100_8x.x4` = 32 GPUs (4 nodes x 8)

With `quota: 50` for H100, deploying `max: 2` of `H100_8x` uses 16 GPUs (2 x 8).

#### Common quota errors

| Error | What to do |
|-------|------------|
| `FAILED_MISSING_CLUSTERS` | Quota has cluster limits -- add cluster to `--targeted-dep-spec` (6th field) |
| `EXCEED_DEDICATED_CLUSTER_QUOTA_LIMITS` | Cluster's GPU limit reached -- reduce instances or free up other deployments |
| `Insufficient quota for ... in region` | Region limit reached -- reduce instances or try another region |

---

## Registry Workflows

### Workflow 20: Build, Push, and Deploy a Custom Container from NGC

End-to-end workflow for a locally-built container image. This is the most common pattern and the one most likely to go wrong if steps are skipped.

#### Step 1: Confirm your org

```bash
ngc config current
```

Note the org name (e.g., `myorg`) from the output.

#### Step 2: Build the image

```bash
docker build -t my-fastapi-app:v1.0 .
```

#### Step 3: Authenticate to the NGC registry

```bash
NGC_API_KEY=$(grep -E '^[[:space:]]*apikey[[:space:]]*=' ~/.ngc/config 2>/dev/null | head -1 | sed 's/.*=[[:space:]]*//')
echo "$NGC_API_KEY" | docker login nvcr.io -u '$oauthtoken' --password-stdin
```

#### Step 4: Tag and push the image

```bash
docker tag my-fastapi-app:v1.0 nvcr.io/myorg/my-fastapi-app:v1.0
docker push nvcr.io/myorg/my-fastapi-app:v1.0
```

#### Step 5: Verify the image exists in the registry

Do not skip this step. If the image is not listed, the deployment will fail.

```bash
ngc registry image info myorg/my-fastapi-app:v1.0
```

#### Step 6: Create the function

```bash
ngc cf fn create \
  --name my-fastapi-app \
  --inference-url /predict \
  --container-image nvcr.io/myorg/my-fastapi-app:v1.0 \
  --health-uri /health \
  --health-port 8000
```

#### Step 7: Deploy the function

```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec L40:gl40_1.br20_2xlarge:1:1:5
```

---

### Workflow 21: List and Inspect NGC Registry Contents

#### List container images

```bash
# All images in the configured org
ngc registry image list

# Filter by name
ngc registry image list myorg/my-*

# With JSON output for scripting
ngc registry image list --format_type json
```

#### List Helm charts

```bash
ngc registry chart list
```

#### List models

```bash
ngc registry model list
```

#### List resources

```bash
ngc registry resource list
```

#### Inspect a specific image

```bash
ngc registry image info myorg/my-inference-app:v1.0
```

---

### Workflow 22: Deploy a Function with an NGC Model

Mount model weights from the NGC registry into a function container without baking them into the image.

#### Step 1: Find the model

```bash
ngc registry model list
ngc registry model info myorg/llm-weights:v1.0
```

#### Step 2: Create the function with the model attached

```bash
ngc cf fn create \
  --name model-inference \
  --inference-url /v1/completions \
  --container-image nvcr.io/myorg/inference-server:v1 \
  --health-uri /health \
  --model myorg/llm-weights:v1.0
```

The model files are mounted at `/mount/models/llm-weights/v1.0` inside the container.

#### Step 3: Deploy

```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec H100:OCI.GPU.H100_1x:1:1:1:my-cluster
```

---

### Workflow 23: Deploy a Function with NGC Resources

Attach datasets, configs, or other file collections from the NGC registry.

```bash
ngc cf fn create \
  --name data-processor \
  --inference-url /v1/process \
  --container-image nvcr.io/myorg/processor:v1 \
  --health-uri /health \
  --resource myorg/config-bundle:v1.0 \
  --resource myorg/reference-data:v2.0
```

Resources are mounted at `/mount/resources/<name>/<version>`.

---

## Common Patterns

### Get function ID from name

```bash
ngc cf fn list --name-pattern "my-function*" --format_type json | jq -r '.[0].id'
```

### Get task ID from name

```bash
ngc cf task list --format_type json | jq -r '.[] | select(.name=="my-task") | .id'
```

### List all active deployments

```bash
ngc cf fn deploy list --status ACTIVE --format_type json
```

### Restart all instances of a deployment

```bash
ngc cf fn deploy restart <function-id>:<version-id>
```

### Wait for task completion

```bash
while true; do
  STATUS=$(ngc cf task info <task-id> --format_type json | jq -r '.status')
  echo "Status: $STATUS"
  if [[ "$STATUS" == "COMPLETED" || "$STATUS" == "ERRORED" || "$STATUS" == "CANCELED" ]]; then
    break
  fi
  sleep 30
done
```

### Filter capacity by multiple GPUs

```bash
ngc cf gpu capacity --gpu L40 --gpu A100 --gpu H100
```

### Check capacity across regions

```bash
ngc cf gpu capacity --region us-east-1 --region us-west-2 --region eu-central-1
```
