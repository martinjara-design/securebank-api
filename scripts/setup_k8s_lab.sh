#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="securebank"
REGISTRY_NAME="securebank-registry"
REGISTRY_PORT="5001"
CALICO_VERSION="v3.31.0"

OUTPUT="reports/k8s"
mkdir -p "$OUTPUT"

docker run -d \
  --name "$REGISTRY_NAME" \
  --restart=always \
  -p "127.0.0.1:${REGISTRY_PORT}:5000" \
  registry:2.8.3

# Comprobar que el registro responde desde el runner.
REGISTRY_READY=false

for ATTEMPT in {1..30}; do
  if curl --fail --silent \
    "http://127.0.0.1:${REGISTRY_PORT}/v2/" \
    > "$OUTPUT/registry-health.json"
  then
    REGISTRY_READY=true
    break
  fi
  sleep 1
done

if [ "$REGISTRY_READY" != "true" ]; then
  docker logs "$REGISTRY_NAME"
  exit 1
fi

cat > "$OUTPUT/kind-config.yaml" <<'YAML'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4

networking:
  disableDefaultCNI: true
  podSubnet: "192.168.0.0/16"

containerdConfigPatches:
  - |-
    [plugins."io.containerd.cri.v1.images"]
      use_local_image_pull = true
    [plugins."io.containerd.cri.v1.images".registry]
      config_path = "/etc/containerd/certs.d"

nodes:
  - role: control-plane
    image: kindest/node:v1.34.0@sha256:7416a61b42b1662ca6ca89f02028ac133a309a2a30ba309614e8ec94d976dc5a
YAML

kind create cluster \
  --name "$CLUSTER_NAME" \
  --config "$OUTPUT/kind-config.yaml"

kubectl config use-context "kind-${CLUSTER_NAME}"

docker network connect kind "$REGISTRY_NAME"

REGISTRY_DIRECTORY="/etc/containerd/certs.d/localhost:${REGISTRY_PORT}"

for NODE in $(kind get nodes --name "$CLUSTER_NAME"); do
  docker exec "$NODE" mkdir -p "$REGISTRY_DIRECTORY"

  # Definir el servidor real, evitando volver al localhost del nodo.
  cat <<EOF | docker exec -i "$NODE" \
    sh -c "cat > '$REGISTRY_DIRECTORY/hosts.toml'"
server = "http://${REGISTRY_NAME}:5000"

[host."http://${REGISTRY_NAME}:5000"]
  capabilities = ["pull", "resolve"]
EOF

  # Registrar la configuracion utilizada para diagnosticos.
  docker exec "$NODE" \
    cat "$REGISTRY_DIRECTORY/hosts.toml" \
    > "$OUTPUT/${NODE}-registry-hosts.toml"

  docker exec "$NODE" containerd config dump \
    > "$OUTPUT/${NODE}-containerd-config.toml"
done

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
