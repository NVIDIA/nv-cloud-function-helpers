# Self-Hosted NVCF Local Development (k3d)

Run the full NVCF self-hosted control plane on your laptop using [k3d](https://k3d.io/) for development, testing, or demos.

> **Note**: This setup uses fake GPUs, a single Cassandra replica, and ephemeral storage. It is not suitable for production.

## Prerequisites

- [Docker](https://www.docker.com/get-started) (running)
- [k3d](https://k3d.io/#installation) v5.x or later
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [helm](https://helm.sh/docs/intro/install/) >= 3.12
- [helmfile](https://helmfile.helmfile.sh/) >= 1.1.0, < 1.2.0
- [helm-diff](https://github.com/databus23/helm-diff) plugin
- NGC API Key from [ngc.nvidia.com](https://ngc.nvidia.com)

## Quick Start

### 1. Create the local cluster

```bash
chmod +x setup.sh teardown.sh
./setup.sh
```

This creates a k3d cluster with:
- 6 nodes (1 server + 5 agents)
- 2 nodes with 8 simulated H100 GPUs each (via fake GPU operator)
- CSI SMB driver for shared storage
- Envoy Gateway with Gateway API

### 2. Deploy the NVCF stack

Follow the Local Development Guide for deployment of the helmfile - nvcf-self-managed-stack. This is available in the Self-Hosted NVCF documentation which is currently early access only. Please reach out to your NVIDIA representative for access.

1. **Environment file** — Download the local development environment template from the docs and save it as `environments/<name>.yaml` in your `nvcf-self-managed-stack` directory. The template uses `nvcr.io/0833294136851237/nvcf-ncp-staging` and is pre-configured for k3d.

2. **Secrets** — Create `secrets/<name>-secrets.yaml` with your NGC credentials.

3. **Pull secrets** — Configure Kyverno to inject image pull secrets.

4. **Deploy:**

```bash
helm registry login nvcr.io -u '$oauthtoken' -p "$NGC_API_KEY"
HELMFILE_ENV=<name> helmfile sync
```

### 3. Verify

```bash
# Get gateway address
export GATEWAY_ADDR=$(kubectl get gateway nvcf-gateway -n envoy-gateway -o jsonpath='{.status.addresses[0].value}')

# Generate admin token
export NVCF_TOKEN=$(curl -s -X POST "http://${GATEWAY_ADDR}/v1/admin/keys" \
  -H "Host: api-keys.${GATEWAY_ADDR}" \
  | grep -o '"value":"[^"]*"' | cut -d'"' -f4)

# List functions (should return empty)
curl -s "http://${GATEWAY_ADDR}/v2/nvcf/functions" \
  -H "Host: api.${GATEWAY_ADDR}" \
  -H "Authorization: Bearer ${NVCF_TOKEN}" | jq .
```

## Accessing Routes

Routes use the `.localhost` TLD which resolves to `127.0.0.1` on most systems. Access via port 8080:

- `http://api.localhost:8080` — NVCF API
- `http://api-keys.localhost:8080` — API Keys
- `http://invocation.localhost:8080` — Function invocation

If `.localhost` doesn't resolve, add to `/etc/hosts`:

```
127.0.0.1 api.localhost
127.0.0.1 api-keys.localhost
127.0.0.1 invocation.localhost
```

## Teardown

```bash
./teardown.sh <name>   # e.g., ./teardown.sh my-local
```

## What's Included

| File | Purpose |
|------|---------|
| `k3d-config.yaml` | k3d cluster configuration (5 agents, fake GPU labels, port mappings) |
| `setup.sh` | Creates cluster, installs KWOK, fake GPU operator, CSI SMB, Envoy Gateway |
| `teardown.sh` | Destroys the NVCF stack and k3d cluster |

## Limitations

- **Fake GPUs** — Containers deploy but cannot run actual GPU workloads
- **Single Cassandra replica** — No high availability
- **Ephemeral storage** — Data lost when the cluster is deleted
- **Not for performance testing** — Laptop resources do not represent production
