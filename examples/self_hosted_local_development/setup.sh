#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_NAME="ncp-local"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_tool() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed. $2"
        exit 1
    fi
}

# --- Pre-flight checks ---
log_info "Checking prerequisites..."
check_tool docker "Install from https://www.docker.com/get-started"
check_tool k3d "Install with: brew install k3d (or see https://k3d.io)"
check_tool kubectl "Install from https://kubernetes.io/docs/tasks/tools/"
check_tool helm "Install with: brew install helm (or see https://helm.sh)"

if ! docker info &> /dev/null; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# --- Step 1: Create k3d cluster ---
log_info "========== STEP 1: CREATE K3D CLUSTER =========="
if k3d cluster get "$CLUSTER_NAME" &> /dev/null; then
    log_info "Cluster '$CLUSTER_NAME' already exists. Skipping creation."
    k3d cluster start "$CLUSTER_NAME" 2>/dev/null || true
else
    log_info "Creating k3d cluster '$CLUSTER_NAME'..."
    k3d cluster create --config "${SCRIPT_DIR}/k3d-config.yaml"
fi

k3d kubeconfig merge "$CLUSTER_NAME" --kubeconfig-switch-context > /dev/null 2>&1
log_info "kubectl context set to k3d-${CLUSTER_NAME}"

kubectl wait --for=condition=Ready nodes --all --timeout=120s > /dev/null 2>&1
log_info "All nodes are Ready."

# --- Step 2: Install KWOK + Fake GPU Operator ---
log_info "========== STEP 2: FAKE GPU OPERATOR =========="

if kubectl get deployment kwok-controller -n kube-system &> /dev/null; then
    log_info "KWOK controller already installed. Skipping."
else
    log_info "Installing KWOK controller..."
    kubectl apply -f https://github.com/kubernetes-sigs/kwok/releases/download/v0.7.0/kwok.yaml 2>&1 | grep -v "FlowSchema" || true
    kubectl wait --for=condition=Available deployment/kwok-controller -n kube-system --timeout=60s
    log_info "KWOK controller is ready."
fi

if helm status gpu-operator -n gpu-operator &> /dev/null; then
    log_info "Fake GPU operator already installed. Skipping."
else
    log_info "Installing fake GPU operator..."
    helm repo add fake-gpu-operator \
        https://runai.jfrog.io/artifactory/api/helm/fake-gpu-operator-charts-prod --force-update > /dev/null 2>&1

    helm upgrade -i gpu-operator fake-gpu-operator/fake-gpu-operator \
        -n gpu-operator --create-namespace \
        --set 'topology.nodePools.default.gpuCount=8' \
        --set 'topology.nodePools.default.gpuProduct=NVIDIA-H100-80GB-HBM3' \
        --set 'topology.nodePools.default.gpuMemory=81559' \
        --wait --timeout=120s
    log_info "Fake GPU operator installed."
fi

log_info "Waiting for fake GPUs to appear on nodes..."
for i in {1..30}; do
    GPU_COUNT=$(kubectl get node -l run.ai/simulated-gpu-node-pool=default \
        -o jsonpath='{.items[0].status.allocatable.nvidia\.com/gpu}' 2>/dev/null || echo "")
    if [ -n "$GPU_COUNT" ] && [ "$GPU_COUNT" != "0" ]; then
        log_info "Fake GPUs detected: ${GPU_COUNT} per node."
        break
    fi
    if [ "$i" -eq 30 ]; then
        log_warn "Fake GPUs not yet visible after 60s. They may appear shortly."
        log_warn "Check with: kubectl get nodes -o custom-columns='NAME:.metadata.name,GPU:.status.allocatable.nvidia\\.com/gpu'"
    fi
    sleep 2
done

# --- Step 3: Install CSI SMB Driver ---
log_info "========== STEP 3: CSI SMB DRIVER =========="

if helm status csi-driver-smb -n kube-system &> /dev/null; then
    log_info "CSI SMB driver already installed. Skipping."
else
    log_info "Installing CSI SMB driver..."
    helm repo add csi-driver-smb \
        https://raw.githubusercontent.com/kubernetes-csi/csi-driver-smb/master/charts > /dev/null 2>&1

    helm install csi-driver-smb csi-driver-smb/csi-driver-smb \
        -n kube-system --version v1.17.0 --wait --timeout=120s
    log_info "CSI SMB driver installed."
fi

# --- Step 4: Install Envoy Gateway ---
log_info "========== STEP 4: ENVOY GATEWAY =========="

if helm status eg -n envoy-gateway-system &> /dev/null; then
    log_info "Envoy Gateway already installed. Skipping."
else
    log_info "Installing Envoy Gateway..."
    helm install eg oci://docker.io/envoyproxy/gateway-helm \
        --version v1.1.3 \
        -n envoy-gateway-system --create-namespace \
        --wait --timeout=120s
    log_info "Envoy Gateway installed."
fi

log_info "Applying GatewayClass..."
kubectl apply -f - <<'EOF'
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: eg
spec:
  controllerName: gateway.envoyproxy.io/gatewayclass-controller
EOF

log_info "Creating namespaces and labeling for Gateway route access..."
for ns in envoy-gateway api-keys ess sis nvcf; do
    kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f - > /dev/null 2>&1
    kubectl label namespace "$ns" nvcf/platform=true --overwrite > /dev/null 2>&1
done

log_info "Applying Gateway resource..."
kubectl apply -f - <<'EOF'
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: nvcf-gateway
  namespace: envoy-gateway
spec:
  gatewayClassName: eg
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: Selector
        selector:
          matchLabels:
            nvcf/platform: "true"
  - name: tcp
    protocol: TCP
    port: 10081
    allowedRoutes:
      namespaces:
        from: Selector
        selector:
          matchLabels:
            nvcf/platform: "true"
EOF

log_info "Waiting for Gateway to be programmed..."
kubectl wait --for=condition=Programmed gateway/nvcf-gateway -n envoy-gateway --timeout=120s 2>/dev/null || \
    log_warn "Gateway not yet programmed. It may take a moment."

# --- Summary ---
echo ""
log_info "=========================================="
log_info "  Local cluster is ready!"
log_info "=========================================="
echo ""
log_info "Cluster:      k3d-${CLUSTER_NAME}"
log_info "Nodes:        6 (1 server + 5 agents)"
log_info "Fake GPUs:    8x H100 on 2 nodes"
log_info "Gateway:      nvcf-gateway (envoy-gateway namespace)"
echo ""
log_info "Next steps:"
log_info "  1. Configure secrets/local-secrets.yaml with your NGC credentials"
log_info "  2. Set up image pull secrets (Kyverno recommended)"
log_info "  3. Run: HELMFILE_ENV=local helmfile sync"
echo ""
log_info "See the self-hosted control plane installation guide for details:"
log_info "  https://docs.nvidia.com/cloud-functions/self-hosted/latest/control-plane-installation.html"
echo ""
