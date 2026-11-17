#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$RUNNER_TEMP/k8s-tools"
cd "$RUNNER_TEMP/k8s-tools"

curl -fsSL \
  https://github.com/kubernetes-sigs/kind/releases/download/v0.30.0/kind-linux-amd64 \
  -o kind-linux-amd64
curl -fsSL \
  https://github.com/kubernetes-sigs/kind/releases/download/v0.30.0/kind-linux-amd64.sha256sum \
  -o kind-linux-amd64.sha256sum
sha256sum -c kind-linux-amd64.sha256sum
sudo install -m 0755 kind-linux-amd64 /usr/local/bin/kind

curl -fsSL \
  https://dl.k8s.io/release/v1.34.0/bin/linux/amd64/kubectl \
  -o kubectl
curl -fsSL \
  https://dl.k8s.io/release/v1.34.0/bin/linux/amd64/kubectl.sha256 \
  -o kubectl.sha256
printf '%s  %s\n' "$(cat kubectl.sha256)" kubectl \
  | sha256sum -c -
sudo install -m 0755 kubectl /usr/local/bin/kubectl
