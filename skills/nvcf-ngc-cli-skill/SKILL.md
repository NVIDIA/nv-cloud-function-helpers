---
name: nvcf-ngc-cli-skill
description: Comprehensive skill for NVIDIA Cloud Functions (NVCF) via NGC CLI. Covers functions, tasks, clusters, GPU management, and the NGC registry (nvcr.io). Use when working with cloud functions, deployments, batch tasks, cluster registration, GPU capacity, container images, Helm charts, models, resources, or when the user mentions ngc cf, NVCF, cloud functions, function deployment, GPU quota, nvcr.io, ngc registry, pushing images, or container registry.
compatibility: Requires NGC CLI installed and configured
metadata:
  author: "nvcf-core-eng <nvcf-core-eng@exchange.nvidia.com>"
  version: "1.0"
  tags:
    - ngc
    - nvcf
    - cloud-functions
    - deployment
    - serverless
    - task
    - batch
    - cluster
    - gpu
    - cli
    - registry
    - nvcr
    - container-image
    - helm-chart
    - model
    - resource
  languages:
    - bash
    - python
  frameworks:
    - ngc-cli
  domain: cloud-infrastructure
---

# NGC Cloud Functions CLI Skill

Complete reference for managing NVIDIA Cloud Functions (NVCF) via NGC CLI.

## Before You Start

Run `ngc config current` **once** at the beginning of a session to confirm which organization is active. Report the org name and ID to the user. After that, do not re-run it -- remember the result for the rest of the session.

```bash
ngc config current
```

### Do Not Modify NGC Configuration

**Never** change the active organization, team, or any other NGC CLI configuration on behalf of the user. This includes commands like `ngc config set`, `ngc config set --org`, or any operation that modifies `~/.ngc/config`. Only the user may change their NGC configuration explicitly.

If the user needs to operate on a different org than the one configured, use the `--org` flag on the specific command instead. Use `ngc org list` to discover available orgs and their IDs:

```bash
ngc org list
```

The `--org` flag accepts the **org ID** (the alphanumeric string shown in parentheses), not the display name. For example, if `ngc org list` shows `sae-sme-nvcf (0530795645140221)`, use:

```bash
ngc cf gpu quota --org 0530795645140221
```

### Verify NGC_API_KEY (Required Before Invocation)

If the task involves invoking a function (via curl, HTTP, or any script), you **must** verify `NGC_API_KEY` is available in the agent's shell **before** attempting any invocation. Do not attempt invocation first and troubleshoot after failure.

```bash
[ -n "$NGC_API_KEY" ] && echo "NGC_API_KEY is configured" || echo "NGC_API_KEY is not set"
```

If `NGC_API_KEY` is not set, try to load it from the NGC CLI config:

```bash
NGC_API_KEY=$(grep -E '^[[:space:]]*apikey[[:space:]]*=' ~/.ngc/config 2>/dev/null | head -1 | sed 's/.*=[[:space:]]*//')
[ -n "$NGC_API_KEY" ] && export NGC_API_KEY && echo "NGC_API_KEY loaded from NGC CLI config" || echo "NGC_API_KEY could not be resolved"
```

If neither method works, **stop and help the user resolve this before proceeding**. See [Invocation Reference - API Key Handling](references/invocation.md) for resolution steps. Do not attempt the invocation -- it will fail with a 401 error.

### Do Not Bypass the CLI

All NVCF management operations must go through the NGC CLI. Do not attempt to call NGC/NVCF REST APIs directly (via curl, Python requests, etc.) to work around CLI errors or authentication restrictions. If a CLI command fails -- for example, requiring browser authentication -- stop and report the issue to the user. The CLI enforces authentication and authorization checks that direct API calls may bypass incorrectly, leading to confusing errors or invalid state.

**Exception:** Function invocation is done via direct HTTP calls (curl), not the CLI. See [Invocation Reference](references/invocation.md) for details.

## Prerequisites

