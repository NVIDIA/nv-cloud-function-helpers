# NGC Cloud Function Cluster Reference

Detailed reference for managing clusters via NGC CLI.

Clusters are compute resources where functions and tasks run. You can register your own clusters (on-premise or cloud) for NVCF deployments.

## Listing Clusters

```bash
# List all registered clusters
ngc cf cluster list

# Get detailed cluster info
ngc cf cluster info <cluster-id>

# List clusters with JSON output
ngc cf cluster list --format_type json
```

## Registering a Cluster

**Authentication requirement:** Cluster creation requires browser-based (email) authentication. API key auth alone is not sufficient. If the CLI returns `"Requires browser authentication. Use ngc config set --auth-option email."`, the user must run `ngc config set --auth-option email` and complete the browser login flow before retrying. Do not attempt to bypass this by calling the REST API directly.

```bash
ngc cf cluster create \
  --cluster-name <name> \
  --cluster-group-name <group-name> \
  --cloud-provider <provider> \
  --region <region> \
  --ssa-client-id <ssa-client-id> \
  [--cluster-description "<description>"] \
  [--capability <capability>] \
  [--attribute <attribute>] \
  [--custom-attribute <custom-attribute>] \
  [--authorized-nca-id <nca-id>] \
  [--nvca-version <version>]
```

### Required parameters

| Parameter | Description |
|-----------|-------------|
| `--cluster-name` | Unique name for the cluster (immutable after creation) |
| `--cluster-group-name` | Group name for deploying across multiple clusters |
| `--cloud-provider` | Cloud platform: `AWS`, `AZURE`, `GCP`, `OCI`, `DGX-CLOUD`, `ON-PREM` |
| `--region` | Deployment region (see supported regions below) |
| `--ssa-client-id` | SSA client ID for authentication |

### Supported regions

- `us-east-1`
- `us-west-1`
- `us-west-2`
- `eu-central-1`
- `eu-north-1`
- `eu-south-1`
- `eu-west-1`
- `ap-east-1`

### Cloud providers

| Provider | Description |
|----------|-------------|
| `AWS` | Amazon Web Services |
| `AZURE` | Microsoft Azure |
| `GCP` | Google Cloud Platform |
| `OCI` | Oracle Cloud Infrastructure |
| `DGX-CLOUD` | NVIDIA DGX Cloud |
| `ON-PREM` | On-premise infrastructure |

### Capabilities

Optional capabilities that can be enabled:

- `CachingSupport` - Enable caching support
- `DynamicGPUDiscovery` - Enable dynamic GPU discovery
- `LogPosting` - Enable log posting

```bash
ngc cf cluster create \
  --cluster-name my-cluster \
  --cluster-group-name my-cluster-group \
  --cloud-provider AWS \
  --region us-west-2 \
  --ssa-client-id <ssa-client-id> \
  --capability CachingSupport \
  --capability LogPosting
```

## Deleting a Cluster

```bash
ngc cf cluster delete <cluster-id>
```

## Using Clusters in Deployments

### Function deployments with targeted clusters

Use `--targeted-dep-spec` with cluster names in the 6th positional field:

```bash
ngc cf fn deploy create <function-id>:<version-id> \
  --targeted-dep-spec <gpu>:<instance_type>:<min>:<max>:<concurrency>:<clusters>[:<regions>][:<attributes>][:<preferredOrder>]
```

**Warning:** The CLI `--help` shows `clusters(c1,c2)` wrapper syntax, but the CLI does not parse it. Always use plain cluster names directly as positional colon-separated values.

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

### Task with specific clusters

```bash
ngc cf task create \
  --name my-task \
  --container-image myorg/image:tag \
  --gpu-specification <gpu>:<instance_type>:<backend>:cluster-1,cluster-2
```

Note: Backend is optional. Format: `<gpu>:<instance_type>[:<backend>][:<clusters>]`

## Examples

### Register an AWS cluster

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

### Register an on-premise cluster

```bash
ngc cf cluster create \
  --cluster-name onprem-datacenter \
  --cluster-group-name datacenter \
  --cloud-provider ON-PREM \
  --region us-east-1 \
  --ssa-client-id xyz789-abc123 \
  --cluster-description "On-premise datacenter cluster"
```

### Register an Azure cluster

```bash
ngc cf cluster create \
  --cluster-name azure-inference \
  --cluster-group-name inference \
  --cloud-provider AZURE \
  --region eu-west-1 \
  --ssa-client-id azure-client-id \
  --cluster-description "Azure inference cluster in EU"
```

### Register a GCP cluster

```bash
ngc cf cluster create \
  --cluster-name gcp-training \
  --cluster-group-name training \
  --cloud-provider GCP \
  --region us-west-2 \
  --ssa-client-id gcp-client-id \
  --cluster-description "GCP training cluster"
```
