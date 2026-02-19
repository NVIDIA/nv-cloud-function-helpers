# NGC Registry Reference

Detailed reference for working with the NGC Private Registry (nvcr.io) via NGC CLI and Docker.

The NGC registry stores container images, Helm charts, models, and resources used by NVCF functions and tasks. Understanding the registry is critical because **artifacts must exist in the registry before they can be referenced in function or task creation**.

## Critical Rule: Push Before You Reference

When creating a function or task with `--container-image`, the image must already exist in the registry you reference. If you build an image locally, you must push it to the registry before creating the function. Do not create a function referencing an image that has not been pushed -- the deployment will fail.

**Common mistake:** Building a container image locally, then immediately running `ngc cf fn create --container-image nvcr.io/<org>/<image>:<tag>` without pushing the image first. The function creation may succeed (it does not validate the image exists), but the deployment will fail when NVCF cannot pull the image.

**Correct workflow:**
1. Build the image locally
2. Tag it for the target registry
3. Push it to the registry
4. Verify it exists in the registry
5. Create the function referencing the pushed image

## Container Images

### Authenticating to the NGC Registry

Before pushing or pulling images, authenticate Docker to nvcr.io:

```bash
docker login nvcr.io
```

When prompted:
- **Username:** `$oauthtoken` (literal string, always this value)
- **Password:** Your NGC API key (the `nvapi-...` token)

Alternatively, use a one-liner (assumes `NGC_API_KEY` is set):

```bash
echo "$NGC_API_KEY" | docker login nvcr.io -u '$oauthtoken' --password-stdin
```

If `NGC_API_KEY` is not set, load it from the NGC CLI config first:

```bash
NGC_API_KEY=$(grep -E '^[[:space:]]*apikey[[:space:]]*=' ~/.ngc/config 2>/dev/null | head -1 | sed 's/.*=[[:space:]]*//')
echo "$NGC_API_KEY" | docker login nvcr.io -u '$oauthtoken' --password-stdin
```

### Building and Pushing Images to nvcr.io

#### Step 1: Build the image

```bash
docker build -t my-inference-app:v1.0 .
```

#### Step 2: Tag the image for NGC

The NGC registry path format is `nvcr.io/<org>/[<team>/]<image>:<tag>`.

Use the org from `ngc config current` (the org slug or ID shown in the output). For example, if your org is `myorg`:

```bash
docker tag my-inference-app:v1.0 nvcr.io/myorg/my-inference-app:v1.0
```

With a team:

```bash
docker tag my-inference-app:v1.0 nvcr.io/myorg/myteam/my-inference-app:v1.0
```

#### Step 3: Push the image

```bash
docker push nvcr.io/myorg/my-inference-app:v1.0
```

#### Step 4: Verify the image exists

```bash
ngc registry image info myorg/my-inference-app:v1.0
```

Or list images to find it:

```bash
ngc registry image list myorg/my-inference-app
```

#### Step 5: Create the function

Only after confirming the image exists in the registry:

```bash
ngc cf fn create \
  --name my-inference-app \
  --inference-url /predict \
  --container-image nvcr.io/myorg/my-inference-app:v1.0 \
  --health-uri /health
```

### Listing Images in the Registry

```bash
# List all images in your org
ngc registry image list

# List images in a specific org
ngc registry image list --org <org-id>

# List images with a name filter
ngc registry image list myorg/my-*

# List images with JSON output
ngc registry image list --format_type json
```

**Note:** `ngc registry image list` without arguments lists images in the currently configured org. If the output is empty or unexpected, verify the active org with `ngc config current`.

### Getting Image Details

```bash
# Get image info (includes tags, size, creation date)
ngc registry image info <org>/<image>:<tag>

# Get info in JSON
ngc registry image info <org>/<image>:<tag> --format_type json

# List all tags for an image
ngc registry image list <org>/<image>
```

### Removing Images

```bash
ngc registry image remove <org>/<image>:<tag>
```

### Image Path Formats for NVCF

When referencing images in `--container-image` for functions and tasks:

| Image location | Format | Example |
|----------------|--------|---------|
| NGC registry (same org) | `nvcr.io/<org>/<image>:<tag>` | `nvcr.io/myorg/my-app:v1.0` |
| NGC registry (short form) | `<org>/<image>:<tag>` | `myorg/my-app:v1.0` |
| NGC registry (with team) | `nvcr.io/<org>/<team>/<image>:<tag>` | `nvcr.io/myorg/myteam/my-app:v1.0` |
| Docker Hub | `docker.io/<org>/<image>:<tag>` | `docker.io/vllm/vllm-openai:latest` |
| AWS ECR (private) | `<account>.dkr.ecr.<region>.amazonaws.com/<repo>:<tag>` | `123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:v1` |
| Other registries | Full URL | `ghcr.io/org/image:tag` |

**Short form for NGC images:** When deploying a function from your own org's registry, you can use the short form `<org>/<image>:<tag>` without the `nvcr.io/` prefix. NVCF resolves this to the NGC registry automatically. However, using the full `nvcr.io/` path is recommended for clarity.

