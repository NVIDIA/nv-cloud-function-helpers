# NGC Cloud Function GPU Reference

Detailed reference for managing GPU resources and quotas via NGC CLI.

## List Allocated GPUs

View GPUs currently allocated to your organization:

```bash
ngc cf gpu list
```

## GPU Capacity

View GPU capacity allocation summary:

```bash
# View all capacity
ngc cf gpu capacity

# Filter by region
ngc cf gpu capacity --region us-west-2

# Filter by GPU type
ngc cf gpu capacity --gpu L40

# Multiple filters
ngc cf gpu capacity --region us-west-2 --gpu L40 --gpu A100

# Multiple regions
ngc cf gpu capacity --region us-east-1 --region us-west-2
```

### Supported regions

- `us-east-1`
- `us-west-1`
- `us-west-2`
- `eu-central-1`
- `eu-north-1`
- `eu-south-1`
- `eu-west-1`
- `ap-east-1`

## GPU Quota

GPU quota controls how many GPUs of each type an organization can use. Quotas are set per GPU hardware type (e.g., 10 L40, 24 H100) and are shared across both functions and tasks. Quotas can also include limits by cluster, region, and allowed instance types.

### Viewing quota

```bash
# ASCII summary
ngc cf gpu quota

# JSON for detailed inspection (recommended)
ngc cf gpu quota --format_type json
```

### Understanding quota JSON output

The JSON output contains an array of GPU entries. Each entry defines the quota rules for one GPU type:

```json
{
  "gpus": [
    {
      "name": "L40",
      "quota": 100,
      "instance-types": "*",
      "clusters": [
        { "names": "cluster-a", "limit": 40 }
      ]
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

### Quota fields

| Field | Meaning |
|-------|---------|
| `name` | GPU hardware type (e.g., `L40`, `H100`, `A100`) |
| `quota` | Total GPU count allowed for this type across all deployments |
| `instance-types` | Allowed instance types. `*` means all; otherwise a comma-separated list (e.g., `H100_1x,H100_2x`) |
| `clusters` | Optional cluster-level limits. Each entry has `names` (comma-separated) and `limit` (max GPUs across those clusters) |
| `dedicated-clusters` | Same as `clusters` but for dedicated/managed clusters. When present, the deployment spec **must** include an explicit cluster |
| `regions` | Optional region-level limits. Each entry has `names` (comma-separated) and `limit` (max GPUs across those regions) |

### How GPU counting works

Quota is counted in **GPUs, not instances**, and is evaluated against **maxInstances** (the autoscaling ceiling), not minInstances. A multi-GPU instance type counts each GPU individually:

| Instance Type | GPU Count per Instance |
|---------------|----------------------|
| `OCI.GPU.H100_1x` | 1 GPU |
| `OCI.GPU.H100_4x` | 4 GPUs |
| `OCI.GPU.H100_8x` | 8 GPUs |
| `OCI.GPU.H100_8x.x4` | 32 GPUs (4 nodes x 8 GPUs) |

**Quota usage per deployment = maxInstances x GPUs per instance type.**

Example: With `quota: 16` for H100, you could deploy 16x `H100_1x`, or 4x `H100_4x`, or 2x `H100_8x` at max. A deployment with `H100_4x` min=1, max=2 counts as **8 GPUs** against quota (2 x 4), not 4.

### Quota enforcement rules

1. **Quota only applies to public clusters**: Quota enforcement applies to **public** clusters (`authorizedNcaId: *`). Private clusters (BYOC, no `authorizedNcaId`) and shared clusters (`authorizedNcaId` lists specific NCA IDs) are **not** subject to quota -- unless they have an explicit `dedicated-clusters` quota entry.
2. **Dedicated-cluster quota is separate**: If a cluster appears under `dedicated-clusters` in the quota rules, that cluster has its own GPU limit regardless of cluster type. The deployment spec **must** include the cluster name.
3. **No quota entry needed for exempt clusters**: If deploying only to private or shared clusters that have no dedicated-cluster quota entry, no quota rule is required for that GPU type.
4. **Functions and tasks share quota**: GPU usage from both functions and tasks counts against the same quota.
5. **Instance type restriction**: If `instance-types` is not `*`, only the listed types can be used.
6. **Region limits**: If region limits are defined, the deployment spec must include a region, and usage in each region group cannot exceed its limit.
7. **Cluster limits**: If cluster or dedicated-cluster limits are defined, the deployment spec must include a cluster, and usage per cluster group cannot exceed its limit.
8. **Mixed deployments**: If a single deployment spec targets both an exempt cluster (private/shared) and a public cluster, quota enforcement applies to the entire deployment.

### Common quota errors and resolution

| Error | Meaning | Fix |
|-------|---------|-----|
| `FAILED_MISSING_CLUSTERS: Cluster quota Limits are set; clusters is required in input` | Org has cluster-level quota limits but deployment spec has no cluster | Add cluster to `--targeted-dep-spec` (6th field) |
| `EXCEED_DEDICATED_CLUSTER_QUOTA_LIMITS: Quota exceeded for GPU 'A100' and dedicated clusters 'my-cluster'` | Not enough GPUs left on the dedicated cluster | Reduce instances, free up other deployments on that cluster, or use a different cluster |
| `Insufficient quota for H100 in region us-west-2` | Region limit reached | Reduce instances or deploy to a different region |
| `GPU type X and instance type Y not found in cluster Z` | Cluster doesn't have that GPU/instance type | Check `ngc cf gpu info <gpu>` for valid cluster + instance type combos |

### Pre-deployment quota check workflow

Before deploying, verify quota and available resources:

```bash
# 1. Check quota limits
ngc cf gpu quota --format_type json

