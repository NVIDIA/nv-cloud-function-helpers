# NGC Cloud Function Reference

Detailed reference for managing cloud functions via NGC CLI.

## Creating Functions

### Container-based function

```bash
ngc cf fn create \
  --name <function-name> \
  --inference-url <endpoint-path> \
  --container-image <image-path> \
  [--health-uri <path>] \
  [--health-port <port>] \
  [--description "<description>"] \
  [--secret <name:value>] \
  [--json-secret-file <file.json>] \
  [--container-environment-variable <key:value>] \
  [--container-args "<args>"] \
  [--inference-port <port>] \
  [--function-type <DEFAULT|STREAMING>] \
  [--health-timeout <duration>] \
  [--health-protocol <HTTP|gRPC>] \
  [--health-expected-status-code <code>] \
  [--model <org>/[<team>/]<model>:<version>] \
  [--resource <org>/[<team>/]<resource>:<version>] \
  [--tag <tag>] \
  [--rate-limit-pattern <NUMBER-S|M|H|D>] \
  [--rate-limit-exempt-nca-id <nca-id>] \
  [--metrics-telemetry-id <uuid>] \
  [--logs-telemetry-id <uuid>] \
  [--traces-telemetry-id <uuid>]
# Telemetry endpoint IDs: obtain via ngc cf telemetry-endpoint create/list
```