1. **Install NGC CLI**: Download from [NGC CLI Documentation](https://docs.ngc.nvidia.com/cli/index.html)
2. **Configure authentication**:
   ```bash
   ngc config set
   ```
   Enter your API key and default org/team when prompted.

## Environment Configuration

### Production (Default)

No additional configuration needed.

### Staging Environment

```bash
export NGC_CLI_API_URL=https://api.stg.ngc.nvidia.com
export NGC_CLI_API_KEY=<your-staging-api-key>
```

## Command Structure

All NVCF commands use the `ngc cloud-function` (or `ngc cf`) prefix:

```bash
ngc cloud-function <subcommand> [options]
ngc cf <subcommand> [options]  # shorthand
```

## Common Options

| Option | Description |
|--------|-------------|
| `--org <id>` | Specify organization by ID (overrides config default). Use `ngc org list` to find org IDs. |
| `--team <name>` | Specify team (use `--team no-team` for no team) |
| `--format_type <fmt>` | Output format: `ascii` (default), `csv`, `json` |
| `--debug` | Enable debug mode for troubleshooting |

## Quick Reference

### Functions (`ngc cf fn`)

Manage cloud functions and deployments. See [references/functions.md](references/functions.md) for details.

```bash
# Create function (set --health-uri if not using Triton; default is /v2/health/ready)
ngc cf fn create --name <name> --inference-url <path> --container-image <image> \
  [--health-uri <health-endpoint>] [--health-port <port>]

# List functions (org-owned only)
ngc cf fn list --access-filter private

# Get function info
ngc cf fn info <function-id>:<version-id>

# Create deployment
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec <gpu>:<instance_type>:<min>:<max>[:<concurrency>][:<clusters>][:<regions>][:<attributes>][:<preferredOrder>]

# List deployments
ngc cf fn deploy list

# Remove deployment
ngc cf fn deploy remove <function-id>:<version-id>

# Delete function
ngc cf fn remove <function-id>:<version-id>
```

### Tasks (`ngc cf task`)

Manage batch tasks/jobs. See [references/tasks.md](references/tasks.md) for details.

```bash
# Create task
ngc cf task create --name <name> --container-image <image> \
  --gpu-specification <gpu>:<instance_type>[:<backend>][:<clusters>]

# List tasks
ngc cf task list

# Get task info
ngc cf task info <task-id>

# View task events
ngc cf task events <task-id>

# View task logs
ngc cf task logs <task-id>

# Cancel task
ngc cf task cancel <task-id>

# Delete task
ngc cf task delete <task-id>
```

### Clusters (`ngc cf cluster`)

Register and manage clusters. See [references/clusters.md](references/clusters.md) for details.

```bash
# List clusters
ngc cf cluster list

# Get cluster info
ngc cf cluster info <cluster-id>

# Register cluster
ngc cf cluster create --cluster-name <name> --cluster-group-name <group> \
  --cloud-provider <provider> --region <region> --ssa-client-id <id>

# Delete cluster
ngc cf cluster delete <cluster-id>
```

### GPUs (`ngc cf gpu`)

View GPU capacity and quotas. See [references/gpus.md](references/gpus.md) for details.

```bash
# List allocated GPUs
ngc cf gpu list

# View capacity
ngc cf gpu capacity [--region <region>] [--gpu <type>]

# View quota (use JSON to see cluster/region limits)
ngc cf gpu quota --format_type json

# Get GPU info (instance types, clusters)
ngc cf gpu info <gpu-type>

# List available GPUs (Admin)
ngc cf available-gpus
```

**Quota key facts:** GPU quota controls how many GPUs of each type an org can use. Quota is counted in GPUs (not instances) and is evaluated against **maxInstances**. An `H100_4x` with max=2 uses 8 GPUs of quota (2 x 4). Functions and tasks share the same quota. To check usage, use `ngc cf fn deploy list --format_type json` and sum `maxInstances x GPUs-per-instance-type` per GPU type. If the quota JSON shows `clusters` or `dedicated-clusters` entries, the deployment spec **must** include an explicit cluster name. If it shows `regions` entries, include the region. See [references/gpus.md](references/gpus.md) for full quota details, GPU counting rules, enforcement rules, and error resolution.

### Registry (`ngc registry`)

Manage container images, Helm charts, models, and resources in the NGC registry (nvcr.io). See [references/registry.md](references/registry.md) for details.

**Critical:** Images must exist in the registry before creating a function or task that references them. If you build an image locally, you must push it to nvcr.io (or another accessible registry) first. Do not create a function referencing an image that has not been pushed.

```bash
# Authenticate Docker to NGC registry
echo "$NGC_API_KEY" | docker login nvcr.io -u '$oauthtoken' --password-stdin

# Tag and push a local image to NGC
docker tag my-app:v1 nvcr.io/<org>/my-app:v1
docker push nvcr.io/<org>/my-app:v1

# Verify the image exists before creating a function
ngc registry image info <org>/my-app:v1

# List images / charts / models / resources
ngc registry image list
ngc registry chart list
ngc registry model list
ngc registry resource list
```

**Image not found?** Verify the active org with `ngc config current`. Try `ngc registry image list --org <org-id>` to specify the org explicitly.

## Function Lifecycle

1. **Create** function (defines container/helm chart, inference URL, health endpoint, secrets)
2. **Deploy** function (allocates GPUs, starts instances, waits for health check)
3. **Manage** instances, authorization, secrets, rate limits
4. **Invoke** via HTTP/gRPC
5. **Remove** deployment and function when done

**Health check note:** At creation time, set `--health-uri` to match the container's actual health endpoint. The default (`/v2/health/ready`) is for Triton Inference Server. Most other containers (FastAPI, vLLM, custom services) use a different path (e.g., `/health`, `/healthz`, `/`). Getting this wrong causes deployments to fail or get stuck. See [references/functions.md](references/functions.md) for details.

### Container Image Formats

| Registry | Format |
|----------|--------|
| NGC | `<org>/[<team>/]<image>:<tag>` |
| Docker Hub | `docker.io/<org>/<image>:<tag>` |
| AWS ECR | `<account_id>.dkr.ecr.<region>.amazonaws.com/<repo>:<tag>` |

**Important:** Third-party images require the full registry path.

### Deployment Specification Format

**Always use `--targeted-dep-spec` for deployments.** The CLI also offers `--deployment-specification` (aka `--dep-spec`), but do not use it -- `--targeted-dep-spec` is a superset that supports all the same deployments plus cluster, region, and attribute targeting.

```
<gpu>:<instance_type>:<min>:<max>[:<concurrency>][:<clusters>][:<regions>][:<attributes>][:<preferredOrder>]
```

All fields after max are optional and positional. Use commas for multiple values within a field. Skip middle fields with empty colons (`::`).

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

Examples:
- Basic: `L40:gl40_1.br20_2xlarge:1:3:10`
- Cluster: `A100:OCI.GPU.A100_1x:1:1:1:my-cluster`
- Cluster + region: `A100:OCI.GPU.A100_1x:1:1:1:my-cluster:us-east-1`
- Region only (skip cluster): `H100:OCI.GPU.H100_1x:1:2:5::us-east-1`
- Multi-spec with priority: `L40:gl40_1.br20_2xlarge:1:3:10:cluster-a:::1`

Use `ngc cf gpu info <gpu>` to discover available clusters, instance types, and regions. Use `ngc cf gpu quota --format_type json` to check for dedicated cluster quota limits that require explicit cluster targeting.

**Warning:** The CLI `--help` shows wrapper syntax like `clusters(c1,c2)` and `regions(r1,r2)`, but the CLI does not parse these wrappers. Always use plain values in the positional colon-separated format shown above.

### Invoking Functions

See [references/invocation.md](references/invocation.md) for detailed invocation documentation.

**Prerequisite:** You must confirm `NGC_API_KEY` is set in the agent's shell before running any invocation command. Follow the [Verify NGC_API_KEY](#verify-ngc_api_key-required-before-invocation) steps above. Do not proceed with invocation until the key is confirmed. Never ask the user for the key value directly.

```bash
curl --request POST \
  --url "https://<function-id>.invocation.api.nvcf.nvidia.com/<inference-url-path>" \
  --header "Authorization: Bearer $NGC_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{"your": "payload"}'
```

## Task Lifecycle

1. **Create** task with GPU specification
2. **Monitor** status via events and logs
3. **Retrieve** results when complete
4. **Delete** task when done

### GPU Specification Format

```
<gpu>:<instance_type>[:<backend>][:<cluster_1,cluster_2>]
```

Example: `A100:ga100_1.br20_4xlarge`

### Task Status Values

| Status | Description |
|--------|-------------|
| `QUEUED` | Waiting for resources |
| `RUNNING` | Currently executing |
| `COMPLETED` | Finished successfully |
| `CANCELED` | Manually canceled |
| `ERRORED` | Failed with error |
| `EXCEEDED_MAX_RUNTIME_DURATION` | Timed out |

### Duration Format (ISO 8601)

- `1H` - 1 hour
- `30M` - 30 minutes
- `1H30M` - 1 hour 30 minutes
- `1D12H` - 1 day 12 hours

## GPU Types

| GPU | Description | Use Cases |
|-----|-------------|-----------|
| `GB200` | NVIDIA GB200 | Next-gen AI workloads |
| `H100` | NVIDIA H100 | Large-scale training, LLMs |
| `A100` | NVIDIA A100 | Training, large models |
| `L40S` | NVIDIA L40S | Enhanced inference, media |
| `L40` | NVIDIA L40 | Inference, light training |
| `T10` | NVIDIA T10 | Cost-effective inference |

## Instance Type Formats

| Format | Example | Description |
|--------|---------|-------------|
| OCI format | `OCI.GPU.H100_1x` | 1x H100 on OCI |
| OCI multi-node | `OCI.GPU.H100_8x.x4` | 4 nodes of 8x H100 |
| DGX Cloud | `DGX-CLOUD.GPU.L40_1x` | 1x L40 on DGX Cloud |
| GFN format | `gl40_1.br20_2xlarge` | 1x L40 (GFN backend) |

Use `ngc cf gpu info <gpu-type>` to see all available instance types.

## Cluster Configuration

### Supported Cloud Providers

| Provider | Description |
|----------|-------------|
| `AWS` | Amazon Web Services |
| `AZURE` | Microsoft Azure |
| `GCP` | Google Cloud Platform |
| `OCI` | Oracle Cloud Infrastructure |
| `DGX-CLOUD` | NVIDIA DGX Cloud |
| `ON-PREM` | On-premise infrastructure |

### Supported Regions

`us-east-1`, `us-west-1`, `us-west-2`, `eu-central-1`, `eu-north-1`, `eu-south-1`, `eu-west-1`, `ap-east-1`

## Authorization

Control which accounts can invoke your function:

```bash
# View authorized parties
ngc cf fn auth info <function-id>:<version-id>

# Authorize an account (by NCA ID)
ngc cf fn auth add <function-id>:<version-id> --authorized-party <nca-id>

# Remove authorization
ngc cf fn auth remove <function-id>:<version-id> --authorized-party <nca-id>
```

## Rate Limiting

```bash
# Set rate limit (format: NUMBER-S|M|H|D)
ngc cf fn update-rate-limit <function-id>:<version-id> --rate-limit-pattern 100-M

# Remove rate limit
ngc cf fn remove-rate-limit <function-id>:<version-id>
```

Rate limit patterns: `10-S` (per second), `100-M` (per minute), `1000-H` (per hour), `10000-D` (per day)

## Secrets Management

```bash
# Function secrets
ngc cf fn update-secret <function-id>:<version-id> --secret <name:value>

# Task secrets
ngc cf task update-secret <task-id> --secret <name:value>

# From JSON file
ngc cf fn update-secret <function-id>:<version-id> --json-secret-file <filename.json>
```

## Instance Management

### Function Instances

```bash
# List instances
ngc cf fn instance list <function-id>:<version-id>

# Get instance logs
ngc cf fn instance logs <function-id>:<version-id> --instance-id <id>

# Execute command in instance
ngc cf fn instance execute <function-id>:<version-id> \
  --instance-id <id> --pod-name <pod> --container-name <container> --command "<cmd>"
```

### Task Instances

```bash
# List instances
ngc cf task instance list <task-id>

# Get instance logs
ngc cf task instance logs <task-id> --instance-id <id>

# Execute command in running task
ngc cf task instance execute <task-id> \
  --instance-id <id> --pod-name <pod> --container-name <container> --command "<cmd>"
```

## Deployment Logs

```bash
ngc cf fn deploy log <function-id>:<version-id> \
  [--start-time yyyy-MM-dd::HH:mm:ss] \
  [--end-time yyyy-MM-dd::HH:mm:ss] \
  [--duration <nD><nH><nM><nS>]
```

## Registry Credentials

For private registries like AWS ECR:

```bash
ngc cf registry-credential create \
  --hostname <registry-hostname> \
  --name <credential-name> \
  --key <secret_access_key> \
  --aws-access-key <access_key_id> \
  --type CONTAINER
```

## Troubleshooting

Enable debug mode to see detailed API calls:

```bash
ngc cf fn list --debug
```

## Additional Resources

- [Detailed Examples](examples.md)
- [Function Reference](references/functions.md)
- [Invocation Reference](references/invocation.md)
- [Task Reference](references/tasks.md)
- [Cluster Reference](references/clusters.md)
- [GPU Reference](references/gpus.md)
- [Registry Reference](references/registry.md)