# 2. Check current usage (sum maxInstances x GPUs-per-instance across deployments)
ngc cf fn deploy list --format_type json

# 3. Discover available clusters and instance types for a GPU
ngc cf gpu info A100
```

If the quota JSON shows `dedicated-clusters` or `clusters` entries, you **must** include the cluster name in your `--targeted-dep-spec`. If it shows `regions` entries, you should include the region.

## GPU Info

Get detailed information about a specific GPU type, including all available instance types, clusters, and regions:

```bash
# Get info for a specific GPU type (required argument)
ngc cf gpu info <gpu-type>

# Examples
ngc cf gpu info H100
ngc cf gpu info L40
ngc cf gpu info A100
ngc cf gpu info GB200
```

Output includes instance types (e.g., `OCI.GPU.H100_1x`), memory specs, available clusters, and regions.

## Available GPUs (Admin Only)

List all available GPU types in your organization:

```bash
ngc cf available-gpus
```

## Common GPU Types

| GPU | Description | Use Cases |
|-----|-------------|-----------|
| `GB200` | NVIDIA GB200 | Next-gen AI workloads |
| `H100` | NVIDIA H100 | Large-scale training, LLMs |
| `A100` | NVIDIA A100 | Training, large models |
| `L40S` | NVIDIA L40S | Enhanced inference, media |
| `L40` | NVIDIA L40 | Inference, light training |
| `T10` | NVIDIA T10 | Cost-effective inference |

## Instance Types

Instance types combine GPU and compute specifications. Format varies by backend/cloud provider:

| Format | Example | Description |
|--------|---------|-------------|
| OCI format | `OCI.GPU.H100_1x` | 1x H100 on OCI |
| OCI multi-node | `OCI.GPU.H100_8x.x4` | 4 nodes of 8x H100 (32 GPUs) |
| DGX Cloud | `DGX-CLOUD.GPU.L40_1x` | 1x L40 on DGX Cloud |
| GFN format | `gl40_1.br20_2xlarge` | 1x L40 GPU (GFN backend) |
| GFN legacy | `g6.full` | Full instance (GFN backend) |

Use `ngc cf gpu info <gpu-type>` to see all available instance types for a GPU.

## Using GPUs in Deployments

### Function deployment specification

```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec <gpu>:<instance_type>:<min>:<max>[:<concurrency>][:<clusters>][:<regions>][:<attributes>][:<preferredOrder>]
```

All fields after max are optional, positional, and colon-separated. Use commas for multiple values within a field. Skip fields with empty colons (`::`).

### Task GPU specification

```bash
ngc cf task create \
  --name my-task \
  --container-image myorg/image:tag \
  --gpu-specification <gpu>:<instance_type>[:<backend>][:<clusters>]
```

Example:
```bash
ngc cf task create \
  --name training \
  --container-image myorg/trainer:v1 \
  --gpu-specification A100:ga100_1.br20_4xlarge
```

## Examples

### Check available capacity before deployment

```bash
# Check L40 capacity in us-west-2
ngc cf gpu capacity --region us-west-2 --gpu L40

# Check overall quota
ngc cf gpu quota
```

### Get capacity as JSON for scripting

```bash
ngc cf gpu capacity --format_type json
```

### Check quota utilization

To calculate actual quota usage, list deployments and account for instance type GPU counts:

```bash
# 1. View quota limits
ngc cf gpu quota --format_type json

# 2. List active deployments to see what's consuming quota
ngc cf fn deploy list --format_type json
```

For each deployment, quota usage = `maxInstances` x GPUs per instance type. Extract the GPU count from the instance type name (e.g., `_2x` = 2 GPUs, `_4x` = 4 GPUs, `_8x.x4` = 32 GPUs). Sum across all deployments per GPU type and compare against the quota limit.

Note: `ngc cf gpu list` shows available instance types and platform capacity, not your org's current usage. Use `ngc cf fn deploy list` for actual deployment-level usage.

### Filter capacity by multiple GPUs

```bash
ngc cf gpu capacity --gpu L40 --gpu A100 --gpu H100
```

### Check capacity across regions

```bash
# US regions
ngc cf gpu capacity --region us-east-1 --region us-west-2

# EU regions  
ngc cf gpu capacity --region eu-central-1 --region eu-west-1
```

### Look up instance types for deployment

```bash
# Find available H100 instance types
ngc cf gpu info H100

# Get JSON output for scripting
ngc cf gpu info H100 --format_type json
```

### Verify GPU availability before task creation

```bash
# Check if A100 capacity is available
ngc cf gpu capacity --gpu A100

# Create task with A100
ngc cf task create \
  --name my-training \
  --container-image myorg/trainer:v1 \
  --gpu-specification A100:ga100_1.br20_4xlarge
```