**Important:** If the container is not Triton-based, you almost certainly need `--health-uri` and possibly `--health-port`. See [Health check configuration](#health-check-configuration) below.

**`--inference-url` is required.** Before creating any function, determine the correct `--inference-url` value:

1. **Check the user's source code or Dockerfile** for the endpoint path the container serves (e.g., `/predict`, `/v1/completions`, `/generate`).
2. **Check the container image name** for well-known frameworks (vLLM → `/v1/completions`, Triton → `/v2/models/{model}/infer`).
3. **If neither is conclusive, use `"/"`** as the default.

For **STREAMING** functions (Low Latency Streaming for graphical workloads), also **confirm the inference port** with the user before proceeding — STREAMING workloads often use non-standard ports. Do not set `--function-type STREAMING` on regular API functions.

### Container image formats

| Registry | Format | Example |
|----------|--------|---------|
| NGC | `<org>/[<team>/]<image>:<tag>` | `nvidia/pytorch:24.01-py3` |
| Docker Hub | `docker.io/<org>/<image>:<tag>` | `docker.io/vllm/vllm-openai:latest` |
| AWS ECR (private) | `<account_id>.dkr.ecr.<region>.amazonaws.com/<repo>:<tag>` | `123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest` |
| AWS ECR (public) | `public.ecr.aws/<alias>/<repo>:<tag>` | `public.ecr.aws/my-alias/my-app:latest` |
| Other registries | Full URL with registry | `ghcr.io/org/image:tag` |

**Important:** Third-party images require the full registry path. Using short forms will fail with "Invalid artifact provided".

### Helm chart function

```bash
ngc cf fn create \
  --name <function-name> \
  --inference-url <endpoint-path> \
  --helm-chart <org>/[<team>/]<chart>:<tag> \
  --helm-chart-service <service-name> \
  [--health-uri <path>] \
  [--health-port <port>]
```

#### Helm chart port mapping

When creating a function from a Helm chart, the `--inference-port` must be set to the **Kubernetes service port** (`spec.ports[].port` in the chart's `service.yaml`), NOT the container's `targetPort` or any `values.yaml` variable.

To determine the correct port:
1. Read the chart's `service.yaml` and find `spec.ports[].port` under the entrypoint service
2. Use that value as `--inference-port`

**Do NOT** use `targetPort` or `values.yaml` variables like `inferencePort` — these are internal container ports, not the service-level port NVCF routes traffic to.

#### Resolving health URI before function creation

**Required:** Before creating any function, you must determine the correct `--health-uri` value. Do not guess. Follow this checklist in order:

1. **Check for explicit health endpoint info.** For container functions, inspect the Dockerfile or source. For Helm chart functions, check deployment.yaml for `readinessProbe` or `livenessProbe` — if a probe defines `httpGet.path`, use that as `--health-uri` (and the probe's `port` as `--health-port` if it differs from 8000).
2. **Check the container image name** for well-known frameworks (e.g., Triton → `/v2/health/ready`, vLLM → `/health`). If clearly one of these, use the documented value.
3. **If neither source is conclusive, stop and ask the user.** Do not guess. Prompt: *"What path does the service use for health checks? (e.g., /health, /healthz)"*

**Transparency:** When you set `--health-uri`, always state what source you used and what value you chose before running `fn create`. Example: *"The deployment.yaml has a readinessProbe at `/healthz` on port 8080 — I'll use `--health-uri /healthz --health-port 8080`."* This lets the user correct the value immediately instead of discovering the problem after a failed deployment.

### Health check configuration

NVCF uses a health endpoint to determine when a container is ready to receive traffic. If the health check fails, the deployment will not become ACTIVE.

**Default behavior:** If no health options are specified, NVCF probes `GET /v2/health/ready` on port `8000`. This default is designed for NVIDIA Triton Inference Server. Most other containers (FastAPI, Flask, custom services, etc.) do **not** serve this endpoint and will fail health checks unless configured.

**Agent instructions:** When creating a function, always consider whether the container exposes the default health endpoint. If the container is not Triton-based, you should set `--health-uri` (and `--health-port` if needed) at function creation time. Do not modify the user's application code to add a `/v2/health/ready` endpoint -- use the CLI flags to match the container's actual health endpoint instead.

Common patterns:
- **FastAPI / uvicorn apps**: Typically serve a health route like `/health` or `/` on port `8000`
- **vLLM**: Uses `/health` on port `8000`
- **Triton Inference Server**: Uses the default `/v2/health/ready` on port `8000` (no flags needed)
- **Custom services**: Ask the user or inspect the Dockerfile / source for the health route and port

```bash
--health-uri <path>                   # Health endpoint path (default: /v2/health/ready)
--health-port <port>                  # Health endpoint port (default: 8000)
--health-timeout <duration>           # Probe timeout in ISO 8601 duration (e.g., PT10S for 10 seconds)
--health-protocol <HTTP|gRPC>         # Protocol for health probe (default: HTTP)
--health-expected-status-code <code>  # Expected HTTP status code (default: 200)
```

Example -- FastAPI app with a `/health` endpoint on port 8080:

```bash
ngc cf fn create \
  --name my-fastapi-fn \
  --inference-url /predict \
  --container-image nvcr.io/my-org/my-image:latest \
  --health-uri /health \
  --health-port 8080
```

**Tip:** If a deployment gets stuck or instances fail health checks, verify the health configuration matches the container. Use `ngc cf fn info <function-id>:<version-id> --format_type json` to inspect the current health settings, and check instance logs for probe failures.

## Listing and Viewing Functions

```bash
# List functions owned by your organization (default - excludes shared functions)
ngc cf fn list --access-filter private

# List all functions including shared/public
ngc cf fn list

# Filter by name pattern
ngc cf fn list --access-filter private --name-pattern "my-*"

# Filter by access type: private (org-owned), public (shared), authorized (granted access)
ngc cf fn list --access-filter <private|public|authorized>

# Get function details
ngc cf fn info <function-id>:<version-id>
```

## Deployments

**Always use `--targeted-dep-spec` for deployments.** The CLI also offers `--deployment-specification` (aka `--dep-spec`), but do not use it -- `--targeted-dep-spec` is a superset that supports all the same deployments plus cluster, region, and attribute targeting.

### Create deployment

```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec <gpu>:<instance_type>:<min>:<max>[:<concurrency>][:<clusters>][:<regions>][:<attributes>][:<preferredOrder>] \
  [--configuration-file <file.yaml>] \
  [--configuration <json>] \
  [--set <key1.key2=value>]
```

All fields after `max` are optional and positional. Use commas for multiple values within a field. Skip middle fields with empty colons (`::`). Can be specified multiple times for multi-spec deployments.

| Field | Position | Format | Example |
|-------|----------|--------|---------|
| gpu | 1 (required) | GPU type | `A100` |
| instance_type | 2 (required) | Instance type | `OCI.GPU.A100_1x` |
| min | 3 (required) | Min instances | `1` |
| max | 4 (required) | Max instances | `3` |
| concurrency | 5 | Max request concurrency | `10` |
| clusters | 6 | Comma-separated cluster names | `cluster-a,cluster-b` |
| regions | 7 | Comma-separated regions | `us-east-1,eu-west-1` |
| attributes | 8 | Comma-separated attributes | `attr1,attr2` |
| preferredOrder | 9 | Integer priority (for multi-spec) | `1` |

**Warning:** The CLI `--help` shows wrapper syntax like `clusters(c1,c2)` and `regions(r1,r2)`, but the CLI does not parse these wrappers. Always use plain values in the positional colon-separated format shown above.
**Note:** The CLI requires clusters for non-GFN instance types (OCI/DGX). If you see `FAILED_MISSING_CLUSTERS`, add a cluster in the 6th field.

#### Examples

Basic (no cluster/region targeting):
```bash
ngc cf fn deploy create abc123:v1 \
  --targeted-dep-spec L40:gl40_1.br20_2xlarge:1:3:10
```

Single cluster:
```bash
ngc cf fn deploy create abc123:v1 \
  --targeted-dep-spec A100:OCI.GPU.A100_1x:1:1:1:nvcf-dgxc-k8s-oci-ord-dev1
```

Multiple clusters:
```bash
ngc cf fn deploy create abc123:v1 \
  --targeted-dep-spec L40:gl40_1.br20_2xlarge:1:3:10:cluster-west,cluster-east
```

Cluster + region:
```bash
ngc cf fn deploy create abc123:v1 \
  --targeted-dep-spec A100:OCI.GPU.A100_1x:1:2:5:my-cluster:us-east-1
```

Region only (skip cluster with empty field when allowed):
```bash
ngc cf fn deploy create abc123:v1 \
  --targeted-dep-spec L40:gl40_1.br20_2xlarge:1:2:5::us-east-1
```

Multiple deployment specs with priority ordering:
```bash
ngc cf fn deploy create abc123:v1 \
  --targeted-dep-spec A100:OCI.GPU.A100_1x:1:1:1:cluster-primary:::1 \
  --targeted-dep-spec A100:OCI.GPU.A100_2x:0:1:1:cluster-fallback:::2
```

**Tip:** Use `ngc cf gpu info <gpu-type>` to discover available clusters and instance types. Use `ngc cf gpu quota --format_type json` to check for dedicated cluster quota limits that require explicit cluster targeting.

### Update deployment

```bash
ngc cf fn deploy update <function-id>:<version-id> \
  --targeted-dep-spec <gpu>:<instance_type>:<min>:<max>[:<concurrency>][:<clusters>][:<regions>][:<attributes>][:<preferredOrder>] \
  [--configuration-file <file.yaml>] \
  [--configuration <json>] \
  [--set <key1.key2=value>]
```

### Manage deployments

```bash
# List all deployments
ngc cf fn deploy list

# Filter by status
ngc cf fn deploy list --status <ACTIVE|ERROR>

# Get deployment info
ngc cf fn deploy info <function-id>:<version-id>

# Restart deployment
ngc cf fn deploy restart <function-id>:<version-id>

# Remove deployment
ngc cf fn deploy remove <function-id>:<version-id>

# Graceful removal (wait for tasks to complete)
ngc cf fn deploy remove <function-id>:<version-id> --graceful
```

### Query deployment logs

```bash
ngc cf fn deploy log <function-id>:<version-id> \
  [--start-time yyyy-MM-dd::HH:mm:ss] \
  [--end-time yyyy-MM-dd::HH:mm:ss] \
  [--duration <nD><nH><nM><nS>]
```

## Instance Management

```bash
# List instances
ngc cf fn instance list <function-id>:<version-id>

# Get instance logs
ngc cf fn instance logs <function-id>:<version-id> \
  --instance-id <instance-id> \
  [--pod-name <pod>] \
  [--container-name <container>]

# Execute command in instance
ngc cf fn instance execute <function-id>:<version-id> \
  --instance-id <instance-id> \
  --pod-name <pod> \
  --container-name <container> \
  --command "<command>"
```

## Function Invocation

For detailed invocation documentation (HTTP, Python, gRPC, streaming, OpenAPI discovery, API key handling, troubleshooting), see the invocation reference linked from SKILL.md.

Quick reference (assumes `NGC_API_KEY` is set):

```bash
curl --request POST \
  --url "https://<function-id>.invocation.api.nvcf.nvidia.com/<url-path>" \
  --header "Authorization: Bearer $NGC_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{"your": "payload"}'
```

## Authorization

Control which accounts can invoke your function:

```bash
# View authorized parties
ngc cf fn auth info <function-id>:<version-id>

# Authorize an account (by NCA ID)
ngc cf fn auth add <function-id>:<version-id> \
  --authorized-party <nca-id>

# Remove authorization
ngc cf fn auth remove <function-id>:<version-id> \
  --authorized-party <nca-id>

# Clear all authorizations
ngc cf fn auth clear <function-id>:<version-id>
```

## Secrets

**Important:** Secrets can only be added or modified when the function is in **INACTIVE** state. Check state with `ngc cf fn info <fn-id>:<version-id>` first. If ACTIVE, undeploy → add secret → redeploy.

```bash
# Update secrets
ngc cf fn update-secret <function-id>:<version-id> \
  --secret <name:value>

# Update from JSON file
ngc cf fn update-secret <function-id>:<version-id> \
  --json-secret-file <filename.json>
```

## Rate Limiting

```bash
# Set rate limit (format: NUMBER-S|M|H|D)
ngc cf fn update-rate-limit <function-id>:<version-id> \
  --rate-limit-pattern 100-M \
  [--rate-limit-exempt-nca-id <nca-id>]

# Remove rate limit
ngc cf fn remove-rate-limit <function-id>:<version-id>
```

Rate limit patterns:
- `10-S` - 10 requests per second
- `100-M` - 100 requests per minute
- `1000-H` - 1000 requests per hour
- `10000-D` - 10000 requests per day

## Registry Credentials

Private registries require credentials to be configured:

### AWS ECR Private

```bash
ngc cf registry-credential create \
  --hostname <account_id>.dkr.ecr.<region>.amazonaws.com \
  --name my-ecr-credential \
  --key <aws_secret_access_key> \
  --aws-access-key <aws_access_key_id> \
  --type CONTAINER
```

### AWS ECR Public

```bash
ngc cf registry-credential create \
  --hostname public.ecr.aws \
  --name my-ecr-public-credential \
  --key <aws_secret_access_key> \
  --aws-access-key <aws_access_key_id> \
  --type CONTAINER
```

For detailed third-party registry setup, see the [NVIDIA Cloud Functions Third-Party Registries documentation](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/third-party-registries.html).

## Deleting Functions

```bash
# Delete specific version
ngc cf fn remove <function-id>:<version-id>

# Delete all versions
ngc cf fn remove <function-id>
```