**Third-party registries:** Images from Docker Hub, ECR, GHCR, or any non-NGC registry require the full registry URL. Using a short name (e.g., `vllm/vllm-openai:latest` instead of `docker.io/vllm/vllm-openai:latest`) will fail with "Invalid artifact provided". Private third-party registries also require registry credentials; see [Registry Credentials](#registry-credentials-for-third-party-registries) below.

## Helm Charts

Helm charts stored in the NGC registry can be used to deploy functions and tasks with more complex multi-container or multi-service architectures.

### Listing Helm Charts

```bash
# List all charts in your org
ngc registry chart list

# List charts in a specific org
ngc registry chart list --org <org-id>

# Get chart details
ngc registry chart info <org>/<chart>:<version>
```

### Pushing Helm Charts

```bash
# Push a local chart to the NGC registry
ngc registry chart push <org>/<chart>:<version> <chart-directory-or-tgz>
```

### Using Helm Charts in Functions

```bash
ngc cf fn create \
  --name my-helm-function \
  --inference-url /v1/predict \
  --helm-chart <org>/<chart>:<version> \
  --helm-chart-service <service-name>
```

The `--helm-chart-service` flag specifies which Kubernetes service in the chart serves the inference endpoint.

### Using Helm Charts in Tasks

```bash
ngc cf task create \
  --name my-helm-task \
  --helm-chart <org>/<chart>:<version> \
  --gpu-specification <gpu>:<instance_type> \
  --configuration-file values.yaml \
  --set image.tag=1.2.3
```

## Models

Models stored in the NGC registry can be mounted into function and task containers at runtime. This is useful for large model weights that should not be baked into the container image.

### Listing Models

```bash
# List models in your org
ngc registry model list

# List models with a filter
ngc registry model list --org <org-id>

# Get model details
ngc registry model info <org>/<model>:<version>
```

### Attaching Models to Functions

Use the `--model` flag when creating a function. The model is mounted into the container at `/mount/models/<model-name>/<version>`:

```bash
ngc cf fn create \
  --name my-model-function \
  --inference-url /v1/predict \
  --container-image nvcr.io/myorg/inference-server:v1 \
  --health-uri /health \
  --model myorg/llama-weights:v1.0
```

Multiple models can be attached by repeating the flag:

```bash
ngc cf fn create \
  --name multi-model-fn \
  --inference-url /v1/predict \
  --container-image nvcr.io/myorg/inference-server:v1 \
  --model myorg/model-a:v1.0 \
  --model myorg/model-b:v2.0
```

### Attaching Models to Tasks

```bash
ngc cf task create \
  --name training-with-pretrained \
  --container-image nvcr.io/myorg/training:v1 \
  --gpu-specification A100:ga100_1.br20_4xlarge \
  --model myorg/pretrained-weights:v1.0
```

## Resources

Resources are general-purpose file collections stored in the NGC registry (datasets, configs, scripts, etc.). They work similarly to models but mount at `/mount/resources/<resource-name>/<version>`.

### Listing Resources

```bash
# List resources in your org
ngc registry resource list

# Get resource details
ngc registry resource info <org>/<resource>:<version>
```

### Attaching Resources to Functions

```bash
ngc cf fn create \
  --name my-function \
  --inference-url /v1/predict \
  --container-image nvcr.io/myorg/inference:v1 \
  --resource myorg/config-files:v1.0
```

### Attaching Resources to Tasks

```bash
ngc cf task create \
  --name my-task \
  --container-image nvcr.io/myorg/processor:v1 \
  --gpu-specification L40:gl40_1.br20_2xlarge \
  --resource myorg/input-dataset:v1.0
```

## Registry Credentials for Third-Party Registries

To pull images from private, non-NGC registries (AWS ECR, GCR, etc.), you must register credentials with NVCF:

```bash
ngc cf registry-credential create \
  --hostname <registry-hostname> \
  --name <credential-name> \
  --key <password-or-secret-key> \
  --aws-access-key <access-key-id>  # Only for AWS ECR
  --type CONTAINER
```

### List registered credentials

```bash
ngc cf registry-credential list
```

### Remove a credential

```bash
ngc cf registry-credential remove <credential-name>
```

For full third-party registry setup, see the [NVIDIA Cloud Functions Third-Party Registries documentation](https://docs.nvidia.com/cloud-functions/user-guide/latest/cloud-function/third-party-registries.html).

## Troubleshooting

### "Invalid artifact provided" when creating a function

The image path format is wrong. Ensure third-party images include the full registry URL (e.g., `docker.io/org/image:tag`, not just `org/image:tag`).

### Deployment fails to pull image

1. Verify the image exists: `ngc registry image info <org>/<image>:<tag>`
2. If it does not exist, push it first (see [Building and Pushing Images](#building-and-pushing-images-to-nvcrio))
3. If using a third-party registry, verify credentials are registered: `ngc cf registry-credential list`

### "unauthorized" or "authentication required" when pushing

1. Re-authenticate: `docker login nvcr.io`
2. Verify your NGC API key is valid
3. Verify you have write access to the target org

### Cannot list images in the registry

1. Check your active org: `ngc config current`
2. Try specifying the org explicitly: `ngc registry image list --org <org-id>`
3. If the org uses teams, you may need to specify the team: `ngc registry image list <org>/<team>/`
4. Use `--format_type json` for more detailed output

### Image exists locally but NVCF cannot pull it

A locally-built image is not accessible to NVCF. You must push it to a registry that NVCF can access:
- **NGC registry (nvcr.io):** Tag and push the image (see steps above)
- **Third-party registry:** Push to your registry and register credentials with NVCF
- **BYOC clusters:** Even bring-your-own-cloud clusters pull images from a registry, not from the local Docker daemon
