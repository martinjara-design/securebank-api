#!/usr/bin/env bash
set -euo pipefail
IMAGE_REFERENCE="${1:?Falta imagen con digest}"
SIGNER_IDENTITY="${2:?Falta identidad autorizada}"
: "${REGISTRY_TOKEN:?Falta token temporal del registro}"
: "${GITHUB_ACTOR:?Falta usuario de GitHub Actions}"
mkdir -p reports/supply-chain/deployment reports/k8s

# Gate repetido inmediatamente antes del despliegue real.
bash scripts/verify_supply_chain.sh "$IMAGE_REFERENCE" "$SIGNER_IDENTITY" \
  reports/supply-chain/deployment/verification

kubectl apply -f k8s/hardened/namespace.yaml
kubectl create namespace kyverno
# Credenciales temporales: no imprimir ni guardar manifiestos Secret como evidencia.
for NAMESPACE in securebank kyverno; do
  kubectl -n "$NAMESPACE" create secret generic ghcr-read \
    --type=kubernetes.io/dockerconfigjson \
    --from-file=.dockerconfigjson="$HOME/.docker/config.json"
done
JWT_FILE=$(mktemp "$RUNNER_TEMP/securebank-jwt.XXXXXX")
trap 'rm -f "$JWT_FILE"' EXIT
JWT=$(openssl rand -hex 32)
echo "::add-mask::$JWT"
printf '%s' "$JWT" > "$JWT_FILE"
kubectl -n securebank create secret generic securebank-secrets \
  --from-file="jwt-secret=$JWT_FILE"

helm repo add kyverno https://kyverno.github.io/kyverno/
helm repo update
helm upgrade --install kyverno kyverno/kyverno \
  --version 3.9.2 --namespace kyverno \
  --set admissionController.replicas=1 \
  --set backgroundController.replicas=1 \
  --set cleanupController.replicas=1 \
  --set reportsController.replicas=1 \
  --set 'existingImagePullSecrets[0]=ghcr-read' \
  --wait --timeout 300s
helm list -n kyverno -o json > reports/supply-chain/deployment/kyverno-version.json

python3 scripts/render_admission.py "$SIGNER_IDENTITY" \
  reports/supply-chain/deployment/policy.yaml
kubectl apply -f reports/supply-chain/deployment/policy.yaml
kubectl wait --for=condition=Ready clusterpolicy/securebank-signed-images --timeout=120s
kubectl wait --for=condition=Ready clusterpolicy/securebank-trusted-registry --timeout=120s

python3 scripts/render_k8s.py "$IMAGE_REFERENCE" reports/k8s/deployment.hardened.yaml
# El archivo generado usa la misma cuenta de lectura temporal del registro.
python3 - <<'PY'
import json, subprocess
from pathlib import Path
s = Path('reports/k8s/deployment.hardened.yaml').read_text()
s = s.replace('      enableServiceLinks: false',
              '      enableServiceLinks: false\n      imagePullSecrets:\n        - name: ghcr-read')
Path('reports/k8s/deployment.hardened.yaml').write_text(s)
PY
kubectl apply --dry-run=server -f reports/k8s/deployment.hardened.yaml
kubectl apply -f reports/k8s/deployment.hardened.yaml
kubectl apply -f k8s/hardened/service.yaml
kubectl apply -f k8s/hardened/networkpolicy.yaml
kubectl -n securebank rollout status deployment/securebank-api --timeout=180s \
  | tee reports/supply-chain/deployment/rollout.txt
kubectl -n securebank exec deployment/securebank-api -- python -c \
  "import json,urllib.request; d=json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=5)); print(json.dumps(d)); assert d.get('status')=='ok'" \
  | tee reports/supply-chain/deployment/health.json
kubectl -n securebank get deployment securebank-api -o json \
  > reports/supply-chain/deployment/deployment-live.json
python3 - "$IMAGE_REFERENCE" <<'PY'
import json,sys
from pathlib import Path
obj=json.loads(Path('reports/supply-chain/deployment/deployment-live.json').read_text())
assert obj['spec']['template']['spec']['containers'][0]['image']==sys.argv[1]
assert obj['status']['availableReplicas'] >= 1
print('PASS: el digest verificado es el desplegado y esta disponible.')
PY
