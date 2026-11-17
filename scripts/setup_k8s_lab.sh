#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="securebank"
REGISTRY_NAME="securebank-registry"
REGISTRY_PORT="5001"
CALICO_VERSION="v3.31.0"

OUTPUT="reports/k8s"
mkdir -p "$OUTPUT"

# Registro disponible solo desde el runner y la red del laboratorio.
docker run -d \
  --name "$REGISTRY_NAME" \
  --restart=always \
  -p "127.0.0.1:${REGISTRY_PORT}:5000" \
  registry:2.8.3

# Desactivamos la red predeterminada de Kind para instalar Calico.
cat > "$OUTPUT/kind-config.yaml" <<'YAML'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4

networking:
  disableDefaultCNI: true
  podSubnet: "192.168.0.0/16"

nodes:
  - role: control-plane
    image: kindest/node:v1.34.0@sha256:7416a61b42b1662ca6ca89f02028ac133a309a2a30ba309614e8ec94d976dc5a
YAML

kind create cluster \
  --name "$CLUSTER_NAME" \
  --config "$OUTPUT/kind-config.yaml"

kubectl config use-context "kind-${CLUSTER_NAME}"

# Permitir que los nodos alcancen el registro local.
docker network connect kind "$REGISTRY_NAME"

REGISTRY_DIRECTORY="/etc/containerd/certs.d/localhost:${REGISTRY_PORT}"

for NODE in $(kind get nodes --name "$CLUSTER_NAME"); do
  docker exec "$NODE" mkdir -p "$REGISTRY_DIRECTORY"

  printf '%s\n' \
    "[host.\"http://${REGISTRY_NAME}:5000\"]" \
    '  capabilities = ["pull", "resolve"]' \
    | docker exec -i "$NODE" \
      cp /dev/stdin "$REGISTRY_DIRECTORY/hosts.toml"
done

# Instalar una version concreta de Calico.
curl --fail --silent --show-error --location \
  "https://raw.githubusercontent.com/projectcalico/calico/${CALICO_VERSION}/manifests/calico.yaml" \
  --output "$OUTPUT/calico.yaml"

sha256sum "$OUTPUT/calico.yaml" \
  > "$OUTPUT/calico-manifest.sha256"

kubectl apply --server-side \
  -f "$OUTPUT/calico.yaml"

kubectl -n kube-system rollout status \
  daemonset/calico-node \
  --timeout=240s

kubectl -n kube-system rollout status \
  deployment/calico-kube-controllers \
  --timeout=240s

kubectl wait \
  --for=condition=Ready \
  nodes --all \
  --timeout=180s

kubectl -n kube-system rollout status \
  deployment/coredns \
  --timeout=180s

# Guardar evidencia sin copiar credenciales del cluster.
kind version > "$OUTPUT/kind-version.txt"

kubectl version -o yaml \
  > "$OUTPUT/kubernetes-version.yaml"

kubectl get nodes -o wide \
  > "$OUTPUT/nodes.txt"

kubectl -n kube-system get pods -o wide \
  > "$OUTPUT/system-pods.txt"

date -u +"%Y-%m-%dT%H:%M:%SZ" \
  > "$OUTPUT/fecha.txt"

echo "Cluster preparado: ${CLUSTER_NAME}"
echo "Registro local: localhost:${REGISTRY_PORT}"
echo "Calico: ${CALICO_VERSION}"
